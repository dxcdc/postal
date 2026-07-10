# Guia de Migração e Acesso Seguro — CDC

Este documento estabelece o protocolo padrão para acesso a servidores, coleta de diagnósticos sem escrita, procedimentos de backup para migração, transferência e validação do servidor de e-mails da **CDC**.

---

## 1. Protocolo de Acesso SSH Seguro
Toda a administração e manutenção técnica da VPS de produção deve ser feita seguindo as melhores práticas de segurança:

### Configuração Recomendada (`~/.ssh/config` na máquina local):
```text
Host cdc-email
    HostName 76.13.227.xxx
    User admin_cdc
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

### Endurecimento (Hardening) do Servidor SSH (`/etc/ssh/sshd_config`):
```text
# Desativar autenticação por senha (forçar chaves públicas)
PasswordAuthentication no

# Desativar login direto como root
PermitRootLogin no

# Forçar o uso do protocolo SSH v2
Protocol 2
```
*Após realizar alterações, reinicie o serviço:* `sudo systemctl restart sshd`

---

## 2. Diagnóstico em Modo Somente Leitura (Read-Only)
Para coletar dados de estado, consumo e rede sem alterar o estado do servidor de e-mails:

```bash
# 1. Verificar consumo de memória RAM
free -h

# 2. Verificar espaço livre e inodes em disco
df -h
df -i

# 3. Analisar desempenho e consumo dos containers em tempo real
docker stats --no-stream

# 4. Verificar portas SMTP/Web em escuta no Host
sudo ss -tulpn | grep -E "25|5000"

# 5. Testar a resolução de DNS interna
dig TXT postal-kkp8ej._domainkey.educa.cdc.org.br +short

# 6. Testar conectividade com o webhook do Mattermost
curl -i -X POST -H 'Content-Type: application/json' \
     -d '{"text": "Teste de conectividade de diagnóstico do Servidor Postal."}' \
     <MATTERMOST_WEBHOOK_URL>
```

---

## 3. Planejamento da Migração de Dados
Para migrar o Postal de uma VPS para outra, siga rigorosamente a sequência de ações operacionais abaixo.

### Fase 1: Preparação e Congelamento (Maintenance Window)
1.  Notifique os usuários e equipes pelo **Mattermost** que uma janela de migração começará.
2.  Interrompa a chegada de novos e-mails parando o servidor SMTP e os workers do Postal:
    ```bash
    sudo postal stop
    ```
3.  Crie um checksum SHA-256 de todas as pastas de chaves e banco antes de exportar:
    ```bash
    find /opt/postal/config/ -type f -exec sha256sum {} \; > /tmp/checksum_config.txt
    ```

### Fase 2: Exportação Segura do Banco de Dados
Para exportar o banco MariaDB sem expor a senha no histórico de comandos da VPS, utilize um arquivo de configuração temporário `~/.my.cnf`:

```bash
# 1. Criar arquivo de credenciais seguro
cat <<EOF > ~/.my.cnf
[client]
user=root
password="<DB_ROOT_PASSWORD>"
host=127.0.0.1
EOF
chmod 600 ~/.my.cnf

# 2. Exportar o banco de dados via container
docker exec -i postal-mariadb mysqldump --defaults-file=/root/.my.cnf --single-transaction postal > /tmp/db_postal_backup.sql

# 3. Apagar o arquivo temporário de credenciais
rm -f ~/.my.cnf
```

### Fase 3: Compactação e Transferência
```bash
# 1. Compactar a pasta de chaves e configurações
tar -czf /tmp/config_postal.tar.gz -C /opt/postal config/

# 2. Transferir os arquivos de forma segura para a nova VPS
rsync -avzP -e "ssh -i ~/.ssh/id_ed25519" /tmp/db_postal_backup.sql admin_cdc@76.13.227.xxx:/tmp/
rsync -avzP -e "ssh -i ~/.ssh/id_ed25519" /tmp/config_postal.tar.gz admin_cdc@76.13.227.xxx:/tmp/
```

### Fase 4: Restauração e Validação na Nova VPS
1.  Descompacte a pasta de configurações no mesmo local `/opt/postal/`.
2.  Suba os novos contêineres e importe o dump do banco de dados.
3.  Verifique a consistência dos checksums usando o arquivo gerado na Fase 1.
4.  Valide o funcionamento:
    *   Envie um e-mail de teste via terminal e certifique-se de que a entrega foi registrada no Gmail.
    *   Verifique se o webhook do Mattermost enviou o alerta de sucesso da migração.
