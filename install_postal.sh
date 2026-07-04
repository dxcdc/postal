#!/usr/bin/env bash

# Script de Instalação e Configuração do Postal Mail Server
# Este script deve ser executado com privilégios de superusuário (root ou sudo)
# na VPS onde o Postal será hospedado.

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sem Cor

echo -e "${GREEN}=== Iniciando Preparação para Instalação do Postal ===${NC}"

# 1. Verificar se o script está rodando como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Erro: Por favor, execute este script como root (sudo).${NC}"
  exit 1
fi

# 2. Detectar Distribuição Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Erro: Não foi possível detectar o Sistema Operacional.${NC}"
    exit 1
fi

echo -e "Sistema Operacional Detectado: ${YELLOW}$OS${NC}"

# 3. Instalar Dependências Necessárias (Docker, Git, Curl, JQ)
echo -e "\n${GREEN}1. Verificando e instalando dependências...${NC}"

install_dependencies_ubuntu() {
    apt-get update
    apt-get install -y git curl jq gnupg lsb-release
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Instalando Docker...${NC}"
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
}

install_dependencies_opensuse() {
    zypper refresh
    zypper install -y git curl jq
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Instalando Docker...${NC}"
        zypper install -y docker docker-compose
        systemctl enable docker
        systemctl start docker
    fi
}

case "$OS" in
    ubuntu|debian)
        install_dependencies_ubuntu
        ;;
    opensuse*|suse)
        install_dependencies_opensuse
        ;;
    *)
        echo -e "${YELLOW}Distribuição não suportada automaticamente. Certifique-se de instalar o Docker e Docker Compose manualmente.${NC}"
        ;;
esac

# Validar se o Docker e Docker Compose estão funcionais
if command -v docker &> /dev/null; then
    echo -e "${GREEN}Docker instalado com sucesso: $(docker --version)${NC}"
else
    echo -e "${RED}Erro: Falha ao garantir a instalação do Docker.${NC}"
    exit 1
fi

# 4. Clonar o Repositório de Instalação Oficial do Postal
echo -e "\n${GREEN}2. Clonando instalador oficial do Postal...${NC}"
if [ -d "/opt/postal/install" ]; then
    echo -e "${YELLOW}Diretório /opt/postal/install já existe. Pulando clone.${NC}"
else
    mkdir -p /opt/postal
    git clone https://github.com/postalserver/install.git /opt/postal/install
fi

# Criar link simbólico para o comando 'postal' ficar disponível globalmente
if [ -L "/usr/bin/postal" ]; then
    rm /usr/bin/postal
fi
ln -s /opt/postal/install/bin/postal /usr/bin/postal

echo -e "${GREEN}Comando 'postal' linkado em /usr/bin/postal.${NC}"

# 5. Próximos Passos Manuais
echo -e "\n${GREEN}=== Instalação de Dependências Concluída! ===${NC}"
echo -e "Para continuar com a configuração do Postal, siga estes passos na VPS:"
echo -e "${YELLOW}Passo 1:${NC} Execute o bootstrap informando o seu subdomínio do Postal:"
echo -e "  ${GREEN}postal bootstrap postal.seudominio.com${NC}"
echo -e "  *(Isso criará os arquivos em /opt/postal/config)*"
echo -e ""
echo -e "${YELLOW}Passo 2:${NC} Configure as credenciais do banco de dados no arquivo:"
echo -e "  ${GREEN}nano /opt/postal/config/postal.yml${NC}"
echo -e "  *(Edite as senhas nas seções 'rails' e 'mariadb' se necessário)*"
echo -e ""
echo -e "${YELLOW}Passo 3:${NC} Inicialize o banco de dados e os containers:"
echo -e "  ${GREEN}postal initialize${NC}"
echo -e ""
echo -e "${YELLOW}Passo 4:${NC} Crie seu usuário administrador:"
echo -e "  ${GREEN}postal make-user${NC}"
echo -e ""
echo -e "${YELLOW}Passo 5:${NC} Inicie o servidor:"
echo -e "  ${GREEN}postal start${NC}"
echo -e ""
echo -e "======================================================="
