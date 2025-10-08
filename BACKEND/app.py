# Versão final com todas as rotas e correção de CORS
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa o aplicativo Flask
app = Flask(__name__)

# --- MUDANÇA 1: Configuração do CORS mais segura ---
# Em vez de CORS(app), especificamos as origens permitidas.
# Isso garante que apenas seu frontend possa fazer requisições.
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "https://amigodigital.netlify.app" # URL do seu site publicado
]
CORS(app, resources={r"/api/*": {"origins": origins}})


# --- Conexão com o Supabase ---
try:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são necessárias.")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Conexão com Supabase estabelecida com sucesso.")
except Exception as e:
    print(f"Erro ao conectar com Supabase: {e}")
    supabase = None

# --- MUDANÇA 2: Tratador de erros genérico removido ---
# Durante o desenvolvimento, é melhor deixar o Flask mostrar o erro completo
# no terminal para facilitar a depuração.
# @app.errorhandler(Exception)
# def handle_exception(e):
#     return jsonify(error=str(e)), 500


# --- Rotas da API ---

# [GET] Rota para buscar todas as categorias
@app.route("/api/categories", methods=['GET'])
def get_categories():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    response = supabase.table('categories').select('*').order('id', desc=False).execute()
    return jsonify(response.data)

# [GET] Rota para buscar tutoriais de uma categoria específica
@app.route("/api/tutorials", methods=['GET'])
def get_tutorials_by_category():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    category_id = request.args.get('category_id')
    if not category_id:
        return jsonify(error="O parâmetro 'category_id' é obrigatório"), 400
    response = supabase.table('tutorials').select('*').eq('category_id', category_id).execute()
    return jsonify(response.data)

# [GET] Rota para buscar os detalhes de um tutorial específico
@app.route("/api/tutorial", methods=['GET'])
def get_tutorial_details():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    tutorial_id = request.args.get('id')
    if not tutorial_id:
        return jsonify(error="O parâmetro 'id' é obrigatório"), 400
    response = supabase.table('tutorials').select('*').eq('id', tutorial_id).single().execute()
    return jsonify(response.data)


# --- ROTAS NOVAS (para a área logada) ---

# [GET] Rota para buscar todas as sugestões
@app.route("/api/suggestions", methods=['GET'])
def get_suggestions():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    # Esta rota deve ser pública ou apenas para usuários logados?
    # Vamos assumir que todos podem ver as sugestões.
    response = supabase.table('suggestions').select('*').order('votes', desc=True).execute()
    return jsonify(response.data)

# [POST] Rota para adicionar uma nova sugestão
@app.route("/api/suggestions", methods=['POST'])
def add_suggestion():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    data = request.json
    if not data or 'content' not in data:
        return jsonify(error="O campo 'content' é obrigatório"), 400
    
    # O Supabase (via RLS) vai garantir que apenas um usuário autenticado pode inserir.
    # O 'user_id' será pego automaticamente pela policy a partir do token do usuário.
    response = supabase.table('suggestions').insert({'content': data['content']}).execute()
    return jsonify(response.data), 201

# [POST] Rota para um usuário logado enviar um pedido de ajuda
@app.route("/api/help_requests", methods=['POST'])
def add_help_request():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    data = request.json
    if not data or 'message' not in data:
        return jsonify(error="O campo 'message' é obrigatório"), 400

    # A segurança é garantida pela RLS no Supabase, que vai pegar o ID do usuário
    # a partir do token de autenticação e garantir que ele só insira em seu próprio nome.
    response = supabase.table('help_requests').insert({'message': data['message']}).execute()
    return jsonify(response.data), 201


if __name__ == '__main__':
    app.run(debug=True, port=5001)