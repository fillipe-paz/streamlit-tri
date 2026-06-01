"""
Página de realização do teste com timer e questões.
"""

import streamlit as st
import json
import time
from streamlit_autorefresh import st_autorefresh
from modules import database, tri_calculator, timer as timer_module

# Configuração da página
st.set_page_config(
    page_title="Fazer Teste - TRI",
    page_icon="📝",
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
    """Carrega as questões do arquivo JSON e limita ao número configurado."""
    try:
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Obter número de questões configurado no banco
        num_questions = database.get_num_questions()
        
        # Limitar questões ao número configurado
        all_questions = data['questions']
        questions = all_questions[:num_questions]  # Pegar as primeiras N questões
        
        return questions, data['time_per_question'], data.get('total_exam_time_minutes', 60)
    except Exception as e:
        st.error(f"Erro ao carregar questões: {e}")
        return None, None, None


def initialize_test(total_exam_time_minutes):
    """Inicializa o teste no session_state."""
    if 'test_started' not in st.session_state:
        st.session_state['test_started'] = True
        st.session_state['current_question'] = 0
        st.session_state['responses'] = {}  # Mudado para dict: {question_id: answer}
        st.session_state['items_data'] = []
        st.session_state['theta_estimates'] = []
        st.session_state['test_completed'] = False
        # Não usamos mais exam_start_time individual - usamos deadline global do banco


def save_response(question, answer, is_timeout=False):
    """
    Salva a resposta (permite alterar respostas já dadas).
    
    Args:
        question: Dicionário com dados da questão
        answer: Resposta do aluno (None se timeout)
        is_timeout: Se houve timeout
    """
    # Salvar resposta no dict
    st.session_state['responses'][question['id']] = {
        'answer': answer,
        'is_timeout': is_timeout,
        'correct_answer': question['correct_answer']
    }

def calculate_all_theta_and_save():
    """
    Calcula theta com todas as respostas e salva no banco.
    Chamado ao finalizar o teste.
    """
    questions, _, _ = load_questions()
    if not questions:
        return
    
    # Preparar listas de respostas na ordem das questões
    responses_list = []
    items_list = []
    
    for question in questions:
        if question['id'] in st.session_state['responses']:
            response_data = st.session_state['responses'][question['id']]
            is_correct = (response_data['answer'] == response_data['correct_answer']) if response_data['answer'] else False
            responses_list.append(is_correct)
            items_list.append(question['tri_parameters'])
    
    # Calcular theta progressivo
    theta_estimates = []
    for i in range(1, len(responses_list) + 1):
        theta = tri_calculator.estimate_theta_progressive(
            responses_list[:i],
            items_list[:i]
        )
        theta_estimates.append(theta)
    
    st.session_state['items_data'] = items_list
    st.session_state['theta_estimates'] = theta_estimates
    st.session_state['responses_list'] = responses_list
    
    # Salvar todas as respostas no banco
    for idx, question in enumerate(questions):
        if question['id'] in st.session_state['responses']:
            response_data = st.session_state['responses'][question['id']]
            is_correct = responses_list[idx]
            theta = theta_estimates[idx]
            
            database.save_response(
                student_id=st.session_state['student_id'],
                student_name=st.session_state['student_name'],
                question_id=question['id'],
                answer=response_data['answer'],
                is_correct=is_correct,
                is_timeout=response_data['is_timeout'],
                theta_estimate=theta
            )


def display_global_timer():
    """Exibe o timer global da prova baseado no deadline do banco."""
    # Obter deadline do banco
    deadline = database.get_exam_deadline()
    
    if not deadline:
        # Sem deadline definido
        return None
    
    # Calcular tempo restante
    from datetime import datetime, timezone, timedelta
    # Usar horário de Brasília (UTC-3)
    brasilia_tz = timezone(timedelta(hours=-3))
    now = datetime.now(brasilia_tz)
    
    if now >= deadline:
        # Tempo esgotado
        return 0
    
    remaining_seconds = int((deadline - now).total_seconds())
    
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    
    # Determinar cor baseado no tempo restante
    if remaining_seconds > 600:  # Mais de 10 minutos
        color = "#28a745"  # Verde
        bg_color = "#f8f9fa"
    elif remaining_seconds > 300:  # Mais de 5 minutos
        color = "#ffc107"  # Amarelo
        bg_color = "#fff3cd"
    else:  # Menos de 5 minutos
        color = "#dc3545"  # Vermelho
        bg_color = "#f8d7da"
    
    timer_html = f"""
    <div style="
        position: fixed;
        top: 60px;
        right: 20px;
        z-index: 999;
        padding: 1rem;
        background-color: {bg_color};
        border: 3px solid {color};
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="text-align: center; font-size: 0.8rem; color: #6c757d; margin-bottom: 0.3rem;">
            ⏱️ Tempo restante da prova
        </div>
        <div style="
            font-size: 1.8rem;
            font-weight: bold;
            color: {color};
            text-align: center;
        ">
            {minutes:02d}:{seconds:02d}
        </div>
    </div>
    """
    
    st.markdown(timer_html, unsafe_allow_html=True)
    return remaining_seconds


def display_question(question, question_num, total_questions, questions):
    """
    Exibe uma questão com navegação.
    
    Args:
        question: Dicionário com dados da questão
        question_num: Número da questão atual (1-indexed)
        total_questions: Total de questões
        questions: Lista completa de questões
    """
    # Barra de progresso
    timer_module.display_progress_bar(question_num, total_questions)
    
    st.markdown("---")
    
    # Exibir questão
    st.markdown(f"### Questão {question_num} de {total_questions}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Área:** {question['subject']}")
    
    st.markdown("---")
    
    st.markdown(f"**{question['question']}**")
    
    st.markdown("")
    
    # Obter resposta já selecionada (se houver)
    current_response = st.session_state['responses'].get(question['id'])
    selected_answer = current_response['answer'] if current_response else None
    
    # Opções de resposta usando radio button para permitir mudança
    options_text = [f"{opt['id']}) {opt['text']}" for opt in question['options']]
    options_ids = [opt['id'] for opt in question['options']]
    
    # Index da resposta selecionada
    default_index = options_ids.index(selected_answer) if selected_answer in options_ids else None
    
    answer = st.radio(
        "Selecione sua resposta:",
        options=options_ids,
        format_func=lambda x: next(opt['text'] for opt in question['options'] if opt['id'] == x),
        index=default_index,
        key=f"radio_{question['id']}"
    )
    
    # Salvar resposta automaticamente quando selecionada
    if answer:
        save_response(question, answer, False)
    
    st.markdown("---")
    
    # Botões de navegação
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if question_num > 1:
            if st.button("⬅️ Anterior", use_container_width=True):
                st.session_state['current_question'] -= 1
                st.rerun()
    
    with col2:
        # Mostrar quantas questões foram respondidas
        answered = len(st.session_state['responses'])
        st.info(f"📝 {answered}/{total_questions} respondidas")
    
    with col3:
        if question_num < total_questions:
            if st.button("Próxima ➡️", use_container_width=True, type="primary"):
                st.session_state['current_question'] += 1
                st.rerun()
        else:
            if st.button("✅ Finalizar Prova", use_container_width=True, type="primary"):
                st.session_state['current_question'] = total_questions
                st.rerun()


def display_results(questions):
    """
    Exibe os resultados finais do teste.
    
    Args:
        questions: Lista de questões
    """
    # Calcular e salvar tudo se ainda não foi feito
    if 'responses_list' not in st.session_state:
        calculate_all_theta_and_save()
    
    st.markdown("# 🎉 Teste Concluído!")
    
    st.markdown("---")
    
    # Buscar respostas do aluno do banco de dados
    student_responses = database.get_student_responses(st.session_state.get('student_id', ''))
    
    # Calcular estatísticas
    responses_list = st.session_state.get('responses_list', [])
    final_theta = st.session_state['theta_estimates'][-1] if st.session_state.get('theta_estimates') else 0.0
    total_correct = sum(responses_list)
    total_questions = len(questions)
    answered_questions = len(st.session_state['responses'])
    classical_score = (total_correct / total_questions) * 100 if total_questions > 0 else 0
    
    # Calcular TCT score
    # Obter taxa de acerto de cada questão
    all_responses = database.get_all_responses()
    item_difficulties = []
    
    for question in questions:
        q_responses = all_responses[all_responses['question_id'] == question['id']]
        if not q_responses.empty and len(q_responses) > 0:
            difficulty = q_responses['is_correct'].mean()  # Taxa de acerto
        else:
            difficulty = 0.5  # Default se não há dados
        item_difficulties.append(difficulty)
    
    weighted_score = tri_calculator.calculate_weighted_score(responses_list, item_difficulties)
    
    # Contar timeouts (questões não respondidas)
    total_timeout = total_questions - answered_questions
    
    # Salvar sessão completa
    database.complete_session(
        student_id=st.session_state['student_id'],
        final_theta=final_theta,
        total_correct=int(total_correct),
        total_timeout=int(total_timeout)
    )
    
    # Calcular ranking comparado aos demais
    all_sessions = database.get_all_sessions()
    completed_sessions = all_sessions[all_sessions['status'] == 'completed'].copy()
    
    theta_rank = None
    classical_rank = None
    total_completed = len(completed_sessions)
    
    if not completed_sessions.empty:
        # Ranking TRI (maior θ = melhor)
        completed_sessions['theta_rank'] = completed_sessions['final_theta'].rank(ascending=False, method='min')
        student_data = completed_sessions[completed_sessions['student_id'] == st.session_state['student_id']]
        if not student_data.empty:
            theta_rank = int(student_data['theta_rank'].iloc[0])
        
        # Ranking Clássico (mais acertos = melhor)
        completed_sessions['classical_rank'] = completed_sessions['total_correct'].rank(ascending=False, method='min')
        student_data = completed_sessions[completed_sessions['student_id'] == st.session_state['student_id']]
        if not student_data.empty:
            classical_rank = int(student_data['classical_rank'].iloc[0])
    
    # Converter theta para escala ENEM
    enem_score = tri_calculator.theta_to_enem_scale(final_theta)
    
    # Métricas principais
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        theta_delta = f"{theta_rank}º de {total_completed}" if theta_rank and total_completed > 1 else None
        st.metric("Nota TRI (Escala ENEM)", f"{enem_score:.0f}", delta=theta_delta, delta_color="off")
        st.caption(f"θ = {final_theta:.2f}")
    
    with col2:
        st.metric("Nota Ponderada", f"{weighted_score:.1f}%")
        st.caption("Por dificuldade empírica")
    
    with col3:
        classical_delta = f"{classical_rank}º de {total_completed}" if classical_rank and total_completed > 1 else None
        st.metric("Nota Bruta", f"{classical_score:.1f}%", delta=classical_delta, delta_color="off")
        st.caption("% simples de acertos")
    
    with col4:
        st.metric("Acertos", f"{total_correct}/{total_questions}")
    
    with col5:
        st.metric("Timeouts", f"{total_timeout}")
    
    # Classificação da habilidade
    category, description = tri_calculator.classify_ability(final_theta)
    
    st.info(f"**Classificação:** {category} - {description}")
    
    st.markdown("---")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Evolução do θ", 
        "📋 Detalhamento por Questão",
        "📈 Curvas Características",
        "💡 Explicação TRI"
    ])
    
    with tab1:
        st.markdown("### Evolução da Habilidade Estimada")
        st.markdown("""
        Este gráfico mostra como sua habilidade (θ) foi estimada progressivamente
        ao longo do teste. Cada ponto representa a estimativa após responder uma questão.
        """)
        
        fig = tri_calculator.plot_theta_progression(st.session_state['theta_estimates'])
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### Análise Detalhada por Questão")
        
        # Criar tabela com detalhes
        details = []
        
        for idx, question in enumerate(questions):
            # Acessar resposta pelo question_id (responses é um dicionário)
            response = st.session_state['responses'].get(question['id'])
            
            # Só processar se tiver resposta registrada
            if response is None:
                continue
            
            # Verificar se os índices estão dentro do range
            if idx >= len(st.session_state['items_data']) or idx >= len(st.session_state['theta_estimates']):
                continue
                
            item = st.session_state['items_data'][idx]
            theta_at_time = st.session_state['theta_estimates'][idx]
            
            # Calcular probabilidade esperada
            prob_expected = tri_calculator.probability_3pl(
                theta_at_time, item['a'], item['b'], item['c']
            )
            
            # Verificar se houve timeout
            is_timeout = False
            if not student_responses.empty:
                timeout_check = student_responses[student_responses['question_id'] == question['id']]
                if not timeout_check.empty:
                    is_timeout = timeout_check.iloc[0]['is_timeout']
            
            details.append({
                'Questão': question['id'],
                'Área': question['subject'],
                'Dificuldade (b)': f"{item['b']:.2f}",
                'Discriminação (a)': f"{item['a']:.2f}",
                'Prob. Esperada': f"{prob_expected:.1%}",
                'Resultado': '✅' if response else ('⏰' if is_timeout else '❌'),
                'θ após questão': f"{theta_at_time:.2f}"
            })
        
        if details:
            st.dataframe(details, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma resposta registrada ainda.")
        
        st.markdown("""
        **Legenda:**
        - ✅ Acertou
        - ❌ Errou
        - ⏰ Timeout (tempo esgotado)
        - **Prob. Esperada:** Probabilidade de você acertar baseada no seu θ
        """)
    
    with tab3:
        st.markdown("### 📈 Curvas Características dos Itens (CCI)")
        st.info("""
        **O que é a Curva Característica do Item?**
        
        A CCI mostra a probabilidade de acertar uma questão em função da habilidade (θ). 
        Questões mais difíceis têm suas curvas deslocadas para a direita.
        """)
        
        # Seletor de questão mais destacado
        # Mapear apenas questões que foram respondidas (que têm theta_estimate)
        question_options = {}
        response_idx = 0  # Índice na lista de respostas (responses_list/theta_estimates)
        
        for q_idx, question in enumerate(questions):
            if question['id'] in st.session_state['responses']:
                response_data = st.session_state['responses'][question['id']]
                if response_data and response_data.get('answer'):
                    # Criar chave do selector
                    q_text = question['question'][:50] + "..." if len(question['question']) > 50 else question['question']
                    key = f"Q{q_idx+1:02d} - {question['subject']}: {q_text}"
                    # Mapear para o índice na lista de respostas, não na lista de questões
                    question_options[key] = (response_idx, question, q_idx)
                    response_idx += 1
        
        selected_option = st.selectbox(
            "📝 Selecione uma questão para visualizar:",
            options=list(question_options.keys()),
            key="student_cci_selector"
        )
        
        if selected_option:
            resp_idx, question, q_idx = question_options[selected_option]
            response = st.session_state['responses_list'][resp_idx]
            theta_at_time = st.session_state['theta_estimates'][resp_idx]
            
            # Informações da questão
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Questão {q_idx + 1}:** {question['question']}")
                
                # Mostrar qual foi a resposta do aluno
                student_response_data = st.session_state['responses'].get(question['id'])
                if student_response_data:
                    st.markdown("**Alternativas:**")
                    for opt in question['options']:
                        if opt['id'] == student_response_data['answer']:
                            if opt['id'] == question['correct_answer']:
                                st.markdown(f"✅ **{opt['id']})** {opt['text']} *(Sua resposta - CORRETA)*")
                            else:
                                st.markdown(f"❌ **{opt['id']})** {opt['text']} *(Sua resposta - INCORRETA)*")
                        elif opt['id'] == question['correct_answer']:
                            st.markdown(f"✔️ **{opt['id']})** {opt['text']} *(Resposta correta)*")
                        else:
                            st.markdown(f"▪️ **{opt['id']})** {opt['text']}")
            
            with col2:
                st.markdown("**Parâmetros TRI:**")
                params = question['tri_parameters']
                st.metric("a (discriminação)", f"{params['a']:.2f}")
                st.metric("b (dificuldade)", f"{params['b']:.2f}")
                st.metric("c (acerto ao acaso)", f"{params['c']:.2f}")
                st.metric("Seu θ na questão", f"{theta_at_time:.2f}")
            
            st.markdown("---")
            
            # Criar objeto item para plotagem
            item_plot = {
                'id': question['id'],
                'a': st.session_state['items_data'][q_idx]['a'],
                'b': st.session_state['items_data'][q_idx]['b'],
                'c': st.session_state['items_data'][q_idx]['c']
            }
            
            fig = tri_calculator.plot_icc_with_student(
                item_plot, 
                theta_at_time,
                response
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
            **Interpretação:**
            - **Linha azul:** Probabilidade de acerto em função da habilidade
            - **Linha vermelha (b):** Dificuldade da questão
            - **Linha verde (c):** Probabilidade de acerto ao acaso
            - **Ponto {'verde' if response else 'vermelho'}:** Sua posição (θ = {theta_at_time:.2f})
            """)
    
    with tab4:
        st.markdown("### 💡 Entendendo a TRI")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            #### Sua Nota TRI (Escala ENEM)
            
            **Nota: {enem_score:.0f} pontos** (θ = {final_theta:.2f})
            
            A nota TRI é apresentada na **escala ENEM**, que varia de **0 a 1000 pontos**.
            
            **Como interpretar:**
            - **Média:** 500 pontos (θ = 0)
            - **Acima da média:** > 500 pontos
            - **Abaixo da média:** < 500 pontos
            
            **Faixas de desempenho:**
            - 0-349: Insuficiente
            - 350-449: Básico
            - 450-549: Regular
            - 550-649: Bom
            - 650-749: Muito Bom
            - 750-1000: Excelente
            """)
            
            st.markdown("""
            #### Parâmetros dos Itens
            
            Cada questão tem 3 parâmetros:
            
            1. **a (discriminação):** Quão bem a questão distingue alunos de diferentes habilidades
               - Maior a = melhor discriminação
            
            2. **b (dificuldade):** Nível de habilidade necessário para 50% de chance de acerto
               - b alto = questão difícil
               - b baixo = questão fácil
            
            3. **c (acerto ao acaso):** Probabilidade de acertar chutando
               - Geralmente 0.25 (25%) para 4 alternativas
            """)
        
        with col2:
            st.markdown("""
            #### Modelo Matemático
            
            A probabilidade de você acertar uma questão é dada por:
            
            $$P(\\theta) = c + \\frac{1-c}{1 + e^{-a(\\theta - b)}}$$
            
            Onde:
            - $P(\\theta)$ = Probabilidade de acerto
            - $\\theta$ = Sua habilidade
            - $a, b, c$ = Parâmetros da questão
            """)
            
            st.markdown(f"""
            #### Três Sistemas de Pontuação
            
            **1. Nota Bruta (TCT Tradicional):** {classical_score:.1f}%
            - Simplesmente % de acertos
            - Todas as questões têm o mesmo peso
            - Dois alunos com mesmo nº de acertos = mesma nota
            
            **2. Nota Ponderada:** {weighted_score:.1f}%
            - Pondera acertos pela dificuldade empírica (taxa de acerto da turma)
            - Questões que menos alunos acertam valem mais pontos
            - Dois alunos com mesmo nº de acertos podem ter notas diferentes
            
            **3. Nota TRI (ENEM):** {enem_score:.0f} pontos (θ = {final_theta:.2f})
            - Modelo logístico de 3 parâmetros (discriminação, dificuldade, acerto casual)
            - Considera qualidade dos itens além da dificuldade
            - Independente da turma (usa parâmetros pré-calibrados)
            
            **Comparação:**
            | Método | Peso dos Itens | Depende da Turma |
            |--------|----------------|------------------|
            | Bruta | Todos iguais | Não |
            | Ponderada | Por dificuldade empírica | Sim |
            | TRI | Por parâmetros a, b, c | Não |
            """)
    
    st.markdown("---")
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Voltar ao Início", use_container_width=True):
            # Limpar session_state do teste
            for key in ['test_started', 'current_question', 'responses', 
                       'items_data', 'theta_estimates', 'test_completed']:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("app.py")
    
    with col2:
        if st.button("📊 Ver Painel Admin", use_container_width=True):
            st.switch_page("pages/2_📊_Painel_Admin.py")
    
    with col3:
        st.markdown("")  # Espaço


def main():
    """Função principal da página de teste."""
    
    # Verificar se está logado
    if 'student_name' not in st.session_state or 'student_id' not in st.session_state:
        st.error("⚠️ Você precisa fazer login primeiro!")
        if st.button("← Voltar para Login"):
            st.switch_page("app.py")
        return
    
    # Carregar questões
    questions, time_per_question, total_exam_time = load_questions()
    
    if not questions:
        st.error("Erro ao carregar questões!")
        return
    
    # ===== VERIFICAR HORÁRIO DE INÍCIO DA PROVA =====
    exam_start = database.get_exam_start()
    
    if exam_start:
        from datetime import datetime, timezone, timedelta
        
        # Usar horário de Brasília (UTC-3)
        brasilia_tz = timezone(timedelta(hours=-3))
        now = datetime.now(brasilia_tz)
        
        if now < exam_start:
            # Prova ainda não começou
            st.warning("⏳ **A prova ainda não começou!**")
            st.info(f"🕐 **Início programado:** {exam_start.strftime('%d/%m/%Y às %H:%M')} (Horário de Brasília)")
            
            # Calcular tempo restante até o início
            time_until_start = (exam_start - now).total_seconds()
            
            if time_until_start > 0:
                hours = int(time_until_start // 3600)
                minutes = int((time_until_start % 3600) // 60)
                seconds = int(time_until_start % 60)
                
                st.markdown("### ⏱️ Tempo até o início:")
                
                # Display countdown
                countdown_html = f"""
                <div style="
                    text-align: center;
                    padding: 2rem;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 15px;
                    margin: 2rem 0;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                ">
                    <div style="
                        font-size: 4rem;
                        font-weight: bold;
                        color: white;
                        font-family: 'Courier New', monospace;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    ">
                        {hours:02d}:{minutes:02d}:{seconds:02d}
                    </div>
                    <div style="
                        font-size: 1.2rem;
                        color: rgba(255,255,255,0.9);
                        margin-top: 0.5rem;
                    ">
                        horas : minutos : segundos
                    </div>
                </div>
                """
                
                st.markdown(countdown_html, unsafe_allow_html=True)
                
                # Auto-refresh a cada 20 segundos
                st_autorefresh(interval=20000, key="exam_start_countdown")
            
            # Botão para voltar
            if st.button("🏠 Voltar ao Início", use_container_width=True, type="primary"):
                st.switch_page("app.py")
            
            return
    
    # ===== CONTINUAR COM A PROVA (código original) =====
    
    # Inicializar teste
    initialize_test(total_exam_time)
    
    # Verificar deadline global
    remaining_time = display_global_timer()
    
    # Se deadline existe e tempo esgotou, finalizar prova automaticamente
    if remaining_time is not None and remaining_time <= 0:
        st.error("⏰ **TEMPO ESGOTADO!** A prova foi finalizada automaticamente.")
        st.info("Suas respostas foram salvas. Veja seus resultados abaixo.")
        
        # Forçar finalização se ainda não finalizou
        if not st.session_state.get('test_completed', False):
            st.session_state['current_question'] = len(questions)
            st.session_state['test_completed'] = True
        
        display_results(questions)
        return
    
    # Autorefresh a cada 20 segundos (se houver deadline)
    if remaining_time is not None:
        st_autorefresh(interval=20000, key="global_timer_refresh")
    
    # Verificar se completou o teste
    if st.session_state['current_question'] >= len(questions):
        if not st.session_state.get('test_completed', False):
            st.session_state['test_completed'] = True
        
        display_results(questions)
        
        # Footer
        st.markdown("""
        <div class="footer">
            <span class="footer-dev">Grupo:</span> Letícia Lopes, Fillipe Paz, Weverton Barros, André Silva<br>
            <span class="footer-dev">Desenvolvido por:</span> Fillipe Paz
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Exibir questão atual
    current_q_index = st.session_state['current_question']
    current_question = questions[current_q_index]
    
    display_question(
        current_question,
        current_q_index + 1,
        len(questions),
        questions
    )


if __name__ == "__main__":
    main()
