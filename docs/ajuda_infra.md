# Ajuda de Infraestrutura (Postal + Easypanel)

Este documento descreve a arquitetura física, redes e gerenciamento de serviços da infraestrutura do servidor de disparo de e-mails (Postal) hospedado na VPS da **CDC**.

---

## Desenho da Arquitetura de Rede

Abaixo está o fluxo de tráfego que viabiliza o acesso seguro (HTTPS) ao painel administrativo e os disparos via SMTP:

```
[Acesso Web (Navegador)]
        │
        ▼ (HTTPS: Port 443)
┌────────────────────────────────────────────────────────┐
│ VPS Ubuntu (Sistema Host)                              │
│                                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Easypanel (Traefik Proxy)                          │ │
│ └──────────┬─────────────────────────────────────────┘ │
│            │ (HTTP: Port 80 - Interno do Docker)       │
│            ▼                                           │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Container App: postal-proxy (nginx:alpine)         │ │
│ └──────────┬─────────────────────────────────────────┘ │
│            │ (Proxy Pass para a VPS: 10.11.0.1:5000)   │
│            ▼                                           │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Postal Web (Serviço Host no IP 0.0.0.0:5000)       │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘

[Moodle / Outros Sistemas]
        │
        ▼ (SMTP: Port 2525)
┌────────────────────────────────────────────────────────┐
│ VPS Ubuntu (Postal SMTP Service no Host)               │
└────────────────────────────────────────────────────────┘
```

---

## Localização dos Arquivos e Diretórios Chave

### Na VPS Ubuntu (Sistema Host)
*   **Comandos do Postal:** `/usr/bin/postal` (link simbólico para `/opt/postal/install/bin/postal`).
*   **Diretório de Instalação/Docker:** `/opt/postal/install/`
    *   Contém o arquivo `docker-compose.yml` que gerencia a aplicação Postal.
*   **Diretório de Configuração:** `/opt/postal/config/`
    *   `postal.yml`: Arquivo principal contendo conexões de banco de dados, chaves e escutas de porta.
    *   `signing.key`: Chave privada gerada no bootstrap para assinar e-mails (DKIM).
*   **Dados Persistentes do MariaDB (Banco de Dados):**
    *   Os dados do banco de dados `postal-mariadb` são mantidos pelo Docker Engine na própria VPS.

### No Easypanel (Painel Web e Nginx Proxy)
*   **Arquivo de Proxy Nginx (`default.conf`):** 
    Localizado no disco da VPS em:
    `/etc/easypanel/projects/cdc-ezpoint/postal-proxy/volumes/config/default.conf`
    *(Este arquivo está montado dentro do container do proxy no caminho `/etc/nginx/conf.d/default.conf`)*.

---

## Comandos de Inicialização e Parada

Sempre que precisar gerenciar os serviços na VPS por terminal, utilize:

*   **Verificar Status dos Serviços:**
    ```bash
    sudo postal status
    ```
*   **Iniciar Todos os Serviços (Web, SMTP, Worker):**
    ```bash
    sudo postal start
    ```
*   **Parar Todos os Serviços:**
    ```bash
    sudo postal stop
    ```
*   **Reiniciar Todos os Serviços:**
    ```bash
    sudo postal restart
    ```
*   **Verificar Logs em Tempo Real:**
    ```bash
    sudo docker compose -p postal logs -f
    ```
    *(Execute na pasta `/opt/postal/install`)*.
