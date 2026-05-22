"""
Módulo de gerenciamento de banco de dados usando Google Sheets.
Salva respostas dos alunos e permite recuperação de dados para análise.
"""

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json


def get_google_sheets_client():
    """
    Conecta ao Google Sheets usando credenciais do Streamlit secrets.
    
    Returns:
        gspread.Client: Cliente autenticado do Google Sheets
    """
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Carregar credenciais dos secrets
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, scope
        )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return None


def get_or_create_worksheet(client, sheet_id: str, worksheet_name: str):
    """
    Obtém ou cria uma worksheet no Google Sheets.
    
    Args:
        client: Cliente do Google Sheets
        sheet_id: ID da planilha
        worksheet_name: Nome da worksheet
    
    Returns:
        gspread.Worksheet: Worksheet solicitada
    """
    try:
        spreadsheet = client.open_by_key(sheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Criar worksheet se não existir
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, 
                rows="1000", 
                cols="20"
            )
            
            # Adicionar cabeçalhos
            if worksheet_name == "responses":
                headers = [
                    "student_id", "student_name", "question_id", 
                    "answer", "is_correct", "is_timeout", 
                    "timestamp", "theta_estimate"
                ]
                worksheet.append_row(headers)
            elif worksheet_name == "sessions":
                headers = [
                    "student_id", "student_name", "started_at", 
                    "completed_at", "final_theta", "total_correct", 
                    "total_timeout", "status"
                ]
                worksheet.append_row(headers)
        
        return worksheet
    except Exception as e:
        st.error(f"Erro ao acessar worksheet '{worksheet_name}': {e}")
        return None


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
    Salva uma resposta individual no Google Sheets.
    
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
        client = get_google_sheets_client()
        if not client:
            return False
        
        sheet_id = st.secrets["sheet_id"]
        worksheet = get_or_create_worksheet(client, sheet_id, "responses")
        
        if not worksheet:
            return False
        
        timestamp = datetime.now().isoformat()
        
        row = [
            student_id,
            student_name,
            question_id,
            answer if answer else "",
            str(is_correct),
            str(is_timeout),
            timestamp,
            str(theta_estimate)
        ]
        
        worksheet.append_row(row)
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
        client = get_google_sheets_client()
        if not client:
            return False
        
        sheet_id = st.secrets["sheet_id"]
        worksheet = get_or_create_worksheet(client, sheet_id, "sessions")
        
        if not worksheet:
            return False
        
        started_at = datetime.now().isoformat()
        
        row = [
            student_id,
            student_name,
            started_at,
            "",  # completed_at (será preenchido depois)
            "",  # final_theta
            "",  # total_correct
            "",  # total_timeout
            "in_progress"
        ]
        
        worksheet.append_row(row)
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
        client = get_google_sheets_client()
        if not client:
            return False
        
        sheet_id = st.secrets["sheet_id"]
        worksheet = get_or_create_worksheet(client, sheet_id, "sessions")
        
        if not worksheet:
            return False
        
        # Buscar a linha do aluno
        records = worksheet.get_all_records()
        for idx, record in enumerate(records):
            if record['student_id'] == student_id and record['status'] == 'in_progress':
                row_num = idx + 2  # +2 porque começa em 1 e tem cabeçalho
                
                completed_at = datetime.now().isoformat()
                
                worksheet.update_cell(row_num, 4, completed_at)  # completed_at
                worksheet.update_cell(row_num, 5, str(final_theta))  # final_theta
                worksheet.update_cell(row_num, 6, str(total_correct))  # total_correct
                worksheet.update_cell(row_num, 7, str(total_timeout))  # total_timeout
                worksheet.update_cell(row_num, 8, "completed")  # status
                
                return True
        
        return False
        
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
        client = get_google_sheets_client()
        if not client:
            return pd.DataFrame()
        
        sheet_id = st.secrets["sheet_id"]
        worksheet = get_or_create_worksheet(client, sheet_id, "responses")
        
        if not worksheet:
            return pd.DataFrame()
        
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        if df.empty:
            return df
        
        # Filtrar por student_id
        df = df[df['student_id'] == student_id]
        
        # Converter tipos
        df['is_correct'] = df['is_correct'].astype(str).str.lower() == 'true'
        df['is_timeout'] = df['is_timeout'].astype(str).str.lower() == 'true'
        df['theta_estimate'] = pd.to_numeric(df['theta_estimate'], errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao recuperar respostas: {e}")
        return pd.DataFrame()


def get_all_sessions() -> pd.DataFrame:
    """
    Recupera todas as sessões de todos os alunos.
    
    Returns:
        pd.DataFrame: DataFrame com todas as sessões
    """
    try:
        client = get_google_sheets_client()
        if not client:
            return pd.DataFrame()
        
        sheet_id = st.secrets["sheet_id"]
        worksheet = get_or_create_worksheet(client, sheet_id, "sessions")
        
        if not worksheet:
            return pd.DataFrame()
        
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        if df.empty:
            return df
        
        # Converter tipos
        df['final_theta'] = pd.to_numeric(df['final_theta'], errors='coerce')
        df['total_correct'] = pd.to_numeric(df['total_correct'], errors='coerce')
        df['total_timeout'] = pd.to_numeric(df['total_timeout'], errors='coerce')
        
        return df
        
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
        client = get_google_sheets_client()
        if not client:
            return pd.DataFrame()
        
        sheet_id = st.secrets["sheet_id"]
        worksheet = get_or_create_worksheet(client, sheet_id, "responses")
        
        if not worksheet:
            return pd.DataFrame()
        
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        if df.empty:
            return df
        
        # Converter tipos
        df['is_correct'] = df['is_correct'].astype(str).str.lower() == 'true'
        df['is_timeout'] = df['is_timeout'].astype(str).str.lower() == 'true'
        df['theta_estimate'] = pd.to_numeric(df['theta_estimate'], errors='coerce')
        
        return df
        
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
        client = get_google_sheets_client()
        if not client:
            return None
        
        sheet_id = st.secrets["sheet_id"]
        worksheet = get_or_create_worksheet(client, sheet_id, "sessions")
        
        if not worksheet:
            return None
        
        records = worksheet.get_all_records()
        
        for record in records:
            if (record['student_name'].lower() == student_name.lower() and 
                record['status'] == 'in_progress'):
                
                student_id = record['student_id']
                
                # Contar quantas questões já foram respondidas
                responses_df = get_student_responses(student_id)
                num_answered = len(responses_df)
                
                return (student_id, num_answered)
        
        return None
        
    except Exception as e:
        st.error(f"Erro ao verificar sessão existente: {e}")
        return None
