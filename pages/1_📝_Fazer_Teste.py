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


def load_questions():
    """Carrega as questões do arquivo JSON."""
    try:
        with open('data/questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['questions'], data['time_per_question']
    except Exception as e:
        st.error(f"Erro ao carregar questões: {e}")
        return None, None


def initialize_test():
    """Inicializa o teste no session_state."""
    if 'test_started' not in st.session_state:
        st.session_state['test_started'] = True
        st.session_state['current_question'] = 0
        st.session_state['responses'] = []
        st.session_state['items_data'] = []
        st.session_state['theta_estimates'] = []
        st.session_state['test_completed'] = False


def save_response_and_update_theta(question, answer, is_timeout):
    """
    Salva a resposta e atualiza a estimativa de theta.
    
    Args:
        question: Dicionário com dados da questão
        answer: Resposta do aluno (None se timeout)
        is_timeout: Se houve timeout
    """
    is_correct = (answer == question['correct_answer']) if answer else False
    
    # Adicionar aos dados de respostas
    st.session_state['responses'].append(is_correct)
    st.session_state['items_data'].append(question['tri_parameters'])
    
    # Calcular theta progressivamente
    theta = tri_calculator.estimate_theta_progressive(
        st.session_state['responses'],
        st.session_state['items_data']
    )
    st.session_state['theta_estimates'].append(theta)
    
    # Salvar no banco de dados
    success = database.save_response(
        student_id=st.session_state['student_id'],
        student_name=st.session_state['student_name'],
        question_id=question['id'],
        answer=answer,
        is_correct=is_correct,
        is_timeout=is_timeout,
        theta_estimate=theta
    )
    
    if not success:
        st.warning("⚠️ Não foi possível salvar a resposta no banco de dados.")
    
    # Avançar para próxima questão
    st.session_state['current_question'] += 1


def display_question(question, question_num, total_questions, time_per_question):
    """
    Exibe uma questão com timer.
    
    Args:
        question: Dicionário com dados da questão
        question_num: Número da questão atual (1-indexed)
        total_questions: Total de questões
        time_per_question: Tempo por questão em segundos
    """
    # Barra de progresso
    timer_module.display_progress_bar(question_num, total_questions)
    
    st.markdown("---")
    
    # Container para timer
    timer_placeholder = st.empty()
    
    # Inicializar timer se necessário
    timer_key = f"timer_start_{question['id']}"
    if timer_key not in st.session_state:
        timer_module.initialize_timer_in_session(question['id'], time_per_question)
        st.session_state[timer_key] = True
    
    # Obter tempo restante
    remaining_time = timer_module.get_timer_remaining(question['id'])
    
    # Exibir timer
    timer_module.display_timer(remaining_time, timer_placeholder)
    
    # Verificar timeout
    if remaining_time == 0:
        # Timeout - exibir mensagem e botão para prosseguir
        timer_module.display_timeout_message(st.empty())
        
        st.warning("⏰ **Tempo esgotado!** Esta questão será marcada como não respondida.")
        
        # Botão para prosseguir
        if st.button("➡️ Próxima Questão", type="primary", use_container_width=True):
            # Salvar resposta como timeout
            save_response_and_update_theta(question, None, True)
            timer_module.clear_timer(question['id'])
            st.rerun()
        
        st.stop()  # Impede a exibição da questão até clicar no botão
    
    # Exibir questão
    st.markdown(f"### Questão {question_num}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Área:** {question['subject']}")
    
    st.markdown("---")
    
    st.markdown(f"**{question['question']}**")
    
    st.markdown("")
    
    # Opções de resposta
    selected_answer = None
    
    for option in question['options']:
        col1, col2 = st.columns([0.1, 0.9])
        with col2:
            if st.button(
                f"**{option['id']})** {option['text']}", 
                key=f"opt_{question['id']}_{option['id']}",
                use_container_width=True
            ):
                selected_answer = option['id']
    
    # Se uma resposta foi selecionada
    if selected_answer:
        # Parar timer
        timer_module.stop_timer(question['id'])
        
        # Salvar resposta
        save_response_and_update_theta(question, selected_answer, False)
        timer_module.clear_timer(question['id'])
        
        # Rerun para próxima questão
        st.rerun()


def display_results(questions):
    """
    Exibe os resultados finais do teste.
    
    Args:
        questions: Lista de questões
    """
    st.markdown("# 🎉 Teste Concluído!")
    
    st.markdown("---")
    
    # Calcular estatísticas
    final_theta = st.session_state['theta_estimates'][-1] if st.session_state['theta_estimates'] else 0.0
    total_correct = sum(st.session_state['responses'])
    total_questions = len(st.session_state['responses'])
    classical_score = (total_correct / total_questions) * 100 if total_questions > 0 else 0
    
    # Obter contagem de timeouts do banco
    student_responses = database.get_student_responses(st.session_state['student_id'])
    total_timeout = student_responses['is_timeout'].sum() if not student_responses.empty else 0
    
    # Salvar sessão completa
    database.complete_session(
        student_id=st.session_state['student_id'],
        final_theta=final_theta,
        total_correct=int(total_correct),
        total_timeout=int(total_timeout)
    )
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Habilidade θ (TRI)", f"{final_theta:.2f}")
    
    with col2:
        st.metric("Nota Clássica", f"{classical_score:.1f}%")
    
    with col3:
        st.metric("Acertos", f"{total_correct}/{total_questions}")
    
    with col4:
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
        
        for idx, question in enumerate(questions[:len(st.session_state['responses'])]):
            response = st.session_state['responses'][idx]
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
        
        st.dataframe(details, use_container_width=True, hide_index=True)
        
        st.markdown("""
        **Legenda:**
        - ✅ Acertou
        - ❌ Errou
        - ⏰ Timeout (tempo esgotado)
        - **Prob. Esperada:** Probabilidade de você acertar baseada no seu θ
        """)
    
    with tab3:
        st.markdown("### Curvas Características dos Itens (CCI)")
        st.markdown("""
        Selecione uma questão para ver sua Curva Característica e onde você se posicionou.
        """)
        
        # Seletor de questão
        question_options = [f"{q['id']} - {q['subject']}" for q in questions[:len(st.session_state['responses'])]]
        selected_q = st.selectbox("Selecione uma questão:", question_options)
        
        if selected_q:
            q_idx = question_options.index(selected_q)
            question = questions[q_idx]
            response = st.session_state['responses'][q_idx]
            theta_at_time = st.session_state['theta_estimates'][q_idx]
            
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
            st.markdown("""
            #### O que é θ (theta)?
            
            Theta (θ) representa sua **habilidade estimada**. É um número que pode variar
            de -∞ a +∞, mas tipicamente fica entre -3 e +3.
            
            - **θ = 0:** Habilidade média
            - **θ > 0:** Acima da média
            - **θ < 0:** Abaixo da média
            
            Seu θ final: **{:.2f}**
            """.format(final_theta))
            
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
            
            st.markdown("""
            #### TRI vs Nota Clássica
            
            **Nota Clássica:** {:.1f}% (simplesmente % de acertos)
            
            **TRI:** θ = {:.2f}
            
            A diferença é que a TRI considera:
            - ✅ Dificuldade de cada questão
            - ✅ Qualidade (discriminação) das questões
            - ✅ Probabilidade de chute
            
            Por isso, acertar questões difíceis vale "mais" do que acertar questões fáceis!
            """.format(classical_score, final_theta))
    
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
    questions, time_per_question = load_questions()
    
    if not questions:
        st.error("Erro ao carregar questões!")
        return
    
    # Inicializar teste
    initialize_test()
    
    # Verificar se completou o teste
    if st.session_state['current_question'] >= len(questions):
        if not st.session_state.get('test_completed', False):
            st.session_state['test_completed'] = True
        
        display_results(questions)
        return
    
    # Exibir questão atual
    current_q_index = st.session_state['current_question']
    current_question = questions[current_q_index]
    
    # Verificar se timer ainda está ativo antes de ativar autorefresh
    timer_key = f"timer_{current_question['id']}"
    if timer_key in st.session_state and st.session_state[timer_key].get('is_active', False):
        remaining = timer_module.get_timer_remaining(current_question['id'])
        if remaining > 0:
            # Auto-refresh a cada 1000ms (1 segundo) para atualizar timer
            st_autorefresh(interval=1000, key=f"timer_refresh_{current_question['id']}")
    
    display_question(
        current_question,
        current_q_index + 1,
        len(questions),
        time_per_question
    )


if __name__ == "__main__":
    main()
