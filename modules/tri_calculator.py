"""
Módulo de cálculos TRI (Teoria de Resposta ao Item).
Implementa o modelo logístico de 3 parâmetros e estimação de habilidade.
"""

import numpy as np
from scipy.optimize import minimize_scalar, minimize
from typing import List, Dict, Tuple
import plotly.graph_objects as go
import plotly.express as px


def theta_to_enem_scale(theta: float) -> float:
    """
    Converte theta para escala ENEM (0-1000).
    
    Escala ENEM: média 500, desvio padrão 100
    Theta: média 0, desvio padrão 1
    
    Fórmula: Nota_ENEM = 500 + (100 × θ)
    
    Args:
        theta: Habilidade no formato theta
    
    Returns:
        float: Nota na escala ENEM (0-1000)
    """
    nota = 500 + (100 * theta)
    # Limitar entre 0 e 1000
    return np.clip(nota, 0, 1000)


def enem_scale_to_theta(enem_score: float) -> float:
    """
    Converte nota ENEM para theta.
    
    Args:
        enem_score: Nota na escala ENEM (0-1000)
    
    Returns:
        float: Habilidade theta
    """
    return (enem_score - 500) / 100


def probability_3pl(theta: float, a: float, b: float, c: float) -> float:
    """
    Calcula a probabilidade de acerto usando o modelo logístico de 3 parâmetros.
    
    P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
    
    Args:
        theta: Habilidade do aluno
        a: Parâmetro de discriminação (a > 0)
        b: Parâmetro de dificuldade
        c: Probabilidade de acerto ao acaso (0 <= c < 1)
    
    Returns:
        float: Probabilidade de acerto [0, 1]
    """
    try:
        exp_term = np.exp(-a * (theta - b))
        prob = c + (1 - c) / (1 + exp_term)
        return np.clip(prob, 0.0, 1.0)
    except:
        return c


def log_likelihood(theta: float, responses: List[bool], items: List[Dict]) -> float:
    """
    Calcula o log da função de verossimilhança.
    
    Args:
        theta: Habilidade a ser avaliada
        responses: Lista de respostas (True=acertou, False=errou)
        items: Lista de dicionários com parâmetros TRI {a, b, c}
    
    Returns:
        float: Log-verossimilhança (quanto maior, melhor)
    """
    log_lik = 0.0
    
    for response, item in zip(responses, items):
        a = item['a']
        b = item['b']
        c = item['c']
        
        prob = probability_3pl(theta, a, b, c)
        
        # Evitar log(0)
        prob = np.clip(prob, 1e-10, 1 - 1e-10)
        
        if response:
            log_lik += np.log(prob)
        else:
            log_lik += np.log(1 - prob)
    
    return log_lik


def estimate_theta_mle(responses: List[bool], items: List[Dict]) -> float:
    """
    Estima a habilidade θ usando Maximum Likelihood Estimation (MLE).
    
    Args:
        responses: Lista de respostas (True=acertou, False=errou/timeout)
        items: Lista de dicionários com parâmetros TRI {a, b, c}
    
    Returns:
        float: Estimativa de θ
    """
    if not responses or not items:
        return 0.0
    
    # Se todas as respostas são iguais, usar heurística
    if all(responses):
        # Acertou tudo - θ alto
        max_b = max(item['b'] for item in items)
        return max_b + 2.0
    elif not any(responses):
        # Errou tudo - θ baixo
        min_b = min(item['b'] for item in items)
        return min_b - 2.0
    
    # Função objetivo (negativo da log-likelihood para minimizar)
    def objective(theta):
        return -log_likelihood(theta, responses, items)
    
    # Otimização no intervalo [-4, 4]
    result = minimize_scalar(objective, bounds=(-4, 4), method='bounded')
    
    return result.x


def estimate_theta_progressive(
    responses: List[bool], 
    items: List[Dict],
    previous_theta: float = 0.0
) -> float:
    """
    Estima θ progressivamente após cada resposta.
    
    Args:
        responses: Lista de respostas até o momento
        items: Lista de itens correspondentes
        previous_theta: Estimativa anterior de θ
    
    Returns:
        float: Nova estimativa de θ
    """
    if not responses:
        return 0.0
    
    return estimate_theta_mle(responses, items)


