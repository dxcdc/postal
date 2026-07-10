# Resumo de Transição do Projeto: Servidor Postal da CDC

Este documento serve como um **Dossiê de Hand-off (Transição de Projeto)**. Ele compila todas as decisões, arquitetura implantada, credenciais, lições aprendidas e próximos passos do servidor de e-mails da CDC. 

Guarde este arquivo no Git para que, ao acessar esta pasta de qualquer nova conta ou sessão da AI, o contexto completo seja lido e compreendido instantaneamente.

---

## 1. Status Atual e URL do Painel
*   **Painel Administrativo:** `https://postal.cdc.org.br` (com HTTPS/SSL ativo)
*   **Usuário Administrador:** `gt.transformadigital@cdc.org.br`
*   **Senha de Acesso:** `<MASCARADA_POR_SEGURANÇA>` *(a senha que redefinimos no console)*
*   **IP da VPS:** `76.x.x.x`

---

## 2. Arquitetura da Infraestrutura Implantada

*   **Postal v3:** Roda no Docker da VPS Ubuntu no modo `network_mode: host` (sem Caddy interno ou RabbitMQ, consumindo pouquíssima RAM).
*   **Banco de Dados:** Container MariaDB standalone (`postal-mariadb`) rodando em `127.0.0.1:3306`.
*   **Escuta do Servidor:** Configurada em `0.0.0.0:5000` em `/opt/postal/config/postal.yml` para aceitar conexões da rede Docker interna e do IP público.
*   **Proxy Reverso (Easypanel):**
    *   Um aplicativo chamado `postal-proxy` (imagem `nginx:alpine`) foi criado no Easypanel.
    *   Ele aponta o domínio `postal.cdc.org.br` para o IP público da VPS: `http://76.x.x.x:5000` (onde o Postal está ouvindo, desviando de problemas de rede flutuante/Swarm).
    *   A configuração do proxy está no volume do container mapeado na VPS: `/etc/easypanel/projects/cdc-ezpoint/postal-proxy/volumes/config/default.conf`.

---

## 3. Arquivos Versionados no Git (Pasta `postal/`)

*   `deploy.sh`: Script de automação 100% silenciosa (não interativo). Faz bootstrap do Postal em container temporário, configura o YAML via Python, inicializa as tabelas e cria o usuário administrador via Rails Runner.
*   `.env.example`: Modelo de segredos locais para o `deploy.sh`.
*   `docker-compose.yml`: Compose unificado moderno para deploys futuros baseados em GitOps/Vault.
*   `default.conf`: Configuração exata do Nginx Proxy utilizada no Easypanel.
*   `install_postal.sh`: Script que prepara dependências da VPS.
*   **Pasta `docs/`:**
    *   `documentacao.md`: Índice central de documentação e lições aprendidas.
    *   `ajuda_infra.md`: Desenho da rede e comandos úteis de ligar/desligar.
    *   `postmortem.md`: Relatório de depuração de bugs ocorridos durante o setup.
    *   `troubleshooting.md`: Guia de resolução de problemas comuns.
    *   `historico_comandos.md`: Runbook com o histórico do console com dados mascarados.

---

## 4. Principais Lições Aprendidas

1.  **Postal v3 vs v2:** A versão 3 não utiliza RabbitMQ e roda direto no host. É mais leve e consome menos de 2 GB de RAM ocioso.
2.  **Docker Bridge Mismatch:** Como o Easypanel usa a subrede privada `10.11.0.x`, o gateway da VPS para o proxy é `10.11.0.1` (e não `172.17.0.1`).
3.  **Bind Address:** O Postal precisa escutar em `0.0.0.0` para aceitar conexões do gateway da rede Docker.
4.  **Escape do Zsh:** Caracteres especiais como `!` em senhas devem ser passados em comandos envoltos em aspas simples (`'...'`) para que o Zsh não dê erro de histórico (`event not found`).
5.  **Console Rails:** O banco do Postal usa o campo `email_address` (e não `email`) no Model `User`. Para redefinir senhas via terminal, a receita é:
    ```bash
    sudo postal console
    u = User.find_by(email_address: "gt.transformadigital@cdc.org.br")
    u.password = "NOVA_SENHA"
    u.save!
    ```

---

## 5. Próximos Passos (Ações para Segunda-Feira)

1.  **DNS & Entregabilidade:**
    *   Criar registro **A** apontando o subdomínio definitivo para o IP da VPS.
    *   Cadastrar os registros **SPF (TXT)**, **DKIM (TXT)** e **DMARC (TXT)** gerados pelo painel do Postal no seu gerenciador de DNS (Cloudflare/Registro.br).
    *   Cadastrar o **DNS Reverso (PTR)** do IP da VPS apontando para o seu subdomínio de disparo.
2.  **Integração Moodle:**
    *   Criar as credenciais SMTP no painel do Postal (aba *Credentials*).
    *   Preencher as credenciais nas configurações de saída de e-mail do Moodle.
