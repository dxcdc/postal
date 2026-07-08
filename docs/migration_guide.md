# Guia de Migração e Arquitetura - Servidor de Disparo Postal (CDC)

Este documento atua como o manual oficial de planejamento da migração, arquitetura e homologação do servidor de e-mails transacionais (Postal v3) para a infraestrutura de produção da CDC.

---

## 1. Objetivos de Infraestrutura e Cenário Atual

### Objetivos:
*   Substituir ou implantar uma alternativa de disparo transacional (Postal v3) robusta, de alta performance e baixo custo operacional.
*   Centralizar o serviço na VPS Ubuntu principal da CDC de forma isolada, rodando de forma segura atrás de um proxy reverso.
*   Integrar o Postal com o Moodle de forma direta e sem latência.

### Cenário de Origem (Mapeamento):
*   **Servidor Host:** VPS rodando Ubuntu.
*   **Orquestrador Web:** Easypanel (gerenciando portas públicas `80` e `443` com SSL do Let's Encrypt).
*   **Isolamento de Redes:** Subrede privada criada pelo Easypanel (faixa `10.11.0.x`).
*   **Bancos de Dados:** Standalone MariaDB rodando na porta `3306`.

---

## 2. Checklist de Mapeamento do Ambiente de Origem (Modo Leitura)

Antes de iniciar qualquer migração ou alteração de infraestrutura, execute os seguintes comandos no terminal da máquina de origem para coletar métricas e configurações de forma 100% segura (sem modificar o estado):

### Diagnóstico de Recursos do Sistema:
```bash
# Verificar arquitetura e versão do kernel
uname -a

# Verificar memória RAM instalada e disponível
free -h

# Analisar capacidade de CPU (núcleos e modelo)
lscpu | grep -E "Model name|Core(s) per socket|CPU(s):"

# Verificar o espaço em disco disponível
df -h
```

### Diagnóstico de Serviços e Portas Ativas:
```bash
# Listar todas as portas em modo de escuta (TCP/UDP) e seus respectivos processos
sudo ss -tulpn

# Listar todos os contêineres Docker ativos e inativos
docker ps -a

# Listar as redes virtuais do Docker ativas no sistema
docker network ls
```

### Validação e Integridade do Banco de Dados:
```bash
# Verificar se o contêiner MariaDB está ativo e respondendo (ping)
docker exec -it <NOME_DO_CONTAINER_BD> mysqladmin -u root -p ping

# Coletar estatísticas de execução e tempo de atividade do banco de dados
docker exec -it <NOME_DO_CONTAINER_BD> mysqladmin -u root -p status
```

---

## 3. Proposta de Arquitetura Baseada em Contêineres (Docker Compose)

Para garantir máxima segurança, performance e facilidade de manutenção, adotamos a arquitetura do **Postal v3** integrada a um banco MariaDB isolado, rodando de forma híbrida:

```
                  [ Acesso HTTPS: 443 ]
                            │
                            ▼
      ┌───────────────────────────────────────────┐
      │          Easypanel (Traefik)              │
      └─────────────────────┬─────────────────────┘
                            │ (Rede Docker Customizada)
                            ▼ [ Porta 80 ]
      ┌───────────────────────────────────────────┐
      │     postal-proxy Container (Nginx)        │
      └─────────────────────┬─────────────────────┘
                            │ (IP Público VPS: 76.13.227.135)
                            ▼ [ Porta local 5000 ]
 ┌─────────────────────────────────────────────────────┐
 │               VPS HOST NETWORK                      │
 │                                                     │
 │   ┌──────────────┐  ┌──────────────┐  ┌─────────┐   │
 │   │  postal-web  │  │ postal-smtp  │  │ postal- │   │
 │   │ (Porta 5000) │  │ (Porta 2525) │  │ worker  │   │
 │   └──────┬───────┘  └──────┬───────┘  └────┬────┘   │
 │          │                 │               │        │
 └──────────┼─────────────────┼───────────────┼────────┘
            │                 │               │
            ▼                 ▼               ▼
      ┌───────────────────────────────────────────┐
      │     Container Database (MariaDB:10)       │
      │           Porta 127.0.0.1:3306            │
      └───────────────────────────────────────────┘
```

### Detalhes de Rede e Segurança:
1.  **Rede Host para o Postal:**
    Os serviços do Postal (`web`, `smtp` e `worker`) rodam com `network_mode: host` devido a requisitos de baixa latência e controle de portas SMTP dinâmicas (porta `2525`).
2.  **Isolamento do Banco de Dados:**
    O banco MariaDB roda dentro do container isolado, expondo a porta `3306` **apenas** para o endereço de loopback (`127.0.0.1:3306`). Nenhuma máquina externa à VPS consegue acessar a porta do banco de dados diretamente.
3.  **Segurança no Proxy Reverso (Nginx):**
    O container `postal-proxy` gerencia a criptografia SSL/TLS e encaminha as requisições para a porta local `5000` na VPS utilizando o IP público da VPS (`76.13.227.135`), contornando limitações de conectividade de rede interna flutuante (Docker Swarm) do Easypanel.

---

## 4. Plano de Contingência, Backup e Homologação (Staging)

### A. Homologação em Laboratório Local (Staging):
Antes de implantar em produção, configure o ambiente em sua máquina de testes local:
1.  Escreva as configurações no arquivo `.env` baseando-se no `.env.example`.
2.  Edite o arquivo `/etc/hosts` na sua máquina de desenvolvimento para simular a resolução DNS localmente:
    ```text
    127.0.0.1   core.cdc.org.br
    ```
3.  Suba a estrutura executando `./deploy.sh` localmente e teste o acesso à interface web e disparos via SMTP local usando uma ferramenta de testes de email (ex: `swaks` ou `mailpit`).

### B. Plano de Backup (Segurança dos Dados):
Crie uma tarefa agendada (Cron) na VPS para fazer o backup diário do banco de dados e arquivos de chaves criptográficas:

#### Script de Backup Diário (`backup_postal.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/opt/postal/backups"
DATE=$(date +%F_%H-%M-%S)
mkdir -p "$BACKUP_DIR"

# 1. Backup do Banco de Dados MariaDB
docker exec postal-mariadb mysqldump -u root -p'SUA_SENHA_AQUI' postal > "$BACKUP_DIR/db_postal_$DATE.sql"

# 2. Backup das Configurações e Chaves DKIM/Criptografia
tar -czf "$BACKUP_DIR/config_postal_$DATE.tar.gz" /opt/postal/config

# Manter apenas os últimos 15 dias de backup (limpeza automática)
find "$BACKUP_DIR" -type f -mtime +15 -delete
```

### C. Plano de Contingência e Rollback (Retorno ao Estado Anterior):
Caso ocorra alguma falha crítica durante a migração ou atualizações em produção, siga estes passos para restabelecer o serviço anterior:

1.  **Parar a nova pilha de serviços:**
    ```bash
    docker compose -f /opt/postal/install/docker-compose.yml down
    ```
2.  **Restaurar o banco de dados anterior:**
    ```bash
    docker exec -i postal-mariadb mysql -u root -p'SUA_SENHA_AQUI' postal < /opt/postal/backups/db_postal_ULTIMO_BACKUP_VALIDO.sql
    ```
3.  **Restaurar a pasta de chaves/configurações:**
    ```bash
    tar -xzf /opt/postal/backups/config_postal_ULTIMO_BACKUP_VALIDO.tar.gz -C /
    ```
4.  **Iniciar a pilha estável novamente:**
    ```bash
    sudo postal start
    ```
