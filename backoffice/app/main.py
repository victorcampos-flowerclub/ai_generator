import os
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from google.cloud import bigquery, storage, run_v2, secretmanager
import anthropic
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configurações
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'flower-ai-generator')
REGION = 'southamerica-east1'
BUCKET_NAME = f'{PROJECT_ID}-agents-docs'

# Clientes Google Cloud
bq_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
run_client = run_v2.ServicesClient()
secret_client = secretmanager.SecretManagerServiceClient()

def get_claude_api_key():
    """Recupera a API key do Claude do Secret Manager"""
    name = f"projects/{PROJECT_ID}/secrets/claude-api-key/versions/latest"
    response = secret_client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

@app.route('/')
def index():
    """Página principal do backoffice"""
    # Buscar todos os agentes
    query = """
    SELECT agent_id, agent_name, agent_type, status, created_at, cloud_run_url
    FROM `{}.ai_generator_metadata.agents`
    ORDER BY created_at DESC
    """.format(PROJECT_ID)
    
    agents = []
    for row in bq_client.query(query):
        agents.append({
            'agent_id': row.agent_id,
            'agent_name': row.agent_name,
            'agent_type': row.agent_type,
            'status': row.status,
            'created_at': row.created_at,
            'cloud_run_url': row.cloud_run_url
        })
    
    return render_template('index.html', agents=agents)

@app.route('/create-agent')
def create_agent_form():
    """Formulário para criar novo agente"""
    return render_template('create_agent.html')

@app.route('/agent/<agent_id>')
def agent_detail(agent_id):
    """Detalhes de um agente específico"""
    # Buscar dados do agente
    query = """
    SELECT * FROM `{}.ai_generator_metadata.agents`
    WHERE agent_id = @agent_id
    """.format(PROJECT_ID)
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("agent_id", "STRING", agent_id)]
    )
    
    results = list(bq_client.query(query, job_config=job_config))
    if not results:
        flash('Agente não encontrado', 'error')
        return redirect(url_for('index'))
    
    agent = results[0]
    
    # Buscar documentos do agente
    docs_query = """
    SELECT document_id, document_name, document_type, upload_date, processing_status
    FROM `{}.ai_generator_metadata.agent_documents`
    WHERE agent_id = @agent_id
    ORDER BY upload_date DESC
    """.format(PROJECT_ID)
    
    documents = list(bq_client.query(docs_query, job_config=job_config))
    
    return render_template('agent_detail.html', agent=agent, documents=documents)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
