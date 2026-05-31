"""
Script para criar secrets.toml local para testes.
Execute: python setup_local.py
"""

import os

secrets_content = '''# Configuração local para testes
# NÃO COMMITAR ESTE ARQUIVO!

# Senha do painel administrativo
admin_password = "admin123"

# ID da planilha (fake para testes locais)
sheet_id = "fake_sheet_id_for_local_testing"

# Credenciais fake para testes locais (não funcionarão com Google Sheets)
[gcp_service_account]
type = "service_account"
project_id = "test-project"
private_key_id = "test-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\\nTEST\\n-----END PRIVATE KEY-----\\n"
client_email = "test@test-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/test"
'''

def setup_local():
    """Cria arquivo secrets.toml para desenvolvimento local."""
    
    # Criar diretório .streamlit se não existir
    os.makedirs('.streamlit', exist_ok=True)
    
    secrets_path = '.streamlit/secrets.toml'
    
    if os.path.exists(secrets_path):
        response = input(f"{secrets_path} já existe. Sobrescrever? (s/n): ")
        if response.lower() != 's':
            print("Operação cancelada.")
            return
    
    # Escrever arquivo
    with open(secrets_path, 'w', encoding='utf-8') as f:
        f.write(secrets_content)
    
    print(f"✅ Arquivo {secrets_path} criado com sucesso!")
    print("\n⚠️  ATENÇÃO:")
    print("Este arquivo contém credenciais FAKE para testes locais.")
    print("Para usar Google Sheets em produção, configure credenciais reais.")
    print("\n📝 Próximos passos:")
    print("1. Execute: streamlit run app.py")
    print("2. Para login admin use: admin123")
    print("3. Funcionalidades de banco de dados NÃO funcionarão sem Google Sheets real")

if __name__ == "__main__":
    setup_local()
