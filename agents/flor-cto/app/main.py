import os
import re
import requests
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google.cloud import secretmanager

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

PROJECT_ID = 'flower-ai-generator'
FLOWER_API_URL = 'https://flower-club-api-v467-486142715688.southamerica-east1.run.app'
FLOWER_API_KEY = 'flowerclub2025'

def get_claude_api_key():
    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/claude-api-key/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Erro ao obter API key: {e}")
        return None

def detect_and_search_client(user_message):
    """CORREÇÃO: Detecta CPF (11 dígitos) ou customer_id (6-9 dígitos)"""
    try:
        headers = {'Authorization': f'Bearer {FLOWER_API_KEY}'}
        
        # CPF (11 dígitos)
        cpf_match = re.search(r'\b\d{11}\b', user_message)
        if cpf_match:
            cpf = cpf_match.group()
            response = requests.get(f'{FLOWER_API_URL}/busca-cliente/{cpf}', headers=headers, timeout=30)
            if response.status_code == 200:
                return {"type": "CPF", "data": response.json()}
        
        # Customer ID (6-9 dígitos)  
        id_match = re.search(r'\b\d{6,9}\b', user_message)
        if id_match:
            customer_id = id_match.group()
            response = requests.get(f'{FLOWER_API_URL}/cliente-completo/{customer_id}', headers=headers, timeout=30)
            if response.status_code == 200:
                return {"type": "ID", "data": response.json()}
        
        return None
    except Exception as e:
        return None

def call_claude_api(api_key, system_prompt, user_message):
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }
        
        response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            return f"Erro API Claude: {response.status_code}"
    except Exception as e:
        return f"Erro: {str(e)}"

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/health')
def health():
    return {"status": "ok", "agent": "Flor CTO AI", "version": "3.4", "cors_enabled": True}

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return {'status': 'ok'}
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Mensagem obrigatória'}), 400
        
        api_key = get_claude_api_key()
        if not api_key:
            return jsonify({'error': 'API key não encontrada'}), 500
            
        # BUSCA CORRIGIDA
        search_result = detect_and_search_client(user_message)
        context = ""
        
        if search_result:
            context = f"\n\nDADOS REAIS ({search_result['type']}):\n{json.dumps(search_result['data'], indent=2, ensure_ascii=False)}"
        
        system_prompt = f"""Você é Flor, CTO Flower Club Enterprise API v4.6.7.

EXPERTISE:
- 25 endpoints funcionais (100% operacional)
- 10.177 clientes ativos
- BigQuery (7 projetos)
- Sistema FIFO + cortesias Pipefy
- Performance < 20s todos endpoints

Responda como CTO expert.{context}"""

        response = call_claude_api(api_key, system_prompt, user_message)
        
        return jsonify({
            'response': response,
            'has_real_data': bool(search_result),
            'agent_name': 'Flor CTO AI',
            'version': '3.4',
            'cors_enabled': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)[:100]}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
