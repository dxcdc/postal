# Backup da Zona DNS - cdc.org.br

Este documento contém o backup de todos os registros DNS do domínio `cdc.org.br` extraídos do Registro.br em 10 de Julho de 2026 antes da migração para a Cloudflare.

## Registros DNS

| Tipo | Nome (Host) | Dados (Conteúdo/Valor) | Notas / Destino |
| :--- | :--- | :--- | :--- |
| **A** | `cdc.org.br` | `76.76.21.21` | Aponta para a Vercel |
| **MX** | `cdc.org.br` | `1 smtp.google.com` | Google Workspace |
| **MX** | `cdc.org.br` | `1 aspmx.l.google.com` | Google Workspace |
| **MX** | `cdc.org.br` | `5 alt1.aspmx.l.google.com` | Google Workspace |
| **MX** | `cdc.org.br` | `5 alt2.aspmx.l.google.com` | Google Workspace |
| **MX** | `cdc.org.br` | `10 alt3.aspmx.l.google.com` | Google Workspace |
| **MX** | `cdc.org.br` | `10 alt4.aspmx.l.google.com` | Google Workspace |
| **TXT** | `cdc.org.br` | `"v=spf1 include:_spf.google.com ~all"` | Google SPF |
| **TXT** | `cdc.org.br` | `"v=spf1 ip4:169.254.1.2/16 ip4:186.227.207.10/29 ip4:138.128.179.82/29 ip4:184.171.250.114/29 ip4:138.128.179.2/29 ip4:107.190.137.34/28 ip4:184.171.248.50/29 ip4:107.190.137.36/29 ip4:50.97.80.197 ip4:75.126.209.248/30 include:_spf.google.com ~all"` | SPF Completo antigo |
| **CNAME** | `4nkkc62wvmhf.cdc.org.br` | `gv-6zpmf6a72msq7b.dv.googlehosted.com` | Verificação do Google |
| **TXT** | `google._domainkey.cdc.org.br` | `"v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCJJ5+k7jYprKIJkHu5MOoG9Eg6diV1KnQCMcZavb9ztFZFilUm6fushjCtpDY+rKZcDg4J/OI+OmG+qumK3dDKXN5Xknylsez8Zjk00xLfVyPtUvIJaFuQTlFP7hvADZA9UX8Q1P0PDIcMEx+OWUwx1b/2VAQBfk7oTycqIZdHmwIDAQAB"` | Google DKIM |
| **A** | `automatiza.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `chat.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `core.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `digital.cdc.org.br` | `131.221.77.9` | IP Externo (Legado/Outro Servidor) |
| **A** | `educa.cdc.org.br` | `76.13.227.135` | Moodle (VPS principal) |
| **TXT** | `educa.cdc.org.br` | `"v=spf1 a mx include:spf.postal.cdc.org.br ~all"` | SPF do Moodle (Postal) |
| **TXT** | `postal-kkp8ej._domainkey.educa.cdc.org.br` | (Chave DKIM do Postal para o Moodle) | DKIM do Moodle (*Corrigir erros de digitação ao colar*) |
| **CNAME** | `psrp.educa.cdc.org.br` | `rp.postal.cdc.org.br` | Return Path do Moodle |
| **CNAME** | `track.educa.cdc.org.br` | `track.postal.cdc.org.br` | Rastreamento de Cliques/Aberturas do Moodle |
| **A** | `engine.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `erpcompras.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `estoque.cdc.org.br` | `35.184.131.8` | IP Externo (GCP/Outro Servidor) |
| **A** | `hub.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `iac.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `integracao.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `live.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `n8n.cdc.org.br` | `76.13.227.135` | VPS principal (n8n) |
| **CNAME** | `notificacao.cdc.org.br` | `smtpdlv.com.br` | Locaweb SMTP (Legado) |
| **CNAME** | `_dmarc.notificacao.cdc.org.br` | `_dmarc.smtpdlv.com.br` | Locaweb DMARC (Legado) |
| **TXT** | `smtplw.notificacao.cdc.org.br` | `"3fe4ddad2311dc5525e09141bcd3d82a"` | Chave Locaweb (Legado) |
| **A** | `pontoeletronico.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `postal.cdc.org.br` | `76.13.227.135` | Painel Administrativo Postal v3 |
| **CNAME** | `track.postal.cdc.org.br` | `postal.cdc.org.br` | Servidor de Track do Postal |
| **A** | `relogio.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `status.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `transportes.cdc.org.br` | `76.13.227.135` | VPS principal (Easypanel) |
| **A** | `vpn.cdc.org.br` | `76.13.227.135` | VPS principal (VPN) |
| **A** | `wiki.cdc.org.br` | `76.13.227.135` | VPS principal (Wiki) |
| **CNAME** | `www.cdc.org.br` | `site-cdc.vercel.app` | Site Principal na Vercel |
