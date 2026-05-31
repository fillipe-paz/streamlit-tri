# 🚀 Guia de Início Rápido - Calculadora TRI

## Desenvolvimento Local (Com Supabase)

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

### 2. Configurar Supabase

**Opção A: Seguir guia completo**
```bash
# Veja o guia detalhado em:
cat SETUP_SUPABASE.md
```

**Opção B: Passos rápidos**

1. Crie conta em https://supabase.com
2. Crie novo projeto
3. No SQL Editor, execute:
   ```sql
   -- Cole o SQL do SETUP_SUPABASE.md
   ```
4. Copie URL e Key do projeto (Settings → API)
5. Crie `.streamlit/secrets.toml`:
   ```toml
   admin_password = "admin123"
   
   [supabase]
   url = "https://seu-projeto.supabase.co"
   key = "sua-anon-key"
   ```

### 3. Testar Conexão

```bash
# Verificar se Supabase está configurado
python test_supabase.py
```

Se todos os testes passarem ✅, prossiga!

### 4. Executar Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

## Deploy no Streamlit Cloud (Produção)

### 1. Preparar Repositório

```bash
# Garantir que secrets.toml não será commitado
git add .gitignore
git commit -m "Add gitignore"

# Adicionar código ao repositório
git add .
git commit -m "Initial commit - TRI Calculator"
git push origin main
```

### 2. Deploy no Streamlit Cloud

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

# Credenciais do Supabase
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-anon-key-aqui"
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
