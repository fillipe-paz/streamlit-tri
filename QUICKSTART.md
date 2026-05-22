# 🚀 Guia de Início Rápido - Calculadora TRI

## Desenvolvimento Local (Teste sem Google Sheets)

### 1. Instalação

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração Mínima (Sem Google Sheets)

Para testar localmente SEM Google Sheets, você pode comentar temporariamente o salvamento no banco:

1. Abra `modules/database.py`
2. Nas funções `save_response`, `start_session` e `complete_session`, comente o código e retorne `True`

**OU** configure um arquivo secrets.toml mínimo:

```bash
# Criar arquivo de secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edite `.streamlit/secrets.toml` e adicione uma senha admin temporária:

```toml
admin_password = "admin123"
sheet_id = "fake_id"

[gcp_service_account]
type = "service_account"
project_id = "test"
private_key_id = "test"
private_key = "test"
client_email = "test@test.com"
client_id = "test"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "test"
```

### 3. Executar Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

## Deploy no Streamlit Cloud (Produção)

### 1. Preparar Google Sheets

1. Acesse [Google Sheets](https://sheets.google.com)
2. Crie uma nova planilha chamada "TRI_Responses"
3. Anote o ID da planilha (está na URL: `https://docs.google.com/spreadsheets/d/{ID_AQUI}/edit`)

### 2. Criar Service Account no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto (ou selecione existente)
3. Ative a **Google Sheets API**:
   - Menu → APIs & Services → Library
   - Busque "Google Sheets API"
   - Clique em "Enable"
4. Crie uma **Service Account**:
   - Menu → APIs & Services → Credentials
   - Clique em "Create Credentials" → "Service Account"
   - Preencha nome e ID
   - Clique em "Create and Continue"
   - Skip permissions (Next)
   - Skip grant users (Done)
5. Crie uma **Key** para a Service Account:
   - Clique na service account criada
   - Aba "Keys"
   - "Add Key" → "Create new key"
   - Selecione "JSON"
   - Clique em "Create" (arquivo JSON será baixado)
6. **Compartilhe a planilha** com a service account:
   - Abra sua planilha Google Sheets
   - Clique em "Compartilhar"
   - Cole o email da service account (exemplo: `meu-projeto@appspot.gserviceaccount.com`)
   - Dê permissão de **Editor**
   - Clique em "Enviar"

### 3. Preparar Repositório

```bash
# Garantir que secrets.toml não será commitado
git add .gitignore
git commit -m "Add gitignore"

# Adicionar código ao repositório
git add .
git commit -m "Initial commit - TRI Calculator"
git push origin main
```

### 4. Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com GitHub
3. Clique em "New app"
4. Selecione:
   - Repository: seu repositório
   - Branch: main
   - Main file path: `app.py`
5. Clique em "Advanced settings"
6. Na seção "Secrets", cole o conteúdo no formato TOML:

```toml
# Senha do painel admin
admin_password = "SuaSenhaSeguraAqui"

# ID da planilha Google Sheets
sheet_id = "SEU_SHEET_ID_AQUI"

# Credenciais da Service Account (copie do arquivo JSON baixado)
[gcp_service_account]
type = "service_account"
project_id = "seu-project-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "seu-email@projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

7. Clique em "Deploy"
8. Aguarde o deploy (2-5 minutos)

## Testando a Aplicação

### Como Aluno:
1. Acesse a URL do app
2. Digite seu nome completo
3. Clique em "Entrar"
4. Navegue para "Fazer Teste"
5. Responda as 40 questões (45s cada)
6. Veja seus resultados TRI

### Como Professor:
1. Acesse "Painel Admin" na barra lateral
2. Digite a senha de administrador
3. Visualize:
   - Visão geral da turma
   - Lista de alunos e resultados
   - Análise individual detalhada
   - Estatísticas por questão
   - Exporte dados em CSV

## Estrutura da Aplicação

```
tri-calculator/
├── app.py                      # Página principal (login)
├── pages/
│   ├── 1_📝_Fazer_Teste.py    # Interface do teste
│   └── 2_📊_Painel_Admin.py   # Dashboard admin
├── modules/
│   ├── database.py             # Integração Google Sheets
│   ├── tri_calculator.py       # Cálculos TRI
│   └── timer.py                # Gerenciamento de timer
├── data/
│   └── questions.json          # 40 questões + parâmetros TRI
├── .streamlit/
│   ├── config.toml             # Configurações do app
│   └── secrets.toml.example    # Template de secrets
├── requirements.txt            # Dependências Python
└── README.md                   # Documentação completa
```

## Funcionalidades Principais

✅ **Multiusuário**: Múltiplos alunos simultaneamente
✅ **Timer**: 45 segundos por questão com feedback visual
✅ **40 Questões**: Conhecimentos gerais em português
✅ **Cálculo TRI**: Modelo logístico 3 parâmetros
✅ **Armazenamento**: Google Sheets (persistente)
✅ **Visualizações**: Gráficos interativos (Plotly)
✅ **Painel Admin**: Dashboard completo para professores
✅ **Export**: Dados em CSV

## Troubleshooting

### Erro ao conectar Google Sheets

**Sintoma**: "Erro ao conectar ao Google Sheets"

**Soluções**:
1. Verifique se a Google Sheets API está ativada
2. Confirme que a planilha foi compartilhada com a service account
3. Verifique se o `sheet_id` está correto nos secrets
4. Certifique-se de que a `private_key` está com quebras de linha corretas (`\n`)

### Timer não funciona

**Sintoma**: Countdown não atualiza

**Solução**: 
- A biblioteca `streamlit-autorefresh` deve estar instalada
- Verifique se há conflitos com outras libraries

### Senha admin não funciona

**Sintoma**: "Erro ao verificar senha"

**Solução**:
- Verifique se `admin_password` está configurado nos secrets
- Certifique-se de não ter espaços antes/depois da senha

### Questões não carregam

**Sintoma**: "Erro ao carregar questões"

**Solução**:
- Verifique se `data/questions.json` existe
- Valide o JSON em https://jsonlint.com
- Certifique-se de que o arquivo está no repositório

## Suporte

Para dúvidas ou problemas:
1. Revise o README.md completo
2. Verifique a documentação do Streamlit: https://docs.streamlit.io
3. Consulte a documentação do Google Sheets API

## Licença

MIT License - Uso educacional livre