def calculate_information(theta: float, a: float, b: float, c: float) -> float:
    """
    Calcula a informação do item na habilidade θ.
    
    Args:
        theta: Habilidade
        a: Discriminação
        b: Dificuldade
        c: Acerto ao acaso
    
    Returns:
        float: Informação do item
    """
    prob = probability_3pl(theta, a, b, c)
    q = 1 - prob
    
    # Derivada da probabilidade
    exp_term = np.exp(-a * (theta - b))
    dp_dtheta = a * (1 - c) * exp_term / ((1 + exp_term) ** 2)
    
    # Informação de Fisher
    if prob > 1e-10 and q > 1e-10:
        information = (dp_dtheta ** 2) / (prob * q)
        return information
    
    return 0.0


def plot_icc(item: Dict, theta_range: Tuple[float, float] = (-3, 3)) -> go.Figure:
    """
    Plota a Curva Característica do Item (ICC).
    
    Args:
        item: Dicionário com parâmetros {id, a, b, c}
        theta_range: Tupla com (theta_min, theta_max)
    
    Returns:
        go.Figure: Figura plotly
    """
    theta_values = np.linspace(theta_range[0], theta_range[1], 200)
    probs = [probability_3pl(t, item['a'], item['b'], item['c']) for t in theta_values]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=theta_values,
        y=probs,
        mode='lines',
        name='P(θ)',
        line=dict(color='blue', width=2)
    ))
    
    # Linha vertical na dificuldade b
    fig.add_vline(
        x=item['b'], 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"b = {item['b']:.2f}"
    )
    
    # Linha horizontal no parâmetro c
    fig.add_hline(
        y=item['c'], 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"c = {item['c']:.2f}"
    )
    
    fig.update_layout(
        title=f"Curva Característica do Item - {item.get('id', 'Item')}",
        xaxis_title="Habilidade (θ)",
        yaxis_title="Probabilidade de Acerto P(θ)",
        yaxis_range=[0, 1],
        template="plotly_white"
    )
    
    return fig


def plot_icc_with_student(
    item: Dict, 
    student_theta: float,
    student_response: bool,
    theta_range: Tuple[float, float] = (-3, 3)
) -> go.Figure:
    """
    Plota a ICC destacando a posição do aluno.
    
    Args:
        item: Dicionário com parâmetros TRI
        student_theta: Habilidade estimada do aluno
        student_response: Se o aluno acertou (True) ou errou (False)
        theta_range: Tupla com (theta_min, theta_max)
    
    Returns:
        go.Figure: Figura plotly
    """
    fig = plot_icc(item, theta_range)
    
    # Probabilidade esperada para o aluno
    prob_expected = probability_3pl(student_theta, item['a'], item['b'], item['c'])
    
    # Adicionar ponto do aluno
    color = 'green' if student_response else 'red'
    symbol = 'circle' if student_response else 'x'
    
    fig.add_trace(go.Scatter(
        x=[student_theta],
        y=[prob_expected],
        mode='markers',
        name=f"Aluno ({'Acertou' if student_response else 'Errou'})",
        marker=dict(size=12, color=color, symbol=symbol)
    ))
    
    return fig


def plot_theta_distribution(thetas: List[float]) -> go.Figure:
    """
    Plota a distribuição de habilidades dos alunos.
    
    Args:
        thetas: Lista de valores de θ estimados
    
    Returns:
        go.Figure: Figura plotly
    """
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=thetas,
        nbinsx=20,
        name='Distribuição de θ',
        marker_color='steelblue'
    ))
    
    fig.update_layout(
        title="Distribuição de Habilidades da Turma",
        xaxis_title="Habilidade (θ)",
        yaxis_title="Frequência",
        template="plotly_white"
    )
    
    return fig


