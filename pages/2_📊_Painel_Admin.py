"""
Painel Administrativo para visualização de resultados.
"""

import streamlit as st
import pandas as pd
import json
from modules import database, tri_calculator

# Configuração da página
st.set_page_config(
    page_title="Painel Admin - TRI",
    page_icon="📊",
    layout="wide"
)


def load_questions():
    """Carrega as questões do arquivo JSON."""
    try:
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['questions']
    except Exception as e:
        st.error(f"Erro ao carregar questões: {e}")
        return None


def authenticate():
    """Verifica autenticação do administrador."""
    if 'admin_authenticated' not in st.session_state:
        st.session_state['admin_authenticated'] = False
    
    if not st.session_state['admin_authenticated']:
        st.markdown("# 🔐 Acesso Administrativo")
        st.markdown("---")
        
        with st.form("admin_login"):
            password = st.text_input(
                "Senha de Administrador",
                type="password",
                help="Digite a senha configurada nos secrets"
            )
            
            submitted = st.form_submit_button("Entrar", type="primary")
            
            if submitted:
                try:
                    correct_password = st.secrets["admin_password"]
                    if password == correct_password:
                        st.session_state['admin_authenticated'] = True
                        st.success("✅ Autenticado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta!")
                except Exception as e:
                    st.error(f"Erro ao verificar senha: {e}")
                    st.info("💡 Certifique-se de configurar 'admin_password' no arquivo secrets.toml")
        
        return False
    
    return True


def display_overview(sessions_df, responses_df):
    """
    Exibe visão geral das estatísticas.
    
    Args:
        sessions_df: DataFrame com sessões
        responses_df: DataFrame com respostas
    """
    st.markdown("## 📊 Visão Geral")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_students = len(sessions_df) if not sessions_df.empty else 0
    completed_tests = len(sessions_df[sessions_df['status'] == 'completed']) if not sessions_df.empty else 0
    in_progress = len(sessions_df[sessions_df['status'] == 'in_progress']) if not sessions_df.empty else 0
    avg_theta = sessions_df[sessions_df['status'] == 'completed']['final_theta'].mean() if not sessions_df.empty else 0
    
    with col1:
        st.metric("Total de Alunos", total_students)
    
    with col2:
        st.metric("Testes Concluídos", completed_tests)
    
    with col3:
        st.metric("Em Andamento", in_progress)
    
    with col4:
        st.metric("θ Médio da Turma", f"{avg_theta:.2f}")
    
    st.markdown("---")
    
    # Gráficos
    if not sessions_df.empty and completed_tests > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Distribuição de Habilidades (θ)")
            completed_sessions = sessions_df[sessions_df['status'] == 'completed']
            thetas = completed_sessions['final_theta'].tolist()
            
            fig = tri_calculator.plot_theta_distribution(thetas)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Taxa de Acerto por Aluno")
            
            if not completed_sessions.empty:
                # Calcular taxa de acerto
                completed_sessions['taxa_acerto'] = (
                    completed_sessions['total_correct'] / 40 * 100
                ).round(1)
                
                chart_data = completed_sessions[['student_name', 'taxa_acerto']].copy()
                chart_data = chart_data.sort_values('taxa_acerto', ascending=True)
                
                st.bar_chart(chart_data.set_index('student_name')['taxa_acerto'])
    else:
        st.info("ℹ️ Nenhum teste concluído ainda. Os gráficos aparecerão quando houver dados.")


