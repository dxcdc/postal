# Manual de Resolução de Problemas (Troubleshooting) — CDC

Este guia consolidado contém diagnósticos técnicos, comandos de teste e soluções rápidas para lidar com incidentes de contêineres, banco de dados, rede, permissões, SMTP e comunicações no servidor de e-mails da **CDC**.

---

## 1. Contêineres Travados ou em Loop (Crash Loop)
*   **Sintoma:** O comando `sudo postal status` ou `docker ps` mostra contêineres com status `Restarting` ou `Exited`.
*   **Diagnóstico:** Logs internos do contêiner indicando falhas de sintaxe ou portas em conflito.
    ```bash
    # Visualizar as últimas 100 linhas de log do contêiner com falha
    sudo docker logs --tail 100 postal-proxy
    ```
*   **Soluções:**
    *   **Erro de sintaxe no Nginx:** Ao editar `/etc/easypanel/.../default.conf`, remova barras invertidas acidentais no `proxy_pass` (ex: `\;` deve ser `;`).
    *   **Portas em uso:** Se o container SMTP não subir, verifique se outro MTA (como Postfix ou Sendmail) está ativo na VPS:
        ```bash
        sudo systemctl stop postfix
        sudo systemctl disable postfix
        ```

---

## 2. Erros de Banco de Dados (MariaDB)
*   **Sintoma:** Postal ou Moodle reportando `Connection Refused` ou `Access Denied` ao conectar no banco de dados.
*   **Diagnóstico:** Verifique se a porta `3306` do banco está respondendo na interface local `127.0.0.1`.
    ```bash
    telnet 127.0.0.1 3306
    ```
*   **Soluções:**
    *   **Banco fora do ar:** Inicie o container do banco: `docker start postal-mariadb`.
    *   **Charset incorreto:** Certifique-se de que o banco de dados do Postal utilize codificação UTF-8 (`utf8mb4_unicode_ci`).

---

## 3. Problemas de Permissões de Arquivos
*   **Sintoma:** Falhas ao gravar arquivos de logs, anexos de e-mail ou dados persistentes do Moodle (`moodledata`).
*   **Diagnóstico:**
    ```bash
    ls -la /opt/postal/config
    ```
*   **Soluções:**
    *   **Evite o uso de `chmod 777`:** Use sempre permissões restritivas mínimas. Os diretórios devem pertencer ao usuário executor dos serviços (ex: `www-data` para o Moodle e usuário `postal` ou `root` para as configurações do Postal):
        ```bash
        # Moodle Data seguro
        sudo chown -R www-data:www-data /var/moodledata
        sudo find /var/moodledata -type d -exec chmod 770 {} \;
        sudo find /var/moodledata -type f -exec chmod 660 {} \;
        ```

---

## 4. Rejeição de E-mails pelo Gmail (IPv6 PTR Guidelines)
*   **Sintoma:** E-mails de teste em status `Hard Fail` no painel do Postal exibindo erro do tipo `550-5.7.1 Gmail has detected that this message does not meet IPv6 sending guidelines regarding PTR records...`.
*   **Diagnóstico:** O Google exige que qualquer conexão SMTP via IPv6 possua DNS reverso configurado. Se a VPS não possuir esse PTR configurado, o e-mail será negado.
*   **Solução:** Desative o protocolo IPv6 para forçar a VPS a enviar apenas via IPv4:
    ```bash
    sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
    sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
    ```

---

## 5. Falhas de Alertas no Mattermost
*   **Sintoma:** Notificações de backup ou alertas operacionais do Postal não chegam nos canais do Mattermost.
*   **Diagnóstico:**
    *   Teste o webhook isoladamente usando um comando `curl`:
        ```bash
        curl -i -X POST -H 'Content-Type: application/json' -d '{"text": "Teste"}' <MATTERMOST_WEBHOOK_URL>
        ```
*   **Soluções:**
    *   **Erro 404 (Not Found):** A URL do webhook foi digitada incorretamente ou o webhook foi apagado no Mattermost.
    *   **Erro 403 (Forbidden) / Firewall:** Verifique se as regras de saída do Firewall (UFW) na VPS estão bloqueando conexões HTTP/HTTPS externas.

---

## 6. Logs e Monitoramento
Para depurar problemas em tempo real na VPS:
```bash
# 1. Cauda de logs unificada do Postal
sudo postal logs

# 2. Filtrar logs do Nginx Proxy buscando por erros HTTP 5xx
docker logs postal-proxy 2>&1 | grep -E "500|502|504"

# 3. Sanitizar logs removendo dados sensíveis de credenciais antes de compartilhar
sudo tail -f /var/log/syslog | grep --line-buffered -vi "password"
```

---

## 7. Checklist de Emergência (Quedas)
Se o servidor de e-mails parar completamente:
1.  [ ] **Disco:** O disco está cheio? (`df -h`). Limpe backups antigos se necessário.
2.  [ ] **Memória:** A RAM esgotou? (`free -h`). Verifique se o OOM-Killer derrubou o container do MariaDB.
3.  [ ] **Rede:** As portas SMTP (`25` ou `2525`) estão ouvindo? (`sudo ss -tulpn`).
4.  [ ] **Contêineres:** A stack está rodando? (`docker ps`).
5.  [ ] **Logs:** Quais são os últimos erros descritos no `sudo postal logs`?