def plot_theta_progression(theta_estimates: List[float]) -> go.Figure:
    """
    Plota a evolução de θ ao longo das questões.
    
    Args:
        theta_estimates: Lista de estimativas de θ após cada questão
    
    Returns:
        go.Figure: Figura plotly
    """
    question_numbers = list(range(1, len(theta_estimates) + 1))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=question_numbers,
        y=theta_estimates,
        mode='lines+markers',
        name='θ estimado',
        line=dict(color='purple', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="gray",
        annotation_text="θ = 0 (média)"
    )
    
    fig.update_layout(
        title="Evolução da Habilidade Estimada (θ)",
        xaxis_title="Número da Questão",
        yaxis_title="Habilidade (θ)",
        template="plotly_white"
    )
    
    return fig


def classify_ability(theta: float) -> Tuple[str, str]:
    """
    Classifica a habilidade θ em categorias descritivas (estilo ENEM).
    
    Args:
        theta: Habilidade estimada
    
    Returns:
        Tuple[str, str]: (categoria, descrição)
    """
    # Converter para escala ENEM
    enem_score = theta_to_enem_scale(theta)
    
    if enem_score < 350:
        return ("Insuficiente", "Desempenho muito abaixo do esperado")
    elif enem_score < 450:
        return ("Básico", "Desempenho abaixo da média")
    elif enem_score < 550:
        return ("Regular", "Desempenho na média")
    elif enem_score < 650:
        return ("Bom", "Desempenho acima da média")
    elif enem_score < 750:
        return ("Muito Bom", "Desempenho muito acima da média")
    else:
        return ("Excelente", "Desempenho excepcional")


def calculate_classical_score(responses: List[bool]) -> float:
    """
    Calcula a nota clássica (percentual de acertos).
    
    Args:
        responses: Lista de respostas
    
    Returns:
        float: Percentual de acertos [0, 100]
    """
    if not responses:
        return 0.0
    
    correct = sum(responses)
    total = len(responses)
    
    return (correct / total) * 100


def calculate_tct_score(responses: List[bool], item_difficulties: List[float]) -> float:
    """
    Calcula a nota pela Teoria Clássica dos Testes (TCT).
    Pondera os acertos pela dificuldade empírica dos itens.
    
    Na TCT, itens mais difíceis (menor taxa de acerto) valem mais pontos.
    
    Args:
        responses: Lista de respostas (True=acertou, False=errou)
        item_difficulties: Lista com taxa de acerto de cada item (0-1)
    
    Returns:
        float: Nota TCT ponderada [0, 100]
    """
    if not responses or not item_difficulties or len(responses) != len(item_difficulties):
        return 0.0
    
    # Calcular peso de cada item (inverso da dificuldade)
    # Item difícil (baixa taxa de acerto) = peso alto
    weights = []
    for difficulty in item_difficulties:
        # Evitar divisão por zero e valores extremos
        difficulty = max(0.1, min(0.9, difficulty))
        weight = 1.0 / difficulty  # Quanto menor a taxa de acerto, maior o peso
        weights.append(weight)
    
    # Normalizar pesos para somar 1
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    
    # Calcular nota ponderada
    weighted_score = sum(r * w for r, w in zip(responses, normalized_weights))
    
    return weighted_score * 100


def get_question_statistics(all_responses: List[Dict]) -> Dict:
    """
    Calcula estatísticas por questão.
    
    Args:
        all_responses: Lista de respostas de todos os alunos
    
    Returns:
        Dict: Estatísticas por questão
    """
    stats = {}
    
    for response in all_responses:
        q_id = response['question_id']
        
        if q_id not in stats:
            stats[q_id] = {
                'total': 0,
                'correct': 0,
                'timeout': 0
            }
        
        stats[q_id]['total'] += 1
        if response['is_correct']:
            stats[q_id]['correct'] += 1
        if response.get('is_timeout', False):
            stats[q_id]['timeout'] += 1
    
    # Calcular taxas
    for q_id in stats:
        total = stats[q_id]['total']
        if total > 0:
            stats[q_id]['correct_rate'] = stats[q_id]['correct'] / total
            stats[q_id]['timeout_rate'] = stats[q_id]['timeout'] / total
    
    return stats