def display_students_list(sessions_df):
    """
    Exibe lista de alunos com seus resultados.
    
    Args:
        sessions_df: DataFrame com sessões
    """
    st.markdown("## 👥 Lista de Alunos")
    
    if sessions_df.empty:
        st.info("ℹ️ Nenhum aluno iniciou o teste ainda.")
        return
    
    # Preparar dados para exibição
    display_df = sessions_df.copy()
    
    # Formatar colunas
    if 'final_theta' in display_df.columns:
        display_df['θ Final'] = display_df['final_theta'].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) and x != '' else '-'
        )
    
    if 'total_correct' in display_df.columns:
        display_df['Acertos'] = display_df['total_correct'].apply(
            lambda x: f"{int(x)}/40" if pd.notna(x) and x != '' else '-'
        )
    
    if 'total_timeout' in display_df.columns:
        display_df['Timeouts'] = display_df['total_timeout'].apply(
            lambda x: int(x) if pd.notna(x) and x != '' else 0
        )
    
    # Status com emoji
    status_map = {
        'completed': '✅ Concluído',
        'in_progress': '🔄 Em andamento'
    }
    display_df['Status'] = display_df['status'].map(status_map)
    
    # Selecionar colunas para exibir
    columns_to_show = ['student_name', 'Status', 'θ Final', 'Acertos', 'Timeouts', 'started_at']
    columns_rename = {
        'student_name': 'Nome do Aluno',
        'started_at': 'Início'
    }
    
    display_df = display_df[columns_to_show].rename(columns=columns_rename)
    
    # Exibir tabela
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def display_individual_analysis(sessions_df, responses_df, questions):
    """
    Exibe análise individual de um aluno selecionado.
    
    Args:
        sessions_df: DataFrame com sessões
        responses_df: DataFrame com respostas
        questions: Lista de questões
    """
    st.markdown("## 🔍 Análise Individual")
    
    if sessions_df.empty:
        st.info("ℹ️ Nenhum aluno para analisar.")
        return
    
    # Seletor de aluno
    student_names = sessions_df['student_name'].unique().tolist()
    selected_student = st.selectbox("Selecione um aluno:", student_names)
    
    if selected_student:
        # Obter dados do aluno
        student_session = sessions_df[sessions_df['student_name'] == selected_student].iloc[0]
        student_id = student_session['student_id']
        
        st.markdown(f"### Aluno: {selected_student}")
        
        # Métricas do aluno
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            theta = student_session['final_theta']
            theta_display = f"{theta:.2f}" if pd.notna(theta) and theta != '' else '-'
            st.metric("θ Final", theta_display)
        
        with col2:
            correct = student_session['total_correct']
            correct_display = f"{int(correct)}/40" if pd.notna(correct) and correct != '' else '-'
            st.metric("Acertos", correct_display)
        
        with col3:
            timeout = student_session['total_timeout']
            timeout_display = int(timeout) if pd.notna(timeout) and timeout != '' else 0
            st.metric("Timeouts", timeout_display)
        
        with col4:
            if pd.notna(correct) and correct != '':
                classical = (float(correct) / 40) * 100
                st.metric("Nota Clássica", f"{classical:.1f}%")
            else:
                st.metric("Nota Clássica", "-")
        
        # Classificação
        if pd.notna(theta) and theta != '':
            category, description = tri_calculator.classify_ability(float(theta))
            st.info(f"**Classificação:** {category} - {description}")
        
        st.markdown("---")
        
        # Obter respostas do aluno
        student_responses_df = responses_df[responses_df['student_id'] == student_id]
        
        if not student_responses_df.empty:
            # Tabs para diferentes visualizações
            tab1, tab2 = st.tabs(["📋 Respostas Detalhadas", "📈 Evolução do θ"])
            
            with tab1:
                st.markdown("#### Análise por Questão")
                
                # Criar tabela detalhada
                details = []
                
                for _, row in student_responses_df.iterrows():
                    # Encontrar questão correspondente
                    question = next((q for q in questions if q['id'] == row['question_id']), None)
                    
                    if question:
                        resultado = '✅ Acertou'
                        if row['is_timeout']:
                            resultado = '⏰ Timeout'
                        elif not row['is_correct']:
                            resultado = '❌ Errou'
                        
                        details.append({
                            'Questão': row['question_id'],
                            'Área': question['subject'],
                            'Dificuldade (b)': f"{question['tri_parameters']['b']:.2f}",
                            'Resultado': resultado,
                            'θ após questão': f"{row['theta_estimate']:.2f}" if pd.notna(row['theta_estimate']) else '-'
                        })
                
                details_df = pd.DataFrame(details)
                st.dataframe(details_df, use_container_width=True, hide_index=True)
            
            with tab2:
                st.markdown("#### Evolução da Habilidade")
                
                theta_estimates = student_responses_df['theta_estimate'].dropna().tolist()
                
                if theta_estimates:
                    fig = tri_calculator.plot_theta_progression(theta_estimates)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Dados de theta não disponíveis.")
        else:
            st.info("Nenhuma resposta registrada para este aluno.")


