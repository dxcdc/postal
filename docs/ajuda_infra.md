# Guia Técnico de Infraestrutura — CDC

Este guia detalha a arquitetura de rede, tabelas de portas, registros DNS, arquivos docker-compose.yml de referência, variáveis de ambiente e integrações operacionais do servidor de e-mails da **CDC**.

---

## 1. Desenho da Arquitetura
A infraestrutura está montada de forma híbrida: a Stack do Postal compartilha a rede do Host da VPS, enquanto o banco de dados e o proxy reverso rodam em redes Docker virtuais isoladas no Easypanel.

```text
┌────────────────────────────────────────────────────────┐
│ VPS Ubuntu Host                                        │
│                                                        │
│ (Tráfego público seguro: HTTPS 443 / SMTP 25)          │
│            │                                           │
│            ▼                                           │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Container App: postal-proxy (nginx:alpine)         │ │
│ └──────────┬─────────────────────────────────────────┘ │
│            │ (Proxy Pass para a VPS: 76.13.227.xxx:5000)│
│            ▼                                           │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Postal Web (Serviço Host no IP 0.0.0.0:5000)       │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

## 2. Tabelas de Portas e DNS

### Mapeamento de Portas

| Serviço | Porta Externa | Porta Interna | Interface de Escuta | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| **Proxy Web** | `443` / `80` | `80` (Docker) | `0.0.0.0` (Público) | SSL/HTTPS pelo Easypanel |
| **Postal Web** | Não exposta | `5000` | `0.0.0.0` (Local) | Painel Administrativo do Postal |
| **SMTP Delivery** | `2525` | `2525` | `0.0.0.0` (Público) | PortaSMTP para envio do Moodle |
| **Database** | Não exposta | `3306` | `127.0.0.1` (Privado) | MariaDB exclusivo local |

### Estrutura de Registros DNS no Cloudflare

| Tipo | Nome (Host) | Destino / Dados | Nuvem Cloudflare |
| :--- | :--- | :--- | :--- |
| **A** | `postal` | `76.13.227.xxx` | 🩶 Cinza (DNS Only) |
| **CNAME** | `track.postal` | `postal.cdc.org.br` | 🩶 Cinza (DNS Only) |
| **TXT** | `educa` | `"v=spf1 a mx include:spf.postal.cdc.org.br ~all"` | 🩶 Cinza (DNS Only) |
| **TXT** | `postal-kkp8ej._domainkey.educa` | `"v=DKIM1; t=s; h=sha256; p=MIGfMA0GCS...;` | 🩶 Cinza (DNS Only) |
| **CNAME** | `psrp.educa` | `rp.postal.cdc.org.br` | 🩶 Cinza (DNS Only) |
| **CNAME** | `track.educa` | `track.postal.cdc.org.br` | 🩶 Cinza (DNS Only) |

---

## 3. Arquivo de Referência `docker-compose.yml`
O contêiner do MariaDB roda em uma rede isolada. O Postal utiliza o fuso de Recife para consistência de logs:

```yaml
version: "3.9"

services:
  # Banco de Dados Standalone Isolado
  postal-mariadb:
    image: mariadb:10.9
    container_name: postal-mariadb
    restart: unless-stopped
    environment:
      MARIADB_DATABASE: postal
      MARIADB_USER: postal
      MARIADB_PASSWORD: <DB_PASSWORD>
      MARIADB_ROOT_PASSWORD: <DB_ROOT_PASSWORD>
    ports:
      - "127.0.0.1:3306:3306"
    volumes:
      - /opt/postal/db-data:/var/lib/mysql
    networks:
      - db-network

  # Aplicação Postal Web-Server
  web:
    image: ghcr.io/postalserver/postal:3.3.7
    command: postal web-server
    network_mode: host
    volumes:
      - /opt/postal/config:/config
    environment:
      - TZ=America/Recife
    restart: unless-stopped

networks:
  db-network:
    internal: true # Garante isolamento completo da rede externa
```

---

## 4. Arquivo de Exemplo `.env.example`
Copie este arquivo como `.env` e ajuste as credenciais correspondentes para testes locais:

```text
# Configurações do Banco de Dados
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=postal
DB_PASSWORD=<DB_PASSWORD>
DB_ROOT_PASSWORD=<DB_ROOT_PASSWORD>

# Fuso Horário
TZ=America/Recife

# Integração com Mattermost
MATTERMOST_WEBHOOK_URL=<MATTERMOST_WEBHOOK_URL>
```

---

## 5. Integração e Testes com o Mattermost
Alertas operacionais importantes de backup, deploy e falhas graves são transmitidos diretamente para o canal da equipe no Mattermost.

### Testando a Webhook pelo Terminal:
```bash
curl -i -X POST -H 'Content-Type: application/json' \
     -d '{"text": "### 🚀 Alerta Operacional: Teste de Webhook concluído na VPS da CDC."}' \
     <MATTERMOST_WEBHOOK_URL>
```

---

## 6. Comandos Operacionais Rápidos
Use estes comandos dentro da VPS para gerenciar a execução do Postal:

*   **Iniciar tudo:** `sudo postal start`
*   **Parar tudo:** `sudo postal stop`
*   **Verificar logs em tempo real:** `sudo postal logs`
*   **Recriar contêineres e aplicar novos timezones/variáveis:**
    ```bash
    sudo docker compose -p postal -f /opt/postal/install/docker-compose.yml up -d --force-recreate
    ```
