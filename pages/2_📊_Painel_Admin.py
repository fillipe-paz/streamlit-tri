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

# CSS para footer
st.markdown("""
<style>
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
    avg_enem = tri_calculator.theta_to_enem_scale(avg_theta) if avg_theta else 500
    
    with col1:
        st.metric("Total de Alunos", total_students)
    
    with col2:
        st.metric("Testes Concluídos", completed_tests)
    
    with col3:
        st.metric("Em Andamento", in_progress)
    
    with col4:
        st.metric("Nota TRI Média (ENEM)", f"{avg_enem:.0f}")
        st.caption(f"θ médio = {avg_theta:.2f}")
    
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
        display_df['Nota TRI (ENEM)'] = display_df['final_theta'].apply(
            lambda x: f"{tri_calculator.theta_to_enem_scale(x):.0f}" if pd.notna(x) and x != '' else '-'
        )
        display_df['θ'] = display_df['final_theta'].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) and x != '' else '-'
        )
    
    if 'total_correct' in display_df.columns:
        # Usar num_questions da sessão, ou fallback para 40 se não existir
        display_df['Acertos'] = display_df.apply(
            lambda row: f"{int(row['total_correct'])}/{int(row.get('num_questions', 40))}" 
            if pd.notna(row['total_correct']) and row['total_correct'] != '' 
            else '-',
            axis=1
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
    columns_to_show = ['student_name', 'Status', 'Nota TRI (ENEM)', 'θ', 'Acertos', 'Timeouts', 'started_at']
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
    
    # Criar lista de opções com nome + ID (para diferenciar alunos com mesmo nome)
    sessions_df['display_name'] = sessions_df['student_name'] + ' (' + sessions_df['student_id'].str[-8:] + ')'
    student_options = sessions_df[['display_name', 'student_id']].to_dict('records')
    
    # Seletor de aluno
    selected_display = st.selectbox(
        "Selecione um aluno:", 
        options=[opt['display_name'] for opt in student_options]
    )
    
    if selected_display:
        # Encontrar student_id correspondente
        student_id = next(opt['student_id'] for opt in student_options if opt['display_name'] == selected_display)
        
        # Obter dados do aluno pelo student_id (único)
        student_session = sessions_df[sessions_df['student_id'] == student_id].iloc[0]
        selected_student = student_session['student_name']
        
        st.markdown(f"### Aluno: {selected_student}")
        st.caption(f"ID: {student_id}")
        
        # Calcular rankings (apenas alunos que completaram)
        completed_sessions = sessions_df[sessions_df['status'] == 'completed'].copy()
        
        theta_rank = None
        classical_rank = None
        total_completed = len(completed_sessions)
        
        if not completed_sessions.empty and pd.notna(student_session['final_theta']):
            # Ranking TRI (maior θ = melhor)
            completed_sessions['theta_rank'] = completed_sessions['final_theta'].rank(ascending=False, method='min')
            theta_rank = int(completed_sessions[completed_sessions['student_id'] == student_id]['theta_rank'].iloc[0])
            
            # Ranking Clássico (mais acertos = melhor)
            completed_sessions['classical_rank'] = completed_sessions['total_correct'].rank(ascending=False, method='min')
            classical_rank = int(completed_sessions[completed_sessions['student_id'] == student_id]['classical_rank'].iloc[0])
        
        # Converter theta para ENEM
        theta = student_session['final_theta']
        enem_score = tri_calculator.theta_to_enem_scale(theta) if pd.notna(theta) and theta != '' else None
        
        # Calcular TCT score
        all_responses_global = database.get_all_responses()
        
        # Obter número total de questões da sessão específica
        # Usa o valor salvo na sessão, senão busca do banco (backward compatibility)
        if 'num_questions' in student_session.index and pd.notna(student_session['num_questions']):
            total_questions = int(student_session['num_questions'])
        else:
            total_questions = database.get_num_questions()  # Fallback para testes antigos
        
        # Usar apenas as questões que estavam disponíveis naquela sessão
        questions_list = questions[:total_questions]
        
        item_difficulties = []
        for question in questions_list:
            q_responses = all_responses_global[all_responses_global['question_id'] == question['id']]
            if not q_responses.empty and len(q_responses) > 0:
                difficulty = q_responses['is_correct'].mean()
            else:
                difficulty = 0.5
            item_difficulties.append(difficulty)
        
        # Get student responses
        student_responses_df = responses_df[responses_df['student_id'] == student_id]
        if not student_responses_df.empty:
            responses_list = []
            for question in questions_list:
                q_resp = student_responses_df[student_responses_df['question_id'] == question['id']]
                if not q_resp.empty:
                    responses_list.append(q_resp.iloc[0]['is_correct'])
                else:
                    responses_list.append(False)
            
            weighted_score = tri_calculator.calculate_weighted_score(responses_list, item_difficulties)
        else:
            weighted_score = 0.0
        
        # Métricas do aluno
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if enem_score:
                theta_delta = f"{theta_rank}º/{total_completed}" if theta_rank else None
                st.metric("Nota TRI (ENEM)", f"{enem_score:.0f}", delta=theta_delta, delta_color="off")
                st.caption(f"θ = {theta:.2f}")
            else:
                st.metric("Nota TRI (ENEM)", "-")
        
        with col2:
            st.metric("Nota Ponderada", f"{weighted_score:.1f}%")
        
        with col3:
            correct = student_session['total_correct']
            correct_display = f"{int(correct)}/{total_questions}" if pd.notna(correct) and correct != '' else '-'
            st.metric("Acertos", correct_display)
        
        with col4:
            if pd.notna(correct) and correct != '':
                classical = (float(correct) / total_questions) * 100
                classical_delta = f"{classical_rank}º/{total_completed}" if classical_rank else None
                st.metric("Nota Bruta", f"{classical:.1f}%", delta=classical_delta, delta_color="off")
            else:
                st.metric("Nota Bruta", "-")
        
        with col5:
            timeout = student_session['total_timeout']
            timeout_display = int(timeout) if pd.notna(timeout) and timeout != '' else 0
            st.metric("Timeouts", timeout_display)
        
        # Classificação
        if pd.notna(theta) and theta != '':
            category, description = tri_calculator.classify_ability(float(theta))
            st.info(f"**Classificação:** {category} - {description}")
            
            # Mostrar escala ENEM
            st.markdown("#### 📊 Escala ENEM")
            
            # Criar barra visual da escala
            progress_html = f"""
            <div style="margin: 1rem 0;">
                <div style="background: linear-gradient(to right, 
                    #dc3545 0%, #dc3545 35%, 
                    #ffc107 35%, #ffc107 45%,
                    #17a2b8 45%, #17a2b8 55%,
                    #28a745 55%, #28a745 65%,
                    #20c997 65%, #20c997 75%,
                    #6f42c1 75%, #6f42c1 100%);
                    height: 30px; 
                    border-radius: 5px; 
                    position: relative;">
                    <div style="position: absolute; 
                        left: {(enem_score / 10)}%; 
                        top: -5px; 
                        transform: translateX(-50%);
                        font-size: 2rem;">
                        ⬇️
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.8rem;">
                    <span>0</span>
                    <span>350</span>
                    <span>450</span>
                    <span>550</span>
                    <span>650</span>
                    <span>750</span>
                    <span>1000</span>
                </div>
            </div>
            """
            st.markdown(progress_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Obter respostas do aluno
        student_responses_df = responses_df[responses_df['student_id'] == student_id]
        
        if not student_responses_df.empty:
            # Tabs para diferentes visualizações
            tab1, tab2, tab3 = st.tabs(["📋 Respostas Detalhadas", "📈 Evolução do θ", "📄 Sumário Final"])
            
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
            
            with tab3:
                st.markdown("#### 📊 Sumário Completo do Teste")
                st.markdown("""
                Este sumário mostra uma análise detalhada questão por questão, incluindo 
                os parâmetros TRI de cada item e a probabilidade esperada de acerto.
                """)
                
                # Criar tabela com detalhes completos
                details = []
                
                # Ordenar respostas pela ordem das questões
                for question in questions_list:
                    q_resp = student_responses_df[student_responses_df['question_id'] == question['id']]
                    
                    if not q_resp.empty:
                        q_resp_data = q_resp.iloc[0]
                        item = question['tri_parameters']
                        theta_at_time = q_resp_data['theta_estimate']
                        
                        # Calcular probabilidade esperada
                        prob_expected = tri_calculator.probability_3pl(
                            theta_at_time, item['a'], item['b'], item['c']
                        ) if pd.notna(theta_at_time) else None
                        
                        # Determinar resultado
                        if q_resp_data['is_timeout']:
                            resultado = '⏰'
                        elif q_resp_data['is_correct']:
                            resultado = '✅'
                        else:
                            resultado = '❌'
                        
                        details.append({
                            'Questão': question['id'],
                            'Área': question['subject'],
                            'Dificuldade (b)': f"{item['b']:.2f}",
                            'Discriminação (a)': f"{item['a']:.2f}",
                            'Prob. Esperada': f"{prob_expected:.1%}" if prob_expected else '-',
                            'Resultado': resultado,
                            'θ após questão': f"{theta_at_time:.2f}" if pd.notna(theta_at_time) else '-'
                        })
                
                if details:
                    st.dataframe(details, use_container_width=True, hide_index=True)
                    
                    st.markdown("""
                    **Legenda:**
                    - ✅ Acertou
                    - ❌ Errou
                    - ⏰ Timeout (tempo esgotado)
                    - **Prob. Esperada:** Probabilidade de acerto baseada no θ do aluno no momento da questão
                    - **θ após questão:** Habilidade estimada após responder essa questão
                    """)
                else:
                    st.info("Nenhuma resposta registrada.")
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
    
    # Tabs para diferentes visualizações
    tab1, tab2 = st.tabs(["📊 Tabela de Estatísticas", "📈 Curvas Características"])
    
    with tab1:
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
    
    with tab2:
        st.markdown("### 📈 Curvas Características dos Itens (CCI)")
        st.info("Selecione uma questão para visualizar sua Curva Característica.")
        
        # Dropdown para selecionar questão
        question_options = {f"{q['id']} - {q['subject']}": q for q in questions}
        selected_option = st.selectbox(
            "Escolha uma questão:",
            options=list(question_options.keys()),
            key="admin_cci_selector"
        )
        
        if selected_option:
            question = question_options[selected_option]
            
            # Mostrar informações da questão
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**{question['question']}**")
                
                # Mostrar opções
                st.markdown("**Alternativas:**")
                for opt in question['options']:
                    icon = "✅" if opt['id'] == question['correct_answer'] else "▪️"
                    st.markdown(f"{icon} **{opt['id']})** {opt['text']}")
            
            with col2:
                st.markdown("**Parâmetros TRI:**")
                params = question['tri_parameters']
                st.metric("Discriminação (a)", f"{params['a']:.2f}")
                st.metric("Dificuldade (b)", f"{params['b']:.2f}")
                st.metric("Acerto ao acaso (c)", f"{params['c']:.2f}")
            
            st.markdown("---")
            
            # Plotar CCI
            item_plot = {
                'id': question['id'],
                'a': params['a'],
                'b': params['b'],
                'c': params['c']
            }
            
            fig = tri_calculator.plot_icc(item_plot)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            **Como interpretar a curva:**
            - **Eixo X (θ):** Habilidade do aluno
            - **Eixo Y:** Probabilidade de acerto
            - **Linha vermelha (b):** Ponto de dificuldade (50% de chance de acerto)
            - **Linha verde (c):** Probabilidade mínima de acerto (chute)
            - **Inclinação:** Quanto mais inclinada, maior a discriminação (parâmetro a)
            """)
            
            # Estatísticas dessa questão
            if not responses_df.empty:
                q_responses = responses_df[responses_df['question_id'] == question['id']]
                
                if not q_responses.empty:
                    st.markdown("---")
                    st.markdown("#### 📊 Desempenho dos Alunos nesta Questão")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    total = len(q_responses)
                    correct = q_responses['is_correct'].sum()
                    timeout = q_responses['is_timeout'].sum()
                    
                    with col1:
                        st.metric("Total de Respostas", total)
                    with col2:
                        st.metric("Acertos", f"{correct} ({correct/total*100:.1f}%)")
                    with col3:
                        st.metric("Timeouts", f"{timeout} ({timeout/total*100:.1f}%)")


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


