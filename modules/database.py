"""
Módulo de gerenciamento de banco de dados usando Supabase.
Salva respostas dos alunos e permite recuperação de dados para análise.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Optional[Client]:
    """
    Conecta ao Supabase usando credenciais do Streamlit secrets.
    
    Returns:
        Client: Cliente autenticado do Supabase
    """
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        client = create_client(url, key)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar ao Supabase: {e}")
        return None


def init_database():
    """
    Inicializa as tabelas no Supabase se não existirem.
    
    SQL para criar as tabelas (execute no Supabase SQL Editor):
    
    -- Tabela de sessões
    CREATE TABLE IF NOT EXISTS sessions (
        id BIGSERIAL PRIMARY KEY,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        completed_at TIMESTAMP WITH TIME ZONE,
        final_theta FLOAT,
        total_correct INTEGER,
        total_timeout INTEGER,
        status TEXT NOT NULL DEFAULT 'in_progress',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Tabela de respostas
    CREATE TABLE IF NOT EXISTS responses (
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
    
    -- Índices para melhor performance
    CREATE INDEX IF NOT EXISTS idx_sessions_student_id ON sessions(student_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
    CREATE INDEX IF NOT EXISTS idx_responses_student_id ON responses(student_id);
    CREATE INDEX IF NOT EXISTS idx_responses_question_id ON responses(question_id);
    """
    pass


def generate_student_id(student_name: str) -> str:
    """
    Gera um ID único para o aluno combinando nome e timestamp.
    
    Args:
        student_name: Nome completo do aluno
    
    Returns:
        str: ID único no formato 'nome_YYYYMMDD_HHMMSS'
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Limpar caracteres especiais do nome
    clean_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '-', '_'))
    clean_name = clean_name.replace(' ', '_')
    return f"{clean_name}_{timestamp}"


def save_response(
    student_id: str,
    student_name: str,
    question_id: str,
    answer: Optional[str],
    is_correct: bool,
    is_timeout: bool,
    theta_estimate: float
) -> bool:
    """
    Salva uma resposta individual no Supabase.
    
    Args:
        student_id: ID único do aluno
        student_name: Nome do aluno
        question_id: ID da questão
        answer: Resposta do aluno (None se timeout)
        is_correct: Se a resposta está correta
        is_timeout: Se houve timeout
        theta_estimate: Estimativa atual de theta
    
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        data = {
            "student_id": student_id,
            "student_name": student_name,
            "question_id": question_id,
            "answer": answer if answer else None,
            "is_correct": is_correct,
            "is_timeout": is_timeout,
            "theta_estimate": float(theta_estimate)
        }
        
        result = client.table("responses").insert(data).execute()
        return True
        
    except Exception as e:
        st.error(f"Erro ao salvar resposta: {e}")
        return False


def start_session(student_id: str, student_name: str) -> bool:
    """
    Inicia uma nova sessão de teste para um aluno.
    
    Args:
        student_id: ID único do aluno
        student_name: Nome do aluno
    
    Returns:
        bool: True se criou com sucesso, False caso contrário
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        data = {
            "student_id": student_id,
            "student_name": student_name,
            "status": "in_progress"
        }
        
        result = client.table("sessions").insert(data).execute()
        return True
        
    except Exception as e:
        st.error(f"Erro ao iniciar sessão: {e}")
        return False


def complete_session(
    student_id: str,
    final_theta: float,
    total_correct: int,
    total_timeout: int
) -> bool:
    """
    Finaliza a sessão de teste de um aluno.
    
    Args:
        student_id: ID único do aluno
        final_theta: Theta final estimado
        total_correct: Total de respostas corretas
        total_timeout: Total de timeouts
    
    Returns:
        bool: True se atualizou com sucesso, False caso contrário
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        data = {
            "completed_at": datetime.now().isoformat(),
            "final_theta": float(final_theta),
            "total_correct": int(total_correct),
            "total_timeout": int(total_timeout),
            "status": "completed"
        }
        
        result = client.table("sessions").update(data).eq("student_id", student_id).eq("status", "in_progress").execute()
        return True
        
    except Exception as e:
        st.error(f"Erro ao finalizar sessão: {e}")
        return False


def get_student_responses(student_id: str) -> pd.DataFrame:
    """
    Recupera todas as respostas de um aluno específico.
    
    Args:
        student_id: ID único do aluno
    
    Returns:
        pd.DataFrame: DataFrame com as respostas do aluno
    """
    try:
        client = get_supabase_client()
        if not client:
            return pd.DataFrame()
        
        result = client.table("responses").select("*").eq("student_id", student_id).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            return df
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao recuperar respostas: {e}")
        return pd.DataFrame()

def get_exam_deadline():
    """
    Obtém o horário limite da prova.
    
    Returns:
        datetime or None: Horário limite da prova (timezone-aware) ou None se não definido
    """
    try:
        client = get_supabase_client()
        result = client.table("exam_config").select("config_value").eq("config_key", "exam_deadline").execute()
        
        if result.data and len(result.data) > 0:
            deadline_str = result.data[0].get('config_value')
            if deadline_str:
                return datetime.fromisoformat(deadline_str)
        return None
    except Exception as e:
        st.error(f"Erro ao buscar deadline: {e}")
        return None


def set_exam_deadline(deadline_datetime):
    """
    Define o horário limite da prova.
    
    Args:
        deadline_datetime: datetime object (timezone-aware) ou None para remover deadline
    
    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        client = get_supabase_client()
        
        # Converter datetime para string ISO ou None
        deadline_str = deadline_datetime.isoformat() if deadline_datetime else None
        
        # Verificar se já existe
        existing = client.table("exam_config").select("id").eq("config_key", "exam_deadline").execute()
        
        if existing.data and len(existing.data) > 0:
            # Atualizar se já existe
            result = client.table("exam_config").update({
                "config_value": deadline_str,
                "updated_at": datetime.now().isoformat()
            }).eq("config_key", "exam_deadline").execute()
        else:
            # Inserir se não existe
            result = client.table("exam_config").insert({
                "config_key": "exam_deadline",
                "config_value": deadline_str,
                "updated_at": datetime.now().isoformat()
            }).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao definir deadline: {e}")
        return False


def get_num_questions():
    """
    Obtém o número de questões configurado para o teste.
    
    Returns:
        int: Número de questões (padrão 40)
    """
    try:
        client = get_supabase_client()
        result = client.table("exam_config").select("config_value").eq("config_key", "num_questions").execute()
        
        if result.data and len(result.data) > 0:
            num_str = result.data[0].get('config_value')
            if num_str:
                return int(num_str)
        return 40  # Padrão
    except Exception as e:
        st.error(f"Erro ao buscar número de questões: {e}")
        return 40


def set_num_questions(num_questions):
    """
    Define o número de questões do teste.
    
    Args:
        num_questions: int (número de questões, entre 1 e 40)
    
    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        client = get_supabase_client()
        
        # Validar número de questões
        num_questions = max(1, min(40, int(num_questions)))
        
        # Verificar se já existe
        existing = client.table("exam_config").select("id").eq("config_key", "num_questions").execute()
        
        if existing.data and len(existing.data) > 0:
            # Atualizar se já existe
            result = client.table("exam_config").update({
                "config_value": str(num_questions),
                "updated_at": datetime.now().isoformat()
            }).eq("config_key", "num_questions").execute()
        else:
            # Inserir se não existe
            result = client.table("exam_config").insert({
                "config_key": "num_questions",
                "config_value": str(num_questions),
                "updated_at": datetime.now().isoformat()
            }).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao definir número de questões: {e}")
        return False

def get_all_sessions() -> pd.DataFrame:
    """
    Recupera todas as sessões de todos os alunos.
    
    Returns:
        pd.DataFrame: DataFrame com todas as sessões
    """
    try:
        client = get_supabase_client()
        if not client:
            return pd.DataFrame()
        
        result = client.table("sessions").select("*").order("started_at", desc=True).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            return df
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao recuperar sessões: {e}")
        return pd.DataFrame()


def get_all_responses() -> pd.DataFrame:
    """
    Recupera todas as respostas de todos os alunos.
    
    Returns:
        pd.DataFrame: DataFrame com todas as respostas
    """
    try:
        client = get_supabase_client()
        if not client:
            return pd.DataFrame()
        
        result = client.table("responses").select("*").order("timestamp", desc=True).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            return df
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao recuperar todas as respostas: {e}")
        return pd.DataFrame()


def check_existing_session(student_name: str) -> Optional[Tuple[str, int]]:
    """
    Verifica se um aluno tem sessão incompleta.
    
    Args:
        student_name: Nome do aluno
    
    Returns:
        Optional[Tuple[str, int]]: (student_id, número de questões respondidas) ou None
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        result = client.table("sessions").select("*").eq("student_name", student_name).eq("status", "in_progress").execute()
        
        if result.data and len(result.data) > 0:
            session = result.data[0]
            student_id = session['student_id']
            
            # Contar quantas questões já foram respondidas
            responses_df = get_student_responses(student_id)
            num_answered = len(responses_df)
            
            return (student_id, num_answered)
        
        return None
        
    except Exception as e:
        st.error(f"Erro ao verificar sessão existente: {e}")
        return None


def get_exam_deadline():
    """
    Obtém o horário limite da prova.
    
    Returns:
        datetime or None: Horário limite da prova (timezone-aware) ou None se não definido
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
            
        result = client.table("exam_config").select("config_value").eq("config_key", "exam_deadline").execute()
        
        if result.data and len(result.data) > 0:
            deadline_str = result.data[0].get('config_value')
            if deadline_str:
                return datetime.fromisoformat(deadline_str)
        return None
    except Exception as e:
        st.error(f"Erro ao buscar deadline: {e}")
        return None


def get_exam_start():
    """
    Obtém o horário de início da prova.
    
    Returns:
        datetime or None: Horário de início da prova (timezone-aware) ou None se não definido
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
            
        result = client.table("exam_config").select("config_value").eq("config_key", "exam_start").execute()
        
        if result.data and len(result.data) > 0:
            start_str = result.data[0].get('config_value')
            if start_str:
                return datetime.fromisoformat(start_str)
        return None
    except Exception as e:
        st.error(f"Erro ao buscar horário de início: {e}")
        return None


def set_exam_deadline(deadline_datetime):
    """
    Define o horário limite da prova.
    
    Args:
        deadline_datetime: datetime object (timezone-aware) ou None para remover deadline
    
    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # Converter datetime para string ISO ou None
        deadline_str = deadline_datetime.isoformat() if deadline_datetime else None
        
        # Atualizar ou inserir
        result = client.table("exam_config").update({
            "config_value": deadline_str,
            "updated_at": datetime.now().isoformat()
        }).eq("config_key", "exam_deadline").execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao definir deadline: {e}")
        return False


def set_exam_start(start_datetime):
    """
    Define o horário de início da prova.
    
    Args:
        start_datetime: datetime object (timezone-aware) ou None para remover horário de início
    
    Returns:
        bool: True se sucesso, False se erro
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # Converter datetime para string ISO ou None
        start_str = start_datetime.isoformat() if start_datetime else None
        
        # Verificar se já existe
        existing = client.table("exam_config").select("id").eq("config_key", "exam_start").execute()
        
        if existing.data and len(existing.data) > 0:
            # Atualizar se já existe
            result = client.table("exam_config").update({
                "config_value": start_str,
                "updated_at": datetime.now().isoformat()
            }).eq("config_key", "exam_start").execute()
        else:
            # Inserir se não existe
            result = client.table("exam_config").insert({
                "config_key": "exam_start",
                "config_value": start_str,
                "updated_at": datetime.now().isoformat()
            }).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao definir horário de início: {e}")
        return False
