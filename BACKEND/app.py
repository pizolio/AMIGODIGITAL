import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env para o desenvolvimento local
load_dotenv()

# --- 1. Inicialização e Configuração do CORS ---
app = Flask(__name__)

# Configuração de CORS simplificada e robusta para permitir acesso de QUALQUER origem.
# Esta é a forma mais direta e garantida de resolver os erros de CORS.
CORS(app)

# --- 2. Conexão com o Supabase ---
supabase = None
try:
    # Busca as credenciais a partir das variáveis de ambiente (essencial para o Render)
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    # Garante que as variáveis foram encontradas
    if not supabase_url or not supabase_key:
        raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.")
    
    # Cria o cliente de conexão
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✅ Conexão com o Supabase estabelecida com sucesso.")

except Exception as e:
    print(f"❌ ERRO CRÍTICO: Não foi possível conectar ao Supabase. Erro: {e}")


# --- 3. Rotas da API ---

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
        # A função .single() pode gerar um erro se nenhum item for encontrado.
        # Este 'try...except' captura esse erro e retorna uma mensagem 404 amigável.
        response = supabase.table('tutorials').select('*').eq('id', tutorial_id).single().execute()
        return jsonify(response.data)
    except Exception as e:
        print(f"Alerta: Tentativa de acesso a tutorial inexistente (ID: {tutorial_id}). Erro: {e}")
        return jsonify(error=f"Tutorial com ID {tutorial_id} não foi encontrado."), 404

@app.route("/api/suggestions", methods=['GET'])
def get_suggestions():
    """Retorna todas as sugestões, ordenadas por votos."""
    response = supabase.table('suggestions').select('*').order('votes', desc=True).execute()
    return jsonify(response.data)

@app.route("/api/suggestions", methods=['POST'])
def add_suggestion():
    """Adiciona uma nova sugestão. A segurança é garantida pela RLS do Supabase."""
    data = request.json
    if not data or 'content' not in data:
        return jsonify(error="O campo 'content' é obrigatório"), 400

    # A segurança é garantida pela política de RLS (Row Level Security) no Supabase,
    # que só permite a inserção por usuários autenticados.
    response = supabase.table('suggestions').insert({
        'content': data['content']
    }).execute()
    return jsonify(response.data), 201

# --- 4. Inicializador para Execução Local ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)

