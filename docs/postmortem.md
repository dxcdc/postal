# Relatório de Análise de Incidentes (Post-Mortem) — CDC

Este relatório documenta as ocorrências, investigações e resoluções aplicadas de forma cronológica durante a fase de implantação e homologação do servidor de e-mails **Postal v3** da CDC. Adotamos uma cultura de análise técnica sem culpados (*blameless*).

---

## Incidente Geral: Instalação e Estabilização do Postal v3 com Nginx Proxy

*   **Data do Incidente:** 04 de Julho de 2026 a 09 de Julho de 2026
*   **Severidade:** Alta (Bloqueio completo de envios e do acesso ao painel)
*   **Canal do Mattermost:** `#infra-email-alerts`

---

## 1. Resumo Executivo
Durante a implantação inicial e a migração de domínio, o servidor de e-mails apresentou falhas consecutivas de inicialização e indisponibilidade (erros de **502 Bad Gateway** e **504 Gateway Time-out**), além de rejeições em cascata nos disparos SMTP pelo Google. Os problemas foram investigados cooperativamente e sanados através de correções na topologia de redes virtuais e na sintaxe do proxy reverso.

---

## 2. Sintomas e Impacto
*   **Sintoma A:** O painel administrativo retornava erros HTTP `504 Gateway Time-out` ao acessar o endereço definitivo.
*   **Sintoma B:** O contêiner do Nginx Proxy caía em loop (`Exited 1`), exibindo erros de sintaxe nos argumentos da diretiva `proxy_pass`.
*   **Sintoma C:** Mensagens de e-mail de teste disparadas para o Gmail retornavam erros de `550-5.7.1` (Diretrizes de SPF/DKIM/PTR em conexões IPv6 violadas).
*   **Sintoma D:** Ações no formulário de login retornavam telas de erro do Rails `The change you wanted was rejected (422 Unprocessable Entity)`.

---

## 3. Linha do Tempo Técnica (Timeline)

| Horário (UTC) | Ação / Evento | Impacto / Status |
| :--- | :--- | :--- |
| **04/Jul 02:00** | Inicialização manual dos contêineres Docker na pasta `/opt/postal/install/` | Conflito de nomes de projetos Docker (`install` vs `postal`). Comando `postal status` invisível. |
| **04/Jul 02:15** | Execução de limpeza (`docker compose down`) e reinício com nome de projeto correto `-p postal` | **Resolvido**. Status do Postal CLI voltou a responder corretamente. |
| **04/Jul 02:30** | Escrita acidental de barra invertida (`\;`) no final do `proxy_pass` do Nginx | Crash loop do container `postal-proxy` do Easypanel. |
| **04/Jul 02:40** | Correção da barra via terminal e reload do Nginx | **Resolvido**. NginxProxy voltou a ficar ativo. |
| **08/Jul 18:59** | Erro 504 Gateway Time-out ao direcionar o tráfego do proxy para `10.11.0.1` | Bloqueio de rede local interna. |
| **08/Jul 19:11** | Alteração do `default.bind_address` para `0.0.0.0` no `postal.yml` | **Resolvido**. Postal passou a ouvir em todas as placas. |
| **09/Jul 14:35** | Primeira tentativa de envio via SMTP para Gmail bloqueada por falta de PTR no IPv6 da VPS | Erro de segurança do Google (Hard Fail). |
| **09/Jul 15:30** | Desativação completa do IPv6 no Host via Sysctl e reinício do Postal | **Resolvido**. Envios SMTP passaram a ir direto via IPv4. |
| **09/Jul 16:30** | Login bloqueado por falha de token CSRF (Rails 422) | Cabeçalho `X-Forwarded-Proto` incorreto no proxy Nginx. |
| **09/Jul 16:35** | Alteração do cabeçalho para `https` fixo no `default.conf` do Nginx Proxy | **Resolvido**. Login liberado sem erros. |

---

## 4. Análise da Causa Raiz (5 Porquês)

### Falha de Autenticação CSRF (Rails 422):
1.  **Por que o usuário recebia "The change you wanted was rejected"?** Porque o Rails rejeitou a requisição devido a um mismatch de segurança (CSRF token).
2.  **Por que o Rails identificou um mismatch?** Porque a requisição chegou informando que a origem era HTTP, mas o navegador do usuário estava rodando em HTTPS.
3.  **Por que a aplicação achava que era HTTP?** Porque o Nginx Proxy passou o cabeçalho `X-Forwarded-Proto` com o valor de `$scheme` da sua própria conexão interna (porta 80).
4.  **Por que o Nginx usava HTTP se a conexão pública era HTTPS?** Porque o SSL era gerenciado e terminado pelo Traefik da ponta do Easypanel, e este repassava ao Nginx via HTTP puro.
5.  **Por que não forçamos o cabeçalho correto?** Porque o template padrão utilizava a variável dinâmica `$scheme`, que foi corrigida forçando-se o valor estático `https`.

---

## 5. Ações Corretivas e Preventivas

| Ação Recomendada | Tipo | Prioridade | Responsável | Prazo | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Criar backup do DNS antes da migração | Processo | Alta | DevOps | Imediato | **Concluído** |
| Desativar IPv6 nativo em servidores sem PTR | Infra | Média | Admin | Imediato | **Concluído** |
| Forçar HTTPS no Nginx Proxy (SSL double-hop) | Código | Alta | DevOps | Imediato | **Concluído** |
| Integrar alertas de erro de SMTP com Mattermost | Sistema | Alta | Dev | Em andamento | **Pendente** |
