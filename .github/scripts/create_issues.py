import os
import sys
import json
import urllib.request
import urllib.error

token = os.environ.get("GITHUB_TOKEN")
repo = os.environ.get("REPO")

if not token or not repo:
    print("❌ GITHUB_TOKEN ou REPO não configurados no ambiente.")
    sys.exit(1)

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "User-Agent": "GitHub-Actions-Issue-Automator"
}

# 1. Obter lista de issues existentes
url_list = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100"
req_list = urllib.request.Request(url_list, headers=headers)

existing_titles = []
try:
    with urllib.request.urlopen(req_list) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, list):
            existing_titles = [item.get("title", "") for item in data if isinstance(item, dict)]
        else:
            print(f"⚠️ Resposta de diagnóstico da API ao buscar issues: {data}")
except Exception as e:
    print(f"⚠️ Erro ao listar issues existentes: {e}")

def create_issue_if_not_exists(title, body, labels):
    if any(title in existing for existing in existing_titles):
        print(f"ℹ️ Issue '{title}' já existe no repositório. Pulando...")
        return

    print(f"🚀 Criando Issue: {title}")
    url_create = f"https://api.github.com/repos/{repo}/issues"
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": labels
    }).encode("utf-8")

    req_create = urllib.request.Request(url_create, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req_create) as resp:
            if resp.status in (200, 201):
                print(f"✅ Issue '{title}' criada com sucesso!")
            else:
                print(f"⚠️ Resposta da API ao criar '{title}': HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"❌ Erro HTTP {e.code} ao criar '{title}': {err_msg}")
    except Exception as e:
        print(f"❌ Erro inesperado ao criar '{title}': {e}")

# Lista de Issues a serem criadas
issues_data = [
    {
        "title": "[CONFIG] Ajuste de Rota e SSL no Proxy para Domínio de Rastreamento",
        "labels": ["bug", "infrastructure"],
        "body": """### Descrição
Ajustar as rotas do proxy reverso Nginx e a terminação SSL para os domínios de rastreamento do Postal (`track.educa.cdc.org.br` e `track.postal.cdc.org.br`), garantindo que o rastreamento de cliques e aberturas ocorra sem retornar erro HTTP 403.

### Referências Técnicas
- Manual de Infraestrutura: [docs/ajuda_infra.md](docs/ajuda_infra.md)
- Manual de Resolução de Problemas: [docs/troubleshooting.md](docs/troubleshooting.md)
- Backlog de Issues: [docs/issues_backlog.md](docs/issues_backlog.md)

### Critérios de Aceite
- [ ] Domínios `track.educa.cdc.org.br` e `track.postal.cdc.org.br` cadastrados no aplicativo `postal-proxy` do Easypanel.
- [ ] Cabeçalho `server_name` no `default.conf` do Nginx atualizado com todos os subdomínios de rastreamento.
- [ ] Configuração de **SSL ENABLED** no painel administrativo do Postal ajustada adequadamente para a arquitetura de proxy.
- [ ] Teste de redirecionamento de link em e-mail HTML efetuado com sucesso sem erros de segurança no navegador."""
    },
    {
        "title": "[CONFIG] Sincronização de Chave DKIM no Subdomínio educa.cdc.org.br",
        "labels": ["documentation", "security", "dns"],
        "body": """### Descrição
Garantir a correta autenticação DKIM para o subdomínio de envio do Moodle (`educa.cdc.org.br`) configurando a entrada TXT apropriada na Cloudflare para evitar rejeições do Gmail (`550-5.7.26`).

### Referências Técnicas
- Desenho de Infraestrutura e DNS: [docs/ajuda_infra.md](docs/ajuda_infra.md)
- Guia de Migração e Acesso Seguro: [docs/migration_guide.md](docs/migration_guide.md)
- Backlog de Issues: [docs/issues_backlog.md](docs/issues_backlog.md)

### Critérios de Aceite
- [ ] Entrada TXT criada na Cloudflare apontando para `postal-kkp8eJ._domainkey.educa`.
- [ ] Validação de consulta DNS (`dig txt postal-kkp8ej._domainkey.educa.cdc.org.br`) retornando a chave pública válida.
- [ ] Selo de validação DKIM marcado como verificado (verde) no painel administrativo do Postal."""
    },
    {
        "title": "[ARCH] Bypass de Conexões IPv6 para Evitar Rejeição por Falta de PTR no Gmail",
        "labels": ["infrastructure", "enhancement"],
        "body": """### Descrição
Impedir que o Postal tente estabelecer conexões de saída SMTP via IPv6 sem registro de DNS Reverso (PTR) válido na hospedagem, evitando falhas de entrega no Gmail e em outros provedores com diretrizes estritas.

### Referências Técnicas
- Manual de Resolução de Problemas: [docs/troubleshooting.md](docs/troubleshooting.md)
- Relatório de Incidentes: [docs/postmortem.md](docs/postmortem.md)
- Backlog de Issues: [docs/issues_backlog.md](docs/issues_backlog.md)

### Critérios de Aceite
- [ ] Roteamento IPv6 desativado no Host via `sysctl` (`net.ipv6.conf.all.disable_ipv6=1`).
- [ ] Serviço do Postal reiniciado para aplicar as novas configurações de rede.
- [ ] Disparo de teste via SMTP validado com sucesso no Gmail via IPv4."""
    },
    {
        "title": "[BUG] Correção de Erros de Validação CSRF (HTTP 422) no Rails via Nginx",
        "labels": ["bug", "security"],
        "body": """### Descrição
Corrigir a passagem de cabeçalhos de protocolo HTTP no Nginx Proxy para sanar falhas de validação CSRF do Rails (erro HTTP 422 ao autenticar ou atualizar credenciais no painel).

### Referências Técnicas
- Análise de Incidentes: [docs/postmortem.md](docs/postmortem.md)
- Manual de Infraestrutura: [docs/ajuda_infra.md](docs/ajuda_infra.md)
- Backlog de Issues: [docs/issues_backlog.md](docs/issues_backlog.md)

### Critérios de Aceite
- [ ] Cabeçalho `proxy_set_header X-Forwarded-Proto https;` configurado de forma estática no `default.conf`.
- [ ] Deploy e reload do Nginx no Easypanel executados.
- [ ] Login e submissão de formulários no painel do Postal validados sem erros HTTP 422."""
    },
    {
        "title": "[DOCS] Governança e Manutenção Contínua da Documentação Técnica (docs/)",
        "labels": ["documentation"],
        "body": """### Descrição
Manter a governança da documentação do projeto atualizada, auditada e em conformidade com as diretrizes de segurança, anonimização de IPs e histórico cronológico.

### Referências Técnicas
- Diretrizes de Documentação: [docs/diretrizes_documentacao.md](docs/diretrizes_documentacao.md)
- Estratégia de Execução: [docs/estrategia_execucao.md](docs/estrategia_execucao.md)
- Contexto de Inteligência Artificial: [docs/prompt_ia.md](docs/prompt_ia.md)

### Critérios de Aceite
- [ ] Todos os arquivos da pasta `docs/` possuem dados sensíveis e IPs mascarados (`76.x.x.x`).
- [ ] Tabela de revisões periódicas atualizada no `diretrizes_documentacao.md`.
- [ ] Links markdown relativos validados no `README.md`."""
    },
    {
        "title": "[FEAT] Implementação e Teste Periódico da Política de Backup Criptografado 3-2-1",
        "labels": ["backup", "security"],
        "body": """### Descrição
Garantir a execução da rotina automatizada de backup 3-2-1 com criptografia simétrica GPG, checksums SHA-256 e envio de alertas no Mattermost, realizando testes periódicos de restauração.

### Referências Técnicas
- Política de Backup e Restauração: [docs/politica_backup.md](docs/politica_backup.md)
- Estratégia de Execução: [docs/estrategia_execucao.md](docs/estrategia_execucao.md)

### Critérios de Aceite
- [ ] Script `backup_postal_prod.sh` configurado na Cron da VPS.
- [ ] Chave/passphrase GPG configurada com permissões restritas `600`.
- [ ] Webhook do Mattermost testado e validado enviando alertas de sucesso/erro.
- [ ] Teste de restauração em ambiente de homologação (Staging) realizado a cada 3 meses."""
    }
]

for item in issues_data:
    create_issue_if_not_exists(item["title"], item["body"], item["labels"])