def display_question_statistics(responses_df, questions):
    """
    Exibe estatísticas por questão.
    
    Args:
        responses_df: DataFrame com respostas
        questions: Lista de questões
    """
    st.markdown("## 📝 Estatísticas por Questão")
    
    if responses_df.empty:
        st.info("ℹ️ Nenhuma resposta registrada ainda.")
        return
    
    # Calcular estatísticas
    stats = []
    
    for question in questions:
        q_id = question['id']
        q_responses = responses_df[responses_df['question_id'] == q_id]
        
        if not q_responses.empty:
            total = len(q_responses)
            correct = q_responses['is_correct'].sum()
            timeout = q_responses['is_timeout'].sum()
            
            correct_rate = (correct / total) * 100 if total > 0 else 0
            timeout_rate = (timeout / total) * 100 if total > 0 else 0
            
            stats.append({
                'Questão': q_id,
                'Área': question['subject'],
                'Dificuldade TRI (b)': f"{question['tri_parameters']['b']:.2f}",
                'Total Respostas': total,
                'Taxa de Acerto': f"{correct_rate:.1f}%",
                'Taxa de Timeout': f"{timeout_rate:.1f}%"
            })
    
    if stats:
        stats_df = pd.DataFrame(stats)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        # Gráfico de taxa de acerto
        st.markdown("### Taxa de Acerto por Questão")
        
        chart_df = stats_df[['Questão', 'Taxa de Acerto']].copy()
        chart_df['Taxa de Acerto'] = chart_df['Taxa de Acerto'].str.rstrip('%').astype(float)
        
        st.bar_chart(chart_df.set_index('Questão')['Taxa de Acerto'])
    else:
        st.info("Nenhuma estatística disponível ainda.")


def export_data(sessions_df, responses_df):
    """
    Permite exportar dados em CSV.
    
    Args:
        sessions_df: DataFrame com sessões
        responses_df: DataFrame com respostas
    """
    st.markdown("## 📥 Exportar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Sessões dos Alunos")
        if not sessions_df.empty:
            csv_sessions = sessions_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Baixar Sessões (CSV)",
                data=csv_sessions,
                file_name="tri_sessoes.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Sem dados para exportar")
    
    with col2:
        st.markdown("### Respostas Detalhadas")
        if not responses_df.empty:
            csv_responses = responses_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Baixar Respostas (CSV)",
                data=csv_responses,
                file_name="tri_respostas.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Sem dados para exportar")


def main():
    """Função principal do painel administrativo."""
    
    st.markdown("# 📊 Painel Administrativo")
    
    # Verificar autenticação
    if not authenticate():
        return
    
    # Botão de logout no sidebar
    with st.sidebar:
        st.markdown("### 🔐 Admin")
        if st.button("🚪 Fazer Logout"):
            st.session_state['admin_authenticated'] = False
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        sessions_df = database.get_all_sessions()
        responses_df = database.get_all_responses()
        questions = load_questions()
    
    if questions is None:
        st.error("Erro ao carregar questões!")
        return
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral",
        "👥 Lista de Alunos",
        "🔍 Análise Individual",
        "📝 Estatísticas por Questão",
        "📥 Exportar Dados"
    ])
    
    with tab1:
        display_overview(sessions_df, responses_df)
    
    with tab2:
        display_students_list(sessions_df)
    
    with tab3:
        display_individual_analysis(sessions_df, responses_df, questions)
    
    with tab4:
        display_question_statistics(responses_df, questions)
    
    with tab5:
        export_data(sessions_df, responses_df)


if __name__ == "__main__":
    main()
