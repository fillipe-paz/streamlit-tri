"""
Script de teste rápido para verificar conexão com Supabase.
Execute: python test_supabase.py
"""

import streamlit as st
from supabase import create_client


def test_connection():
    """Testa a conexão com Supabase."""
    print("=" * 60)
    print("🧪 TESTE DE CONEXÃO COM SUPABASE")
    print("=" * 60)
    
    try:
        # Tentar carregar secrets
        print("\n1️⃣ Carregando credenciais...")
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        print(f"   ✅ URL: {url}")
        print(f"   ✅ Key: {key[:20]}...{key[-20:]}")
        
    except Exception as e:
        print(f"   ❌ Erro ao carregar secrets: {e}")
        print("\n💡 SOLUÇÃO:")
        print("   1. Crie o arquivo .streamlit/secrets.toml")
        print("   2. Adicione as credenciais do Supabase")
        print("   3. Veja: SETUP_SUPABASE.md")
        return False
    
    try:
        # Tentar conectar
        print("\n2️⃣ Conectando ao Supabase...")
        client = create_client(url, key)
        print("   ✅ Cliente criado com sucesso")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar cliente: {e}")
        return False
    
    try:
        # Tentar listar tabelas
        print("\n3️⃣ Testando acesso às tabelas...")
        
        # Testar tabela sessions
        result = client.table("sessions").select("*").limit(1).execute()
        print(f"   ✅ Tabela 'sessions' acessível ({len(result.data)} registros)")
        
        # Testar tabela responses
        result = client.table("responses").select("*").limit(1).execute()
        print(f"   ✅ Tabela 'responses' acessível ({len(result.data)} registros)")
        
    except Exception as e:
        print(f"   ❌ Erro ao acessar tabelas: {e}")
        print("\n💡 POSSÍVEIS CAUSAS:")
        print("   - Tabelas não foram criadas")
        print("   - Execute o SQL no Supabase SQL Editor")
        print("   - Veja: SETUP_SUPABASE.md (Passo 3)")
        return False
    
    try:
        # Tentar inserir um registro de teste
        print("\n4️⃣ Testando inserção de dados...")
        
        test_data = {
            "student_id": "test_connection_123",
            "student_name": "Teste de Conexão",
            "status": "in_progress"
        }
        
        result = client.table("sessions").insert(test_data).execute()
        print("   ✅ Inserção bem-sucedida")
        
        # Deletar o registro de teste
        print("\n5️⃣ Limpando dados de teste...")
        client.table("sessions").delete().eq("student_id", "test_connection_123").execute()
        print("   ✅ Dados de teste removidos")
        
    except Exception as e:
        print(f"   ❌ Erro ao inserir dados: {e}")
        print("\n💡 POSSÍVEIS CAUSAS:")
        print("   - Políticas RLS (Row Level Security) muito restritivas")
        print("   - Execute as policies no SQL (veja SETUP_SUPABASE.md)")
        return False
    
    # Sucesso!
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)
    print("\n🎉 Supabase está configurado corretamente!")
    print("   Você pode executar: streamlit run app.py")
    return True


def show_current_data():
    """Mostra dados atuais nas tabelas."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        client = create_client(url, key)
        
        print("\n" + "=" * 60)
        print("📊 DADOS ATUAIS NO BANCO")
        print("=" * 60)
        
        # Contar sessões
        sessions = client.table("sessions").select("*").execute()
        print(f"\n📝 Sessões: {len(sessions.data)} registros")
        if sessions.data:
            print("   Últimas 5:")
            for session in sessions.data[:5]:
                print(f"   - {session['student_name']} ({session['status']})")
        
        # Contar respostas
        responses = client.table("responses").select("*").execute()
        print(f"\n✅ Respostas: {len(responses.data)} registros")
        if responses.data:
            print(f"   Primeira: {responses.data[0]['student_name']} - Q{responses.data[0]['question_id']}")
            print(f"   Última: {responses.data[-1]['student_name']} - Q{responses.data[-1]['question_id']}")
        
    except Exception as e:
        print(f"\n⚠️  Não foi possível carregar dados: {e}")


if __name__ == "__main__":
    try:
        success = test_connection()
        
        if success:
            show_current_data()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
