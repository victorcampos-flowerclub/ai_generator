#!/usr/bin/env python3
"""
API Backend para Backoffice do Agente Flor
"""

import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google.cloud import bigquery

app = Flask(__name__)
CORS(app)

PROJECT_ID = 'flower-ai-generator'
AGENT_ID = 'flor-cto'
AGENT_URL = 'https://flor-intelligent-365442086139.southamerica-east1.run.app'

class AgentAdmin:
    def __init__(self):
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        
    def get_agent_config(self):
        try:
            query = f"""
            SELECT * FROM `{PROJECT_ID}.ai_generator_metadata.agents`
            WHERE agent_id = '{AGENT_ID}'
            """
            
            result = list(self.bq_client.query(query))
            if result:
                agent = result[0]
                return {
                    'agent_name': agent.agent_name,
                    'agent_type': agent.agent_type,
                    'specialization': agent.specialization,
                    'status': agent.status
                }
            return None
        except Exception as e:
            print(f"Erro: {e}")
            return None
    
    def test_agent(self, message):
        try:
            response = requests.post(f'{AGENT_URL}/chat', 
                json={'message': message, 'conversation_id': 'admin-test'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Erro HTTP {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}

admin = AgentAdmin()

@app.route('/')
def admin_panel():
    return send_from_directory('.', 'agent_admin.html')

@app.route('/api/config')
def get_config():
    config = admin.get_agent_config()
    if config:
        return jsonify(config)
    else:
        return jsonify({'error': 'Não encontrado'}), 404

@app.route('/api/test', methods=['POST'])
def test_agent():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Mensagem obrigatória'}), 400
        
        result = admin.test_agent(message)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Iniciando Backoffice - Agente Flor")
    print("URL: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
