import os
from functools import wraps
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env para o desenvolvimento local
load_dotenv()

# --- 1. Inicialização e Configuração do CORS ---
app = Flask(__name__)

# Configuração de CORS simplificada para permitir acesso de QUALQUER origem.
CORS(app)

# --- 2. Conexão com o Supabase ---
supabase = None
try:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Conexão com o Supabase estabelecida com sucesso.")

except Exception as e:
    print(f"❌ ERRO CRÍTICO: Não foi possível conectar ao Supabase. Erro: {e}")


# --- 3. Segurança: Verificador de Token de Autenticação ---
def token_required(f):
    """Um decorator para garantir que a rota seja acessada apenas por usuários logados."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify(error="Token de autenticação ausente ou mal formatado."), 401
        
        jwt = auth_header.split(' ')[1]
        try:
            # Valida o token com o Supabase
            user_response = supabase.auth.get_user(jwt)
            # Armazena os dados do usuário no contexto 'g' para uso na rota
            g.user = user_response.user
        except Exception as e:
            return jsonify(error=f"Token inválido ou expirado."), 401
        
        return f(*args, **kwargs)
    return decorated_function


# --- 4. Rotas Públicas da API (Qualquer um pode ver) ---

@app.route("/")
def index():
    """Rota de verificação para confirmar que a API está no ar."""
    return "A API do Amigo Digital está funcionando!"

@app.route("/api/categories", methods=['GET'])
def get_categories():
    """Retorna todas as categorias, ordenadas por ID."""
    response = supabase.table('categories').select('*').order('id').execute()
    return jsonify(response.data)

@app.route("/api/tutorials", methods=['GET'])
def get_tutorials_by_category():
    """Retorna tutoriais filtrados por um 'category_id'."""
    category_id = request.args.get('category_id')
    if not category_id:
        return jsonify(error="'category_id' é um parâmetro obrigatório"), 400
    
    response = supabase.table('tutorials').select('*').eq('category_id', category_id).execute()
    return jsonify(response.data)

@app.route("/api/tutorial", methods=['GET'])
def get_tutorial_details():
    """Retorna os detalhes de um único tutorial pelo seu 'id'."""
    tutorial_id = request.args.get('id')
    if not tutorial_id:
        return jsonify(error="'id' é um parâmetro obrigatório"), 400
    
    try:
        response = supabase.table('tutorials').select('*').eq('id', tutorial_id).single().execute()
        if not response.data:
             raise Exception("Nenhum dado retornado para este ID.")
        return jsonify(response.data)
    except Exception as e:
        print(f"Alerta: Tentativa de acesso a tutorial inexistente (ID: {tutorial_id}). Erro: {e}")
        return jsonify(error=f"Tutorial com ID {tutorial_id} não foi encontrado."), 404

@app.route("/api/suggestions", methods=['GET'])
def get_suggestions():
    """Retorna todas as sugestões, ordenadas por votos."""
    response = supabase.table('suggestions').select('*').order('votes', desc=True).execute()
    return jsonify(response.data)


# --- 5. Rotas Protegidas da API (Exigem Login) ---

@app.route("/api/suggestions", methods=['POST'])
@token_required
def add_suggestion():
    """Adiciona uma nova sugestão. A segurança é garantida pelo token."""
    data = request.json
    if not data or 'content' not in data:
        return jsonify(error="O campo 'content' é obrigatório"), 400

    response = supabase.table('suggestions').insert({
        'content': data['content']
    }).execute()
    return jsonify(response.data), 201

@app.route("/api/tutorials", methods=['POST'])
@token_required
def create_tutorial():
    """Cria um novo tutorial. Rota protegida."""
    data = request.json
    # Validação simples dos campos necessários
    required_fields = ['title', 'description', 'category_id', 'content']
    if not all(field in data for field in required_fields):
        return jsonify(error="Campos 'title', 'description', 'category_id', e 'content' são obrigatórios."), 400

    # Opcional: Adicionar o ID do autor do tutorial no futuro
    # 'author_id': g.user.id 
    response = supabase.table('tutorials').insert({
        'title': data['title'],
        'description': data['description'],
        'category_id': data['category_id'],
        'content': data['content']
    }).execute()

    return jsonify(response.data), 201


# --- 6. Inicializador para Execução Local ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)

