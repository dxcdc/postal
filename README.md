# CDC - Servidor de Disparo de E-mails (Postal)

Este repositório contém a documentação, scripts e templates de infraestrutura para o servidor de envio de e-mails transacionais (alternativa open-source ao SendGrid/Mailgun) da **CDC (Centro de Desenvolvimento e Cidadania)**, atendendo ao Moodle e a outros projetos futuros.

O servidor de e-mails foi implantado com sucesso utilizando o **Postal v3** rodando em Docker e integrado com o proxy reverso **Traefik** do **Easypanel** no ambiente Ubuntu VPS.

---

## Estrutura do Repositório

*   `install_postal.sh`: Script utilizado para instalar as dependências base e baixar o instalador oficial do Postal na VPS.
*   `default.conf`: Arquivo de configuração do Nginx Proxy que faz a ponte entre o Easypanel (Traefik) e a porta local `5000` do Postal na VPS.
*   `docker-compose.yml`: Template DevOps definitivo para subir o banco MariaDB e a aplicação Postal de forma unificada no Git (ideal para automações futuras).

---

## Detalhes da Implantação Atual

### 1. Aplicação Postal (Host Docker Stack)
O Postal v3 roda em `network_mode: host` diretamente na rede da VPS:
*   **Diretório de Configuração:** `/opt/postal/config/`
*   **Diretório do Instalador:** `/opt/postal/install/`
*   **Comandos de Gerenciamento:**
    *   Iniciar: `sudo postal start` (ou `sudo docker compose -p postal up -d` na pasta do instalador)
    *   Parar: `sudo postal stop` (ou `sudo docker compose -p postal down` na pasta do instalador)
    *   Verificar Status: `sudo postal status`
*   **Ajuste de Escuta (postal.yml):**
    Para permitir que o proxy interno do Docker fale com a porta `5000` do host, adicionamos a escuta pública no arquivo `/opt/postal/config/postal.yml`:
    ```yaml
    web_server:
      default_bind_address: 0.0.0.0
    ```

### 2. Banco de Dados MariaDB
O banco de dados roda em um container standalone:
*   **Nome do container:** `postal-mariadb`
*   **Porta exposta:** `127.0.0.1:3306:3306` (acesso restrito apenas localmente)
*   **Database:** `postal`

### 3. Integração com o Easypanel (Nginx Proxy)
Como o Easypanel controla as portas públicas `80` e `443` da VPS, configuramos um aplicativo do tipo "App" com o nome **`postal-proxy`** dentro do projeto **`cdc-ezpoint`** no painel:
*   **Imagem Docker:** `nginx:alpine`
*   **Porta do Proxy:** `80`
*   **Domínio associado:** `core.cdc.org.br` (com SSL Let's Encrypt automático via Easypanel)
*   **Armazenamento (Volume):** 
    Criamos um volume chamado `config` apontando para `/etc/nginx/conf.d` dentro do container.
*   **Configuração do Proxy (default.conf):**
    No terminal da VPS, escrevemos o arquivo `/etc/easypanel/projects/cdc-ezpoint/postal-proxy/volumes/config/default.conf` que aponta para o gateway da rede interna do Easypanel (`10.11.0.1:5000`):
    ```nginx
    server {
        listen 80;
        server_name core.cdc.org.br;
        location / {
            proxy_pass http://10.11.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
    ```

---

## Configurações Pendentes (Para Segunda-Feira)

Quando tiver acesso ao gerenciador de DNS do domínio `cdc.org.br`, realize as configurações abaixo:

### 1. Criar Subdomínio Definitivo (Opcional)
Se preferir mudar do domínio temporário `core.cdc.org.br` para algo como `postal.cdc.org.br`:
1. No DNS, aponte um registro **A** com o nome `postal` para o IP da VPS.
2. No Easypanel, mude o domínio do app `postal-proxy` para `postal.cdc.org.br`.
3. No arquivo `default.conf`, altere o `server_name` para `postal.cdc.org.br`.
4. No arquivo `/opt/postal/config/postal.yml`, altere as linhas `web_hostname` e `smtp_hostname` para `postal.cdc.org.br` e reinicie o Postal (`sudo postal restart`).

### 2. Autenticação de E-mail (Entregabilidade)
Dentro do painel do Postal, após criar a organização e o servidor virtual para o Moodle:
1. Acesse **Domains** -> **Add Domain** -> Adicione `cdc.org.br`.
2. Configure na sua zona de DNS as chaves exibidas pelo painel:
   *   **SPF (TXT):** `v=spf1 ip4:IP_DA_SUA_VPS include:spf.core.cdc.org.br ~all`
   *   **DKIM (TXT):** Crie um registro com nome `postal._domainkey` contendo a chave gerada.
   *   **DMARC (TXT):** `v=DMARC1; p=none; rua=mailto:dmarc@cdc.org.br`
   *   **DNS Reverso (PTR):** Configure o DNS reverso do IP da sua VPS no painel de sua hospedagem para apontar para `core.cdc.org.br` (ou `postal.cdc.org.br`).

---

## Integração com o Moodle

Configurações no Moodle (`Administração do site` -> `Servidor` -> `Configuração de saída de e-mail`):
*   **SMTP hosts:** `IP_DA_SUA_VPS:2525` (ou `core.cdc.org.br:2525`)
*   **Segurança SMTP:** `Nenhum` (se for rede local interna na VPS) ou `TLS` (se passar por conexão externa com certificado)
*   **Autenticação SMTP:** `Login`
*   **Usuário e Senha SMTP:** Gerados na aba **Credentials** do painel do Postal.
*   **Endereço de e-mail de suporte:** Deve ser um e-mail do domínio verificado (ex: `nao-responda@cdc.org.br`).
