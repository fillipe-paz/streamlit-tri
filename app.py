"""
Calculadora TRI - Teoria de Resposta ao Item
Página principal com entrada de nome do estudante.
"""

import streamlit as st
import json
from modules import database

# Configuração da página
st.set_page_config(
    page_title="Calculadora TRI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #FF4B4B;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #FF4B4B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        border-top: 1px solid #e0e0e0;
        padding: 10px 20px;
        text-align: center;
        font-size: 0.85rem;
        color: #666;
        z-index: 999;
    }
    .footer-dev {
        font-weight: bold;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)


def load_questions():
    """Carrega as questões do arquivo JSON."""
    try:
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Erro ao carregar questões: {e}")
        return None


def main():
    """Função principal da aplicação."""
    
    # Título
    st.markdown('<div class="main-title">📊 Calculadora TRI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Teoria de Resposta ao Item - Demonstração Didática</div>', unsafe_allow_html=True)
    
    # Verificar se já está logado
    if 'student_name' in st.session_state and 'student_id' in st.session_state:
        st.success(f"✅ Bem-vindo(a), **{st.session_state['student_name']}**!")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 Fazer Teste")
            st.markdown("""
            Responda 40 questões de conhecimentos gerais com timer de 45 segundos cada.
            Ao final, você verá:
            - Sua habilidade estimada (θ)
            - Comparação com nota clássica
            - Análise detalhada por questão
            - Gráficos explicativos do TRI
            """)
            
            if st.button("➡️ Iniciar Teste", type="primary", use_container_width=True):
                st.switch_page("pages/1_📝_Fazer_Teste.py")
        
        with col2:
            st.markdown("### 📊 Painel Admin")
            st.markdown("""
            Área restrita para professores visualizarem:
            - Resultados de todos os alunos
            - Estatísticas da turma
            - Análises comparativas
            - Exportação de dados
            """)
            
            if st.button("🔐 Acessar Painel", use_container_width=True):
                st.switch_page("pages/2_📊_Painel_Admin.py")
        
        st.markdown("---")
        
        if st.button("🔄 Trocar de Aluno"):
            # Limpar sessão
            for key in ['student_name', 'student_id', 'current_question', 
                       'responses', 'test_started', 'test_completed']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    else:
        # Formulário de entrada
        st.markdown("### 👤 Identificação do Aluno")
        
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
        **Instruções:**
        1. Digite seu nome completo abaixo
        2. Você terá 40 questões para responder
        3. Cada questão tem 45 segundos de limite
        4. Não é possível voltar depois de confirmar a resposta
        5. Ao final, você verá sua análise TRI completa
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.form("student_form"):
            student_name = st.text_input(
                "Nome Completo",
                placeholder="Digite seu nome completo",
                help="Seu nome será usado para identificar seus resultados"
            )
            
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            if submitted:
                if student_name and len(student_name.strip()) >= 3:
                    # Validar nome
                    student_name = student_name.strip()
                    
                    # Gerar ID único
                    student_id = database.generate_student_id(student_name)
                    
                    # Salvar no session_state
                    st.session_state['student_name'] = student_name
                    st.session_state['student_id'] = student_id
                    
                    # Iniciar sessão no banco
                    success = database.start_session(student_id, student_name)
                    
                    if success:
                        st.success(f"✅ Bem-vindo(a), {student_name}!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao iniciar sessão. Verifique a configuração do banco de dados.")
                else:
                    st.error("⚠️ Por favor, digite um nome válido (mínimo 3 caracteres).")
        
        st.markdown("---")
        
        # Informações sobre TRI
        st.markdown("### 📚 Sobre a Teoria de Resposta ao Item (TRI)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **O que é TRI?**
            
            A Teoria de Resposta ao Item é uma metodologia moderna de avaliação que considera:
            
            - **Discriminação (a)**: Capacidade da questão distinguir alunos
            - **Dificuldade (b)**: Nível de habilidade necessário
            - **Acerto ao Acaso (c)**: Probabilidade de chute
            
            Diferente da nota clássica (% de acertos), o TRI considera a dificuldade e qualidade de cada questão.
            """)
        
        with col2:
            st.markdown("""
            **Como funciona?**
            
            O modelo logístico de 3 parâmetros calcula a probabilidade de acerto:
            
            $$P(\\theta) = c + \\frac{1-c}{1 + e^{-a(\\theta - b)}}$$
            
            Onde:
            - $\\theta$ = Sua habilidade (estimada)
            - $a$ = Discriminação
            - $b$ = Dificuldade
            - $c$ = Chute
            
            Usado no ENEM, vestibulares e avaliações educacionais.
            """)

    # Footer
    st.markdown("""
    <div class="footer">
        <span class="footer-dev">Desenvolvido por:</span> Fillipe Paz<br>
        <span class="footer-dev">Grupo:</span> Letícia Lopes, Fillipe Paz, Weverton Barros, André Silva
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
