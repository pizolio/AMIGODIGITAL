import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CONFIGURAÇÃO DE CORS ATUALIZADA E CORRIGIDA
# Agora aceita as duas origens mais comuns para o seu frontend
origins = ["http://localhost:8000", "http://127.0.0.1:5500"]
CORS(app, resources={r"/api/*": {"origins": origins}})

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route("/api/categories", methods=['GET'])
def get_categories():
    response = supabase.table('categories').select('*').execute()
    return jsonify(response.data)

# (O resto das suas rotas continua igual)
@app.route("/api/tutorials", methods=['GET'])
def get_tutorials_by_category():
    category_id = request.args.get('category_id')
    response = supabase.table('tutorials').select('*').eq('category_id', category_id).execute()
    return jsonify(response.data)

@app.route("/api/tutorial", methods=['GET'])
def get_tutorial_details():
    tutorial_id = request.args.get('id')
    response = supabase.table('tutorials').select('*').eq('id', tutorial_id).single().execute()
    return jsonify(response.data)


if __name__ == '__main__':
    # Garanta que a porta é a 5001
    app.run(debug=True, port=5001)