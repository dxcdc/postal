# Post-Mortem: Implantação e Depuração do Postal v3 com Nginx Proxy (Easypanel)

**Data do Incidente/Ajuste:** 04 de Julho de 2026  
**Autor:** Antigravity (AI Architect)  
**Status:** Resolvido e Estabilizado  

---

## 1. Resumo do Evento

Durante a instalação inicial do servidor de e-mails **Postal v3** em uma VPS Ubuntu compartilhando portas com o painel **Easypanel**, deparamo-nos com três problemas técnicos em cascata que resultaram em falhas de inicialização e em erros de **504 Gateway Time-out**. Todos os problemas foram solucionados no mesmo dia, permitindo a entrega bem-sucedida do sistema com HTTPS e login ativo.

---

## 2. Linha do Tempo e Detalhes dos Problemas

### Incidente 1: Colisão de Namespace do Projeto Docker (postal vs. install)
*   **Sintoma:** Os containers de aplicação (`web`, `smtp` e `worker`) pareciam sumir após a execução de `sudo postal start` e a tela de `postal status` retornava vazia.
*   **Causa Raiz:** O comando oficial `postal` executa as tarefas do Docker Compose forçando o nome de projeto `-p postal` (gerando containers como `postal-web-1`). No entanto, ao rodar comandos manuais de teste (`docker compose up -d`) dentro da pasta `/opt/postal/install`, o Docker subiu os containers usando o nome da pasta como escopo (`install-web-1`), gerando um conflito de controle e fazendo com que a ferramenta CLI `postal` não enxergasse o status dos containers.
*   **Solução:** Paramos o projeto incorreto (`docker compose down`) e iniciamos com o nome de projeto correto através do comando `sudo docker compose -p postal up -d` (ou simplesmente usando a CLI oficial `sudo postal start`).

### Incidente 2: Sintaxe Incorreta no Proxy Pass (Barra Invertida)
*   **Sintoma:** O container `postal-proxy` (Nginx no Easypanel) entrou em loop de travamento (crash loop) reportando:
    `invalid number of arguments in "proxy_pass" directive in /etc/nginx/conf.d/default.conf:7`
*   **Causa Raiz:** Ao copiar/gravar o arquivo de configuração do Nginx na VPS, uma barra invertida (`\`) foi acidentalmente inserida antes do caractere de ponto e vírgula na linha do `proxy_pass` (`proxy_pass http://172.17.0.1:5000\;`). O Nginx interpretou isso como parte da URL e continuou a ler a linha seguinte como argumento, quebrando a sintaxe do interpretador.
*   **Solução:** Rodamos um comando `sed` corretivo para remover a barra invertida e deixar a linha limpa com o ponto e vírgula (`proxy_pass http://...:5000;`), normalizando a execução do container Nginx.

### Incidente 3: Incompatibilidade de Gateway de Rede Docker e IP de Escuta (127.0.0.1)
*   **Sintoma:** O container do Nginx iniciou corretamente, mas ao acessar `https://core.cdc.org.br`, o navegador retornava erro **504 Gateway Time-out**. Os logs do Nginx revelavam:
    `upstream timed out (110: Operation timed out) while connecting to upstream, upstream: "http://172.17.0.1:5000/"`
*   **Causa Raiz:** Foram identificados dois problemas de rede combinados:
    1.  O Nginx estava tentando encaminhar o tráfego para `172.17.0.1` (o gateway padrão do Docker0), mas o Easypanel roda seus aplicativos em uma rede privada customizada (com IP do cliente sendo `10.11.0.4` e o gateway da VPS sendo `10.11.0.1`).
    2.  O Postal v3 por padrão escuta apenas na interface de loopback da VPS (`127.0.0.1:5000`), rejeitando qualquer requisição que venha da ponte do Docker (origem `10.11.x.x` apontando para o IP de gateway `10.11.0.1`).
*   **Solução:** 
    1.  Adicionamos a diretiva `web_server.default_bind_address: 0.0.0.0` no arquivo `/opt/postal/config/postal.yml` para fazer o Postal escutar em todas as interfaces de rede da VPS.
    2.  Atualizamos o arquivo `default.conf` do Nginx Proxy para apontar para o gateway correto da rede do Easypanel: `http://10.11.0.1:5000`.

### Incidente 4: Conectividade Docker Swarm e Gateway Inativo (Connection Refused)
*   **Sintoma:** Após configurar o domínio definitivo `postal.cdc.org.br`, o Nginx retornava erro `502 Bad Gateway` e o Easypanel exibia a tela `Service is not reachable`. O container do Nginx entrava em loop de reinicialização sendo finalizado pelo *health check* do Easypanel.
*   **Causa Raiz:**
    1.  O Easypanel utiliza Docker Swarm. Na rede Swarm (*overlay*), o IP do gateway (`10.11.0.1`) é dinâmico ou inexistente no nível da interface do container, gerando um erro de `Connection Refused` quando o Nginx tentava realizar o proxy pass.
    2.  O *health check* do Easypanel identificava o erro `502` do Nginx como uma falha de integridade do app e matava o container em loop.
    3.  Durante a edição manual do domínio no nano, o caractere de escape barra invertida (`\`) foi reintroduzido acidentalmente no `proxy_pass`, causando falha de sintaxe.
*   **Solução:**
    1.  Corrigimos a sintaxe do Nginx removendo a barra invertida (`\;` para `;`).
    2.  Liberamos a porta `5000` no firewall da VPS (`sudo ufw allow 5000/tcp`).
    3.  Alteramos o `proxy_pass` do Nginx para apontar diretamente para o IP público da VPS (`http://76.13.227.xxx:5000`), bypassando as flutuações das pontes de rede internas do Docker Swarm.

---

## 3. Lições Aprendidas

1.  **Isolamento de Redes no Easypanel:** Sempre verificar os IPs de entrada dos containers nos logs (`client: X.X.X.X`) para deduzir o IP correto do gateway do host no Docker (que geralmente termina em `.1` na mesma faixa do cliente).
2.  **Escuta de Aplicações Host:** Serviços que rodam diretamente no host com `network_mode: host` e precisam interagir com containers Docker não podem escutar apenas em `127.0.0.1`. Eles precisam escutar em `0.0.0.0` (ou na interface específica da ponte Docker) para que os containers consigam fazer a conexão via IP de gateway.
3.  **Sanitização de Caracteres no Terminal:** Evitar o uso de caracteres especiais de escape (`\`) em comandos rápidos do terminal que envolvam configurações críticas, pois eles podem ser interpretados incorretamente dependendo do shell ativo (bash vs. zsh).
4.  **Bypass de Rede Swarm com IP Público:** Em orquestradores que utilizam Docker Swarm (como Easypanel), as conexões entre containers e serviços do host são mais estáveis e fáceis de gerenciar se feitas através do IP público (ou IP privado da placa física da VPS), sob proteção do firewall local (UFW), evitando o uso de gateways de ponte instáveis.
5.  **Monitoramento de Health Checks:** Falhas de conexões em upstream (como 502 Bad Gateway) podem derrubar contêineres se o health check do orquestrador for agressivo e esperar retornos exclusivamente da família `200 OK`.

