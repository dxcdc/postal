# Backlog de Issues Técnicas — Postal v3 (CDC)

Este documento contém os modelos prontos de **GitHub Issues** para registro, acompanhamento e histórico de melhorias na infraestrutura do servidor de e-mails da **CDC**.

---

## 📌 Issue 1: Ajuste de Rota e SSL no Proxy para Domínio de Rastreamento (`track.educa.cdc.org.br`)

**Título:** `fix(proxy): ajustar terminação SSL e rotas de tracking para evitar HTTP 403`

### Descrição
Ao clicar em links rastreáveis de e-mails, o Postal retornava um erro `HTTP 403 Forbidden` devido à falta de alinhamento entre o certificado SSL gerado no Easypanel/Traefik e o modo de verificação interna do Postal.

### Tarefas / Checklist
- [x] Adicionar `track.educa.cdc.org.br` e `track.postal.cdc.org.br` na aba **Domains** do app `postal-proxy` no Easypanel.
- [x] Atualizar o `server_name` no `default.conf` do Nginx para aceitar os domínios de rastreamento.
- [x] Configurar o campo **SSL ENABLED** no painel do Postal para `No - do not use SSL for tracking` (permitindo que o Proxy/Cloudflare gerencie o HTTPS).
- [ ] Validar redirecionamento de links em novos e-mails de teste.

---

## 📌 Issue 2: Correção da Chave DKIM para o Subdomínio `educa.cdc.org.br` na Cloudflare

**Título:** `dns(cloudflare): ajustar nome da entrada TXT do DKIM para subdomínio de disparos`

### Descrição
O Gmail estava rejeitando os e-mails com o erro `550-5.7.26 (DKIM did not pass)` porque o registro TXT no DNS foi criado na raiz (`postal-kkp8eJ._domainkey`) em vez de estar atrelado ao subdomínio do Moodle (`postal-kkp8eJ._domainkey.educa`).

### Tarefas / Checklist
- [x] Renomear o registro TXT na Cloudflare para `postal-kkp8eJ._domainkey.educa`.
- [x] Validar propagação DNS usando `dig txt postal-kkp8ej._domainkey.educa.cdc.org.br`.
- [x] Confirmar o selo verde de validação DKIM na aba **Domains** do Postal.

---

## 📌 Issue 3: Bypass de Conexões IPv6 para Evitar Rejeição por Falta de PTR no Gmail

**Título:** `infra(network): desativar roteamento IPv6 SMTP no Host para forçar envios via IPv4`

### Descrição
As tentativas de envio SMTP para o Gmail falhavam com o erro `550-5.7.26` quando o Postal tentava se conectar via IPv6, pois a interface da VPS não possuía registro de DNS Reverso (PTR IPv6) cadastrado na hospedagem.

### Tarefas / Checklist
- [x] Desativar o protocolo IPv6 nas configurações do kernel da VPS (`sysctl -w net.ipv6.conf.all.disable_ipv6=1`).
- [x] Reiniciar o serviço do Postal (`sudo postal restart`).
- [x] Validar entrega de e-mail na caixa de entrada do Gmail via IPv4.

---

## 📌 Issue 4: Correção de Erros de Validação CSRF (HTTP 422) no Rails

**Título:** `fix(nginx): forçar cabeçalho X-Forwarded-Proto para HTTPS no Nginx Proxy`

### Descrição
Ações no painel administrativo do Postal retornavam a mensagem de erro do Rails `The change you wanted was rejected (422 Unprocessable Entity)` devido à incompatibilidade do cabeçalho de protocolo entre o Traefik (HTTPS) e o Nginx Proxy interno (HTTP).

### Tarefas / Checklist
- [x] Alterar o cabeçalho `proxy_set_header X-Forwarded-Proto` no `default.conf` para `https` estático.
- [x] Efetuar reload do proxy Nginx no Easypanel.
- [x] Testar formulários de login e atualização de credenciais.
