# Guia de Troubleshooting (Resolução de Problemas)

Este documento reúne os problemas mais comuns encontrados no gerenciamento e manutenção do servidor de e-mails Postal com Nginx/Easypanel e como solucioná-los.

---

## 1. Erro "504 Gateway Time-out" no Navegador

Se o painel web em `https://postal.cdc.org.br` parar de responder e exibir a tela de Timeout:

1.  **Verifique se os containers do Postal estão rodando:**
    No terminal da VPS, execute:
    ```bash
    sudo postal status
    ```
    Se algum serviço estiver parado, inicie-o:
    ```bash
    sudo postal start
    ```

2.  **Verifique se a escuta em `0.0.0.0` está ativa:**
    ```bash
    sudo ss -tulpn | grep 5000
    ```
    Se retornar `127.0.0.1:5000` em vez de `0.0.0.0:5000` (ou `*:5000`), a configuração de bind do Postal foi perdida. Certifique-se de que a linha abaixo está no final do arquivo `/opt/postal/config/postal.yml` e reinicie o Postal:
    ```yaml
    web_server:
      default_bind_address: 0.0.0.0
    ```

3.  **Verifique se a rota do proxy aponta para o IP público da VPS:**
    Como o Easypanel roda com Docker Swarm, as redes internas (ponte/gateway) são instáveis. Garanta que o arquivo `/etc/easypanel/projects/cdc-ezpoint/postal-proxy/volumes/config/default.conf` aponte para o IP público da sua VPS:
    ```nginx
    proxy_pass http://76.13.227.135:5000;
    ```
    Em seguida, rode o Deploy no painel do Easypanel.

---

## 2. Erro de Conexão SMTP "Connection Refused" no Moodle

Se o Moodle não conseguir enviar e-mails e der erro de conexão com o host de SMTP:

1.  **Verifique se o serviço SMTP do Postal está escutando na porta 2525:**
    ```bash
    sudo ss -tulpn | grep 2525
    ```
2.  **Verifique as regras do Firewall local (UFW):**
    O firewall do Ubuntu pode estar bloqueando a porta interna `2525` de receber requisições dos containers. Libere a porta com:
    ```bash
    sudo ufw allow 2525/tcp
    ```
3.  **Se o Moodle estiver na mesma máquina física:**
    Em vez de apontar o SMTP Host para `postal.cdc.org.br` (conexão externa), aponte nas configurações do Moodle para o IP de gateway do Docker (`10.11.0.1:2525` ou `172.17.0.1:2525`), fazendo o tráfego ir direto pela rede interna sem sair para a internet.

---

## 3. E-mails Enviados Vão Direto para o SPAM

Se os e-mails estão sendo enviados, mas caem na pasta de Spam do Gmail/Hotmail:

1.  **Validar Registros de SPF e DKIM:**
    Acesse o painel do Postal, vá no seu servidor de e-mail (Moodle) -> aba **Domains**, e verifique se há algum selo vermelho indicando que o DNS não está propagado ou tem erros de chaves.
2.  **Configurar o PTR (Reverse DNS) da VPS:**
    *   **Sintoma:** O Gmail recusa e-mails de IPs sem DNS reverso configurado.
    *   **Resolução:** Entre no painel da sua empresa de VPS (onde você aluga a máquina) e mude o campo "Reverse DNS" (ou PTR) do IP da sua máquina para apontar exatamente para o seu domínio principal (ex: `postal.cdc.org.br`).
3.  **Testar com Mail-Tester:**
    Envie um e-mail de teste do Postal para o site [mail-tester.com](https://www.mail-tester.com/). Ele dará uma nota de 0 a 10 e apontará exatamente qual configuração (DMARC, SPF, assinatura DKIM ou IP em blacklist) está prejudicando a sua entregabilidade.

---

## 4. Quedas e Lentidão Geral (Out of Memory)

Se o Postal ou o Moodle travarem misteriosamente e sem logs claros de erro:

1.  **Verifique o uso de memória RAM:**
    ```bash
    free -h
    ```
    Se a memória disponível estiver próxima de zero, o Linux executa o *OOM Killer* (Out Of Memory Killer), derrubando o container que consome mais memória (geralmente o banco de dados MariaDB ou o Postal Web).
2.  **Configurar Memória Swap (Se necessário):**
    Caso a VPS tenha pouca RAM (menos de 4 GB) para rodar o Moodle + Postal juntos, crie uma memória swap de segurança de 2 GB:
    ```bash
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    ```

---

## 5. Erro "Service is not reachable" no Easypanel (Nginx Crash Loop)

Se o navegador exibir a tela azul "Service is not reachable":

1.  **Verifique se o contêiner do proxy está ativo:**
    ```bash
    sudo docker ps -a | grep proxy
    ```
    Se ele estiver listado com o status `Exited (1)`, significa que há um erro de sintaxe no arquivo `/etc/easypanel/projects/cdc-ezpoint/postal-proxy/volumes/config/default.conf`.
2.  **Corrija a barra invertida (escape) no proxy_pass:**
    Ao editar o arquivo com o nano, certifique-se de que a linha do `proxy_pass` termina com apenas ponto e vírgula `;` (e não com `\;`).
3.  **Remover a barra via terminal:**
    ```bash
    sudo sed -i 's/5000\\;/5000;/g' /etc/easypanel/projects/cdc-ezpoint/postal-proxy/volumes/config/default.conf
    ```
    Em seguida, realize o **Deploy** no Easypanel.

