# Versão final com todas as rotas e correção de CORS
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (ótimo para desenvolvimento local)
load_dotenv()

# Inicializa o aplicativo Flask
app = Flask(__name__)

# --- Configuração de CORS ---
# Permite que seu front-end (rodando em localhost ou em um site publicado)
# se comunique com esta API.
# O "*" é um curinga que permite qualquer origem, ideal para começar.
CORS(app)


# --- Conexão com o Supabase ---
# Pega a URL e a Chave de API do Supabase a partir das variáveis de ambiente.
# Isso é mais seguro e flexível do que colocar as chaves diretamente no código.
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


# --- Tratamento de Erros Genérico ---
# Uma boa prática para retornar erros de forma padronizada
@app.errorhandler(Exception)
def handle_exception(e):
    # Para erros mais sérios, você pode querer logar o erro aqui
    return jsonify(error=str(e)), 500


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

# --- ROTAS NOVAS ---

# [GET] Rota para buscar todas as sugestões
@app.route("/api/suggestions", methods=['GET'])
def get_suggestions():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    response = supabase.table('suggestions').select('*').order('votes', desc=True).execute()
    return jsonify(response.data)

# [POST] Rota para adicionar uma nova sugestão
@app.route("/api/suggestions", methods=['POST'])
def add_suggestion():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    data = request.json
    if not data or 'content' not in data:
        return jsonify(error="O campo 'content' é obrigatório no corpo da requisição"), 400

    # A política de RLS no Supabase garante que apenas usuários autenticados possam inserir.
    # Opcional: Você pode querer validar o token do usuário aqui para segurança extra.
    response = supabase.table('suggestions').insert({
        'content': data['content'],
        'votes': 0 # Sugestões sempre começam com 0 votos
    }).execute()
    
    return jsonify(response.data), 201

# [POST] Rota para um usuário logado enviar um pedido de ajuda
@app.route("/api/help_requests", methods=['POST'])
def add_help_request():
    if not supabase: return jsonify(error="Conexão com Supabase não disponível"), 503
    data = request.json
    # Validação dos dados recebidos
    if not data or 'message' not in data or 'user_id' not in data:
        return jsonify(error="Os campos 'message' e 'user_id' são obrigatórios"), 400

    # A política de RLS que criamos no banco de dados é a principal camada de segurança aqui.
    # Ela garante que um usuário só pode criar um pedido para si mesmo (auth.uid() == user_id).
    response = supabase.table('help_requests').insert({
        'user_id': data['user_id'],
        'message': data['message']
    }).execute()

    return jsonify(response.data), 201


if __name__ == '__main__':
    # Garante que a porta seja a 5001 para desenvolvimento local
    app.run(debug=True, port=5001)