def manage_exam_settings():
    """
    Gerencia configurações da prova (horário de início e fim).
    """
    st.markdown("## ⚙️ Configurações da Prova")
    
    # ===== CONFIGURAÇÃO: NÚMERO DE QUESTÕES =====
    st.markdown("### 📝 Número de Questões")
    
    current_num_questions = database.get_num_questions()
    
    col_num1, col_num2 = st.columns([2, 1])
    
    with col_num1:
        st.info(f"📌 Atualmente o teste tem **{current_num_questions} questões**. O banco possui 40 questões cadastradas.")
    
    with col_num2:
        new_num = st.number_input(
            "Definir número de questões",
            min_value=1,
            max_value=40,
            value=current_num_questions,
            step=1,
            key="num_questions_input"
        )
        
        if st.button("💾 Salvar", type="primary", use_container_width=True, key="save_num_questions"):
            if database.set_num_questions(new_num):
                st.success(f"✅ Número de questões atualizado para {new_num}!")
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🕐 Janela de Tempo da Avaliação")
    st.info("📌 Defina o horário de início e fim da prova. **Todos os horários são em Horário de Brasília (UTC-3)**")
    
    from datetime import datetime, timezone, timedelta
    
    # Usar timezone de Brasília
    brasilia_tz = timezone(timedelta(hours=-3))
    
    # Obter configurações atuais
    current_start = database.get_exam_start()
    current_deadline = database.get_exam_deadline()
    
    # Duas colunas: início e fim
    col_start, col_fim = st.columns(2)
    
    # ===== COLUNA: HORÁRIO DE INÍCIO =====
    with col_start:
        st.markdown("#### 🟢 Horário de Início")
        
        if current_start:
            st.success(f"✅ Início definido:\n\n**{current_start.strftime('%d/%m/%Y às %H:%M')}**\n\n(Horário de Brasília)")
        else:
            st.warning("⚠️ Sem horário de início\n\n(Alunos podem começar a qualquer momento)")
        
        if current_start:
            if st.button("🗑️ Remover Início", use_container_width=True, key="remove_start"):
                if database.set_exam_start(None):
                    st.success("Horário de início removido!")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("**Definir Horário de Início**")
        
        start_date = st.date_input(
            "Data de Início",
            value=current_start.date() if current_start else None,
            key="start_date"
        )
        
        start_time = st.time_input(
            "Hora de Início",
            value=current_start.time() if current_start else None,
            key="start_time"
        )
        
        if st.button("💾 Salvar Início", type="primary", use_container_width=True, key="save_start"):
            if start_date and start_time:
                # Combinar data e hora
                start_datetime = datetime.combine(start_date, start_time)
                # Adicionar timezone (UTC-3 - Horário de Brasília)
                start_datetime = start_datetime.replace(tzinfo=brasilia_tz)
                
                if database.set_exam_start(start_datetime):
                    st.success(f"✅ Início definido para {start_datetime.strftime('%d/%m/%Y às %H:%M')} (Horário de Brasília)")
                    st.rerun()
            else:
                st.error("Por favor, preencha data e horário")
    
    # ===== COLUNA: HORÁRIO DE FIM =====
    with col_fim:
        st.markdown("#### 🔴 Horário de Fim (Deadline)")
        
        if current_deadline:
            st.success(f"✅ Fim definido:\n\n**{current_deadline.strftime('%d/%m/%Y às %H:%M')}**\n\n(Horário de Brasília)")
        else:
            st.warning("⚠️ Sem horário de fim\n\n(Prova sem limite de tempo)")
        
        if current_deadline:
            if st.button("🗑️ Remover Fim", use_container_width=True, key="remove_deadline"):
                if database.set_exam_deadline(None):
                    st.success("Horário de fim removido!")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("**Definir Horário de Fim**")
        
        deadline_date = st.date_input(
            "Data de Fim",
            value=current_deadline.date() if current_deadline else None,
            key="deadline_date"
        )
        
        deadline_time = st.time_input(
            "Hora de Fim",
            value=current_deadline.time() if current_deadline else None,
            key="deadline_time"
        )
        
        if st.button("💾 Salvar Fim", type="primary", use_container_width=True, key="save_deadline"):
            if deadline_date and deadline_time:
                # Combinar data e hora
                deadline_datetime = datetime.combine(deadline_date, deadline_time)
                # Adicionar timezone (UTC-3 - Horário de Brasília)
                deadline_datetime = deadline_datetime.replace(tzinfo=brasilia_tz)
                
                if database.set_exam_deadline(deadline_datetime):
                    st.success(f"✅ Fim definido para {deadline_datetime.strftime('%d/%m/%Y às %H:%M')} (Horário de Brasília)")
                    st.rerun()
            else:
                st.error("Por favor, preencha data e horário")



def main():
    """Função principal do painel administrativo."""
    
    # Logo da instituição
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.image("https://portal.cin.ufpe.br/wp-content/uploads/2025/08/HC.png", use_container_width=True)
    
    st.markdown("---")
    
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Visão Geral",
        "👥 Lista de Alunos",
        "🔍 Análise Individual",
        "📝 Estatísticas por Questão",
        "⚙️ Configurações",
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
        manage_exam_settings()
    
    with tab6:
        export_data(sessions_df, responses_df)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <span class="footer-dev">Grupo:</span> Letícia Lopes, Fillipe Paz, Weverton Barros, André Silva<br>
        <span class="footer-dev">Desenvolvido por:</span> Fillipe Paz
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
