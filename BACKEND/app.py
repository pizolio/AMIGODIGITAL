import os
from functools import wraps
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuração de CORS segura, permitindo seus ambientes de dev e produção
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "https://amigodigital.netlify.app"
]
CORS(app, resources={r"/api/*": {"origins": origins}})

# --- Conexão com o Supabase ---
supabase = None
try:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são necessárias.")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Conexão com Supabase estabelecida.")
except Exception as e:
    print(f"Erro ao conectar com Supabase: {e}")

# <<< NOVO >>> Roda ANTES de cada requisição para checar a conexão com o DB
@app.before_request
def before_request_func():
    if not supabase:
        return jsonify(error="Conexão com o banco de dados não disponível."), 503

# <<< NOVO >>> Decorator para proteger rotas que exigem autenticação
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify(error="Token de autenticação ausente ou mal formatado."), 401
        
        jwt = auth_header.split(' ')[1]
        try:
            user_response = supabase.auth.get_user(jwt)
            g.user = user_response.user # Armazena o usuário no contexto da requisição
        except Exception as e:
            return jsonify(error=f"Token inválido ou expirado: {e}"), 401
        
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas Públicas da API ---

@app.route("/api/categories", methods=['GET'])
def get_categories():
    """Retorna todas as categorias."""
    response = supabase.table('categories').select('*').order('id').execute()
    return jsonify(response.data)

@app.route("/api/tutorials", methods=['GET'])
def get_tutorials_by_category():
    """Retorna tutoriais filtrados por um 'category_id'."""
    category_id = request.args.get('category_id')
    if not category_id: return jsonify(error="'category_id' é obrigatório"), 400
    response = supabase.table('tutorials').select('*').eq('category_id', category_id).execute()
    return jsonify(response.data)

@app.route("/api/tutorial", methods=['GET'])
def get_tutorial_details():
    """Retorna os detalhes de um único tutorial pelo seu 'id'."""
    tutorial_id = request.args.get('id')
    if not tutorial_id: return jsonify(error="'id' é obrigatório"), 400
    response = supabase.table('tutorials').select('*').eq('id', tutorial_id).single().execute()
    return jsonify(response.data)

@app.route("/api/suggestions", methods=['GET'])
def get_suggestions():
    """Retorna todas as sugestões, ordenadas por votos."""
    response = supabase.table('suggestions').select('*').order('votes', desc=True).execute()
    return jsonify(response.data)


# --- Rotas Protegidas da API (Exigem Login) ---

@app.route("/api/suggestions", methods=['POST'])
@token_required # <<< MUDANÇA: Rota agora protegida
def add_suggestion():
    """Cria uma nova sugestão para o usuário autenticado."""
    data = request.json
    if not data or 'content' not in data:
        return jsonify(error="O campo 'content' é obrigatório"), 400
    
    user = g.user # Pega o usuário validado pelo decorator
    
    # Inserção explícita do user_id para maior segurança
    response = supabase.table('suggestions').insert({
        'content': data['content'],
        'user_id': user.id
    }).execute()
    
    return jsonify(response.data), 201

@app.route("/api/help_requests", methods=['POST'])
@token_required # <<< MUDANÇA: Rota agora protegida
def add_help_request():
    """Cria um novo pedido de ajuda para o usuário autenticado."""
    data = request.json
    if not data or 'message' not in data:
        return jsonify(error="O campo 'message' é obrigatório"), 400
    
    user = g.user # Pega o usuário validado pelo decorator

    response = supabase.table('help_requests').insert({
        'message': data['message'],
        'user_id': user.id
    }).execute()
    
    return jsonify(response.data), 201

if __name__ == '__main__':
    app.run(debug=True, port=5001)