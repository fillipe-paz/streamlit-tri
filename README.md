# 📊 Calculadora TRI - Teoria de Resposta ao Item

Aplicação Streamlit para demonstração didática de cálculos TRI (Teoria de Resposta ao Item) com questões de conhecimentos gerais em português.

## 🎯 Funcionalidades

- ✅ **Teste Multiusuário**: Múltiplos alunos acessam simultaneamente
- ⏱️ **Timer por Questão**: 45 segundos por questão com feedback visual
- 📝 **30-40 Questões**: Conhecimentos gerais (História, Geografia, Ciências, Cultura)
- 📊 **Cálculo TRI**: Modelo logístico de 3 parâmetros com estimação de habilidade (θ)
- 👨‍🏫 **Painel Admin**: Dashboard para professores visualizarem resultados de todos os alunos
- 💾 **Armazenamento Centralizado**: Respostas salvas em Google Sheets

## 🚀 Como Usar

### Para Alunos

1. Acesse a aplicação
2. Digite seu nome completo
3. Responda as questões dentro do tempo (45s cada)
4. Visualize seu resultado com explicações TRI

### Para Professores

1. Acesse o "Painel Admin" na barra lateral
2. Digite a senha de administrador
3. Visualize estatísticas da turma, resultados individuais e exporte dados

## ⚙️ Configuração para Deploy

### 1. Criar Google Sheet

1. Acesse [Google Sheets](https://sheets.google.com)
2. Crie uma nova planilha chamada "TRI_Responses"
3. Anote o ID da planilha (está na URL)

### 2. Criar Service Account

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione existente
3. Ative a Google Sheets API
4. Crie uma Service Account
5. Baixe o arquivo JSON de credenciais
6. Compartilhe a planilha com o email da service account (permissão de editor)

### 3. Configurar Secrets no Streamlit Cloud

No Streamlit Cloud, adicione os seguintes secrets:

```toml
# Senha do painel administrativo
admin_password = "sua_senha_aqui"

# Credenciais do Google Sheets (copie do arquivo JSON)
[gcp_service_account]
type = "service_account"
project_id = "seu-project-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "seu-service-account@projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

# ID da planilha
sheet_id = "ID_DA_SUA_PLANILHA_AQUI"
```

### 4. Deploy

1. Faça push do código para GitHub
2. Conecte o repositório no [Streamlit Cloud](https://streamlit.io/cloud)
3. Configure os secrets
4. Deploy!

## 📚 Sobre TRI

A Teoria de Resposta ao Item (TRI) é uma metodologia utilizada para avaliar habilidades através de testes. Diferentemente da Teoria Clássica dos Testes, que considera apenas o percentual de acertos, a TRI leva em conta:

- **Discriminação (a)**: Capacidade da questão distinguir alunos de diferentes habilidades
- **Dificuldade (b)**: Nível de habilidade necessário para 50% de chance de acerto
- **Acerto ao Acaso (c)**: Probabilidade de acerto por chute

### Modelo Logístico de 3 Parâmetros

$$P(\theta) = c + \frac{1-c}{1 + e^{-a(\theta - b)}}$$

Onde:
- $P(\theta)$ = Probabilidade de acerto dado a habilidade θ
- $\theta$ = Habilidade do aluno (estimada)
- $a$ = Discriminação do item
- $b$ = Dificuldade do item
- $c$ = Probabilidade de acerto ao acaso

## 🛠️ Desenvolvimento Local

```bash
# Clonar repositório
git clone <seu-repositorio>
cd tri-calculator

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo de secrets local
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editar .streamlit/secrets.toml com suas credenciais

# Executar aplicação
streamlit run app.py
```

## 📄 Licença

MIT License - Uso educacional livre
