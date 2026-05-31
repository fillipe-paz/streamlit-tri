# 🚀 Setup Supabase para Calculadora TRI

Este guia mostra como configurar o Supabase para a aplicação.

## 1️⃣ Criar Conta no Supabase

1. Acesse: https://supabase.com
2. Clique em "Start your project"
3. Crie uma conta (pode usar GitHub)

## 2️⃣ Criar Novo Projeto

1. No dashboard, clique em "New Project"
2. Preencha:
   - **Name**: `tri-calculator` (ou qualquer nome)
   - **Database Password**: Crie uma senha forte e **guarde-a**
   - **Region**: Escolha a região mais próxima (ex: South America)
3. Clique em "Create new project"
4. Aguarde 2-3 minutos para o projeto ser criado

## 3️⃣ Criar Tabelas do Banco de Dados

1. No menu lateral, clique em **"SQL Editor"**
2. Clique em **"New query"**
3. Cole o SQL abaixo e clique em **"Run"**:

```sql
-- Criar tabela de configuração da prova
CREATE TABLE exam_config (
    id SERIAL PRIMARY KEY,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserir configurações padrão (sem horários definidos inicialmente)
INSERT INTO exam_config (config_key, config_value) 
VALUES 
    ('exam_start', NULL),
    ('exam_deadline', NULL),
    ('num_questions', '40');

-- Criar tabela de sessões
CREATE TABLE sessions (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    final_theta FLOAT,
    total_correct INTEGER,
    total_timeout INTEGER,
    num_questions INTEGER DEFAULT 40,
    status TEXT NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar tabela de respostas
CREATE TABLE responses (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    question_id TEXT NOT NULL,
    answer TEXT,
    is_correct BOOLEAN NOT NULL,
    is_timeout BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    theta_estimate FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar índices para melhor performance
CREATE INDEX idx_sessions_student_id ON sessions(student_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_responses_student_id ON responses(student_id);
CREATE INDEX idx_responses_question_id ON responses(question_id);

-- Habilitar Row Level Security (RLS)
ALTER TABLE exam_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;

-- Criar políticas permissivas (para aplicação funcionar)
-- Permitir todas operações em exam_config (SELECT, INSERT, UPDATE, DELETE)
CREATE POLICY "Enable read for all" ON exam_config FOR SELECT USING (true);
CREATE POLICY "Enable insert for all" ON exam_config FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for all" ON exam_config FOR UPDATE USING (true);
CREATE POLICY "Enable delete for all" ON exam_config FOR DELETE USING (true);

-- Permitir todas operações em sessions
CREATE POLICY "Enable read for all on sessions" ON sessions FOR SELECT USING (true);
CREATE POLICY "Enable insert for all on sessions" ON sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for all on sessions" ON sessions FOR UPDATE USING (true);
CREATE POLICY "Enable delete for all on sessions" ON sessions FOR DELETE USING (true);

-- Permitir todas operações em responses
CREATE POLICY "Enable read for all on responses" ON responses FOR SELECT USING (true);
CREATE POLICY "Enable insert for all on responses" ON responses FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for all on responses" ON responses FOR UPDATE USING (true);
CREATE POLICY "Enable delete for all on responses" ON responses FOR DELETE USING (true);
```

4. Você verá: **"Success. No rows returned"** ✅

## 4️⃣ Obter Credenciais da API

1. No menu lateral, clique em **"Settings"** (ícone de engrenagem)
2. Clique em **"API"**
3. Você verá duas informações importantes:

   - **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
   - **anon public**: Uma chave longa começando com `eyJ...`

4. **Copie esses valores** (vamos usar no próximo passo)

## 5️⃣ Configurar Secrets Localmente

1. Crie o arquivo `.streamlit/secrets.toml`:

```bash
# No terminal, execute:
mkdir -p .streamlit
nano .streamlit/secrets.toml
```

2. Cole este conteúdo (substitua pelos seus valores):

```toml
# Senha do painel admin
admin_password = "admin123"

# Credenciais do Supabase
[supabase]
url = "https://seu-projeto-aqui.supabase.co"
key = "sua-anon-key-aqui-muito-longa"
```

3. Salve o arquivo:
   - No nano: `Ctrl+O`, `Enter`, `Ctrl+X`
   - No VS Code: `Ctrl+S`

## 6️⃣ Instalar Dependências

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar/atualizar dependências
pip install -r requirements.txt
```

## 7️⃣ Testar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

### ✅ Testar:
1. Digite seu nome
2. Clique em "Entrar"
3. Se não houver erros, está funcionando! 🎉

### Verificar dados no Supabase:
1. Volte ao dashboard do Supabase
2. Clique em **"Table Editor"** no menu lateral
3. Você verá as tabelas `sessions` e `responses`
4. Após fazer o teste, clique em `sessions` para ver seu registro

## 8️⃣ Deploy no Streamlit Cloud

Quando for fazer deploy no Streamlit Cloud:

1. Faça push do código para GitHub (sem o secrets.toml!)
2. No Streamlit Cloud, em **"Advanced settings"** → **"Secrets"**
3. Cole:

```toml
admin_password = "sua_senha_segura"

[supabase]
url = "https://seu-projeto.supabase.co"
key = "sua-anon-key"
```

## 🔧 Troubleshooting

### Erro: "Erro ao conectar ao Supabase"

**Solução:**
- Verifique se o `url` e `key` estão corretos em `secrets.toml`
- Certifique-se de que não há espaços extras
- A URL deve começar com `https://`
- A key é uma string longa (~200 caracteres)

### Erro: "relation does not exist"

**Solução:**
- As tabelas não foram criadas
- Execute o SQL do passo 3 novamente no SQL Editor

### Erro: "new row violates row-level security policy"

**Solução:**
- As políticas RLS não foram criadas corretamente
- Execute novamente as linhas `CREATE POLICY` do SQL

### Erro ao instalar dependências

```bash
# Se tiver problemas com supabase
pip install supabase --upgrade

# Se tiver problemas com outras libs
pip install -r requirements.txt --upgrade
```

## 📊 Visualizar Dados no Supabase

### Via Table Editor:
1. Dashboard do Supabase
2. **"Table Editor"** no menu lateral
3. Selecione `sessions` ou `responses`
4. Você verá todos os dados em formato de tabela

### Via SQL:
1. **"SQL Editor"**
2. Execute queries como:

```sql
-- Ver todas as sessões
SELECT * FROM sessions ORDER BY started_at DESC;

-- Ver todas as respostas
SELECT * FROM responses ORDER BY timestamp DESC;

-- Ver estatísticas
SELECT 
    student_name, 
    final_theta, 
    total_correct,
    total_timeout
FROM sessions 
WHERE status = 'completed';
```

## 🎉 Pronto!

Agora você tem:
- ✅ Banco de dados Supabase configurado
- ✅ Aplicação conectada ao banco
- ✅ Dados persistindo entre sessões
- ✅ Suporte multiusuário funcionando

## 📚 Recursos Úteis

- **Documentação Supabase**: https://supabase.com/docs
- **Dashboard**: https://app.supabase.com
- **Suporte**: https://github.com/supabase/supabase/discussions
