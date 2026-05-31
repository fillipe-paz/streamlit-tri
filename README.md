# 📊 Calculadora TRI - Teoria de Resposta ao Item

Aplicação Streamlit para demonstração didática de cálculos TRI (Teoria de Resposta ao Item) com questões de conhecimentos gerais em português.

## 🎯 Funcionalidades

- ✅ **Teste Multiusuário**: Múltiplos alunos acessam simultaneamente
- ⏱️ **Timer por Questão**: 45 segundos por questão com feedback visual
- 📝 **30-40 Questões**: Conhecimentos gerais (História, Geografia, Ciências, Cultura)
- 📊 **Cálculo TRI**: Modelo logístico de 3 parâmetros com estimação de habilidade (θ)
- 👨‍🏫 **Painel Admin**: Dashboard para professores visualizarem resultados de todos os alunos
- 💾 **Armazenamento Centralizado**: Respostas salvas em Supabase (PostgreSQL)

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

### 1. Criar Projeto no Supabase

1. Acesse [Supabase](https://supabase.com)
2. Crie uma conta e um novo projeto
3. No SQL Editor, execute o script para criar as tabelas (veja [SETUP_SUPABASE.md](SETUP_SUPABASE.md))

### 2. Obter Credenciais

1. No dashboard do Supabase, vá em **Settings** → **API**
2. Copie:
   - **Project URL**: `https://xxxx.supabase.co`
   - **anon public key**: `eyJ...`

### 3. Configurar Secrets no Streamlit Cloud

No Streamlit Cloud, adicione os seguintes secrets:

```toml
# Senha do painel administrativo
admin_password = "sua_senha_aqui"

# Credenciais do Supabase
[supabase]
url = "https://seu-projeto.supabase.co"
key = "sua-anon-key-aqui"
```

### 4. Deploy

1. Faça push do código para GitHub
2. Conecte o repositório no [Streamlit Cloud](https://streamlit.io/cloud)
3. Configure os secrets
4. Deploy!

📖 **Guia completo de configuração**: Veja [SETUP_SUPABASE.md](SETUP_SUPABASE.md)

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

# Configurar Supabase (veja SETUP_SUPABASE.md)
# Criar arquivo .streamlit/secrets.toml com credenciais

# Executar aplicação
streamlit run app.py
```

📖 **Guia detalhado**: [SETUP_SUPABASE.md](SETUP_SUPABASE.md)

## 📄 Licença

MIT License - Uso educacional livre
