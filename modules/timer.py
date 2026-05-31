"""
Módulo de timer para questões com feedback visual.
Gerencia countdown de 45 segundos com alertas visuais.
"""

import streamlit as st
import time
from datetime import datetime, timedelta


class QuestionTimer:
    """
    Classe para gerenciar o timer de uma questão.
    """
    
    def __init__(self, duration_seconds: int = 45):
        """
        Inicializa o timer.
        
        Args:
            duration_seconds: Duração em segundos (padrão 45)
        """
        self.duration = duration_seconds
        self.start_time = None
        self.is_active = False
    
    def start(self):
        """Inicia o timer."""
        self.start_time = time.time()
        self.is_active = True
    
    def get_remaining_time(self) -> int:
        """
        Obtém o tempo restante em segundos.
        
        Returns:
            int: Segundos restantes (mínimo 0)
        """
        if not self.is_active or self.start_time is None:
            return self.duration
        
        elapsed = time.time() - self.start_time
        remaining = max(0, self.duration - int(elapsed))
        
        return remaining
    
    def is_timeout(self) -> bool:
        """
        Verifica se o tempo acabou.
        
        Returns:
            bool: True se timeout, False caso contrário
        """
        return self.get_remaining_time() == 0
    
    def stop(self):
        """Para o timer."""
        self.is_active = False
    
    def reset(self):
        """Reseta o timer."""
        self.start_time = None
        self.is_active = False


def display_timer(remaining_seconds: int, placeholder) -> None:
    """
    Exibe o timer com feedback visual baseado no tempo restante.
    
    Args:
        remaining_seconds: Segundos restantes
        placeholder: st.empty() placeholder para atualização
    """
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    
    # Determinar cor e estilo baseado no tempo restante
    if remaining_seconds > 10:
        # Normal - verde/azul
        color = "#28a745"  # Verde
        icon = "⏱️"
        size = "2rem"
        weight = "normal"
    elif remaining_seconds > 5:
        # Aviso - amarelo
        color = "#ffc107"  # Amarelo
        icon = "⚠️"
        size = "2.5rem"
        weight = "bold"
    else:
        # Crítico - vermelho
        color = "#dc3545"  # Vermelho
        icon = "🔴"
        size = "3rem"
        weight = "bold"
    
    # HTML com estilo
    timer_html = f"""
    <div style="
        text-align: center;
        padding: 1rem;
        background-color: {'#fff3cd' if remaining_seconds <= 10 else '#f8f9fa'};
        border: 2px solid {color};
        border-radius: 10px;
        margin: 1rem 0;
    ">
        <div style="
            font-size: {size};
            font-weight: {weight};
            color: {color};
        ">
            {icon} {minutes:02d}:{seconds:02d}
        </div>
        <div style="
            font-size: 0.9rem;
            color: #6c757d;
            margin-top: 0.5rem;
        ">
            {'Tempo restante' if remaining_seconds > 0 else 'Tempo esgotado!'}
        </div>
    </div>
    """
    
    placeholder.markdown(timer_html, unsafe_allow_html=True)


def display_timeout_message(placeholder) -> None:
    """
    Exibe mensagem de timeout.
    
    Args:
        placeholder: st.empty() placeholder para mensagem
    """
    timeout_html = """
    <div style="
        text-align: center;
        padding: 2rem;
        background-color: #f8d7da;
        border: 3px solid #dc3545;
        border-radius: 10px;
        margin: 1rem 0;
        animation: pulse 1s ease-in-out;
    ">
        <div style="
            font-size: 3rem;
            margin-bottom: 1rem;
        ">
            ⏰
        </div>
        <div style="
            font-size: 1.5rem;
            font-weight: bold;
            color: #dc3545;
            margin-bottom: 0.5rem;
        ">
            Tempo Esgotado!
        </div>
        <div style="
            font-size: 1rem;
            color: #721c24;
        ">
            Avançando para a próxima questão...
        </div>
    </div>
    
    <style>
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    </style>
    """
    
    placeholder.markdown(timeout_html, unsafe_allow_html=True)


def initialize_timer_in_session(question_id: str, duration: int = 45) -> None:
    """
    Inicializa o timer no session_state para uma questão específica.
    
    Args:
        question_id: ID da questão
        duration: Duração em segundos
    """
    timer_key = f"timer_{question_id}"
    
    if timer_key not in st.session_state:
        st.session_state[timer_key] = {
            'start_time': time.time(),
            'duration': duration,
            'is_active': True
        }


def get_timer_remaining(question_id: str) -> int:
    """
    Obtém tempo restante do timer no session_state.
    
    Args:
        question_id: ID da questão
    
    Returns:
        int: Segundos restantes
    """
    timer_key = f"timer_{question_id}"
    
    if timer_key not in st.session_state:
        return 0
    
    timer_data = st.session_state[timer_key]
    
    if not timer_data['is_active']:
        return 0
    
    elapsed = time.time() - timer_data['start_time']
    remaining = max(0, timer_data['duration'] - int(elapsed))
    
    return remaining


def stop_timer(question_id: str) -> None:
    """
    Para o timer de uma questão.
    
    Args:
        question_id: ID da questão
    """
    timer_key = f"timer_{question_id}"
    
    if timer_key in st.session_state:
        st.session_state[timer_key]['is_active'] = False


def clear_timer(question_id: str) -> None:
    """
    Remove o timer do session_state.
    
    Args:
        question_id: ID da questão
    """
    timer_key = f"timer_{question_id}"
    
    if timer_key in st.session_state:
        del st.session_state[timer_key]


def display_progress_bar(current: int, total: int) -> None:
    """
    Exibe barra de progresso do teste.
    
    Args:
        current: Questão atual (1-indexed)
        total: Total de questões
    """
    progress = current / total
    
    st.progress(progress)
    
    progress_html = f"""
    <div style="
        text-align: center;
        font-size: 1.1rem;
        color: #495057;
        margin: 0.5rem 0;
    ">
        Questão <strong>{current}</strong> de <strong>{total}</strong>
        ({int(progress * 100)}% concluído)
    </div>
    """
    
    st.markdown(progress_html, unsafe_allow_html=True)
