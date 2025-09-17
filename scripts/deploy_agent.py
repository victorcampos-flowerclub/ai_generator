import os
import uuid
import shutil
import subprocess
from datetime import datetime
from google.cloud import bigquery, storage, secretmanager
import time

class AgentDeployer:
    def __init__(self, project_id, region):
        self.project_id = project_id
        self.region = region
        self.bq_client = bigquery.Client(project=project_id)
        self.storage_client = storage.Client(project=project_id)
        
    def create_agent_dataset(self, agent_id):
        """Cria dataset BigQuery específico para o agente"""
        dataset_name = f"agent_{agent_id.replace('-', '_')}"
        dataset_id = f"{self.project_id}.{dataset_name}"
        
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = self.region
        dataset.description = f"Dataset para agente {agent_id}"
        
        try:
            dataset = self.bq_client.create_dataset(dataset, timeout=30)
            print(f"✅ Dataset criado: {dataset.dataset_id}")
            
            # Criar tabelas essenciais do agente
            self._create_agent_tables(dataset_name)
            return dataset_name
            
        except Exception as e:
            print(f"❌ Erro ao criar dataset: {e}")
            return None
    
    def _create_agent_tables(self, dataset_name):
        """Cria tabelas necessárias para o agente"""
        tables = {
            'conversations': [
                bigquery.SchemaField("conversation_id", "STRING"),
                bigquery.SchemaField("user_id", "STRING"),
                bigquery.SchemaField("started_at", "TIMESTAMP"),
                bigquery.SchemaField("ended_at", "TIMESTAMP"),
                bigquery.SchemaField("status", "STRING"),
                bigquery.SchemaField("message_count", "INTEGER"),
            ],
            'messages': [
                bigquery.SchemaField("message_id", "STRING"),
                bigquery.SchemaField("conversation_id", "STRING"),
                bigquery.SchemaField("role", "STRING"),  # user, assistant
                bigquery.SchemaField("content", "STRING"),
                bigquery.SchemaField("timestamp", "TIMESTAMP"),
                bigquery.SchemaField("tokens_used", "INTEGER"),
            ],
            'documents_processed': [
                bigquery.SchemaField("document_id", "STRING"),
                bigquery.SchemaField("filename", "STRING"),
                bigquery.SchemaField("processed_at", "TIMESTAMP"),
                bigquery.SchemaField("content_summary", "STRING"),
                bigquery.SchemaField("embedding_stored", "BOOLEAN"),
            ]
        }
        
        for table_name, schema in tables.items():
            table_id = f"{self.project_id}.{dataset_name}.{table_name}"
            table = bigquery.Table(table_id, schema=schema)
            table = self.bq_client.create_table(table)
            print(f"  ✅ Tabela criada: {table_name}")
    
    def create_agent_code(self, agent_data, agent_id):
        """Cria código personalizado do agente"""
        agent_dir = f"/tmp/agent_{agent_id}"
        
        # Remover diretório se já existe
        if os.path.exists(agent_dir):
            shutil.rmtree(agent_dir)
        os.makedirs(agent_dir, exist_ok=True)
        
        # Copiar template base
        template_source = "/home/victor_campos/ai-generator-system/agent-template"
        shutil.copytree(template_source, f"{agent_dir}/agent-code", dirs_exist_ok=True)
        
        # Personalizar código com dados do agente
        self._customize_agent_code(f"{agent_dir}/agent-code", agent_data, agent_id)
        
        return f"{agent_dir}/agent-code"
    
    def _customize_agent_code(self, agent_dir, agent_data, agent_id):
        """Personaliza o código do agente com suas configurações"""
        # Substituir placeholders no main.py
        main_py_content = f'''
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from google.cloud import bigquery, secretmanager
import anthropic

app = Flask(__name__)
app.secret_key = '{str(uuid.uuid4())}'

# Configurações do agente
AGENT_ID = '{agent_id}'
AGENT_NAME = '{agent_data['agent_name']}'
AGENT_TYPE = '{agent_data['agent_type']}'
CONVERSATION_STYLE = '{agent_data['conversation_style']}'
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', '{self.project_id}')
DATASET_NAME = 'agent_{agent_id.replace('-', '_')}'

# Prompt base do agente
AGENT_PROMPT = """{agent_data['prompt_template']}"""

# Cliente BigQuery
bq_client = bigquery.Client(project=PROJECT_ID)

def get_claude_api_key():
    secret_client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{{PROJECT_ID}}/secrets/claude-api-key/versions/latest"
    response = secret_client.access_secret_version(request={{"name": name}})
    return response.payload.data.decode("UTF-8")

@app.route('/')
def index():
    return render_template('chat.html', 
                         agent_name=AGENT_NAME,
                         agent_type=AGENT_TYPE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        conversation_id = request.json.get('conversation_id', str(uuid.uuid4()))
        
        # Configurar Claude
        client = anthropic.Anthropic(api_key=get_claude_api_key())
        
        # Buscar contexto da conversa
        context = get_conversation_context(conversation_id)
        
        # Criar mensagem completa
        full_prompt = f"{{AGENT_PROMPT}}\\n\\nContexto da conversa:\\n{{context}}\\n\\nUsuário: {{user_message}}\\n\\nAssistente:"
        
        # Chamar Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{{"role": "user", "content": full_prompt}}]
        )
        
        assistant_message = response.content[0].text
        
        # Salvar mensagens no BigQuery
        save_messages(conversation_id, user_message, assistant_message, response.usage.input_tokens + response.usage.output_tokens)
        
        return jsonify({{
            'response': assistant_message,
            'conversation_id': conversation_id
        }})
        
    except Exception as e:
        return jsonify({{'error': str(e)}}), 500

def get_conversation_context(conversation_id):
    query = f"""
    SELECT role, content, timestamp
    FROM `{{PROJECT_ID}}.{{DATASET_NAME}}.messages`
    WHERE conversation_id = @conversation_id
    ORDER BY timestamp DESC
    LIMIT 10
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("conversation_id", "STRING", conversation_id)]
    )
    
    try:
        results = list(bq_client.query(query, job_config=job_config))
        context = ""
        for row in reversed(results):
            context += f"{{row.role}}: {{row.content}}\\n"
        return context
    except:
        return ""

def save_messages(conversation_id, user_message, assistant_message, tokens_used):
    now = datetime.utcnow()
    
    rows = [
        {{
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": "user",
            "content": user_message,
            "timestamp": now,
            "tokens_used": 0
        }},
        {{
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": "assistant", 
            "content": assistant_message,
            "timestamp": now,
            "tokens_used": tokens_used
        }}
    ]
    
    table_id = f"{{PROJECT_ID}}.{{DATASET_NAME}}.messages"
    try:
        errors = bq_client.insert_rows_json(table_id, rows)
        if errors:
            print(f"Erro ao salvar mensagens: {{errors}}")
    except Exception as e:
        print(f"Erro ao salvar mensagens: {{e}}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
'''
        
        with open(f"{agent_dir}/app/main.py", 'w') as f:
            f.write(main_py_content)
        
        print(f"✅ Código do agente personalizado criado")
    
    def deploy_to_cloud_run(self, agent_dir, agent_id, agent_name):
        """Deploy do agente para Cloud Run"""
        service_name = f"agent-{agent_id}"
        
        try:
            # Mudar para diretório do agente
            original_dir = os.getcwd()
            os.chdir(agent_dir)
            
            # Build da imagem
            build_cmd = [
                "gcloud", "builds", "submit",
                "--tag", f"gcr.io/{self.project_id}/{service_name}",
                "."
            ]
            
            print(f"🔨 Fazendo build da imagem...")
            result = subprocess.run(build_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Erro no build: {result.stderr}")
            
            print(f"✅ Build concluído para {service_name}")
            
            # Deploy para Cloud Run
            deploy_cmd = [
                "gcloud", "run", "deploy", service_name,
                "--image", f"gcr.io/{self.project_id}/{service_name}",
                "--platform", "managed",
                "--region", self.region,
                "--allow-unauthenticated",
                "--memory", "1Gi",
                "--cpu", "1",
                "--set-env-vars", f"GOOGLE_CLOUD_PROJECT={self.project_id}",
                "--service-account", f"ai-generator-sa@{self.project_id}.iam.gserviceaccount.com"
            ]
            
            print(f"🚀 Fazendo deploy no Cloud Run...")
            result = subprocess.run(deploy_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Erro no deploy: {result.stderr}")
            
            # Extrair URL do serviço
            service_url = self._extract_service_url(result.stdout)
            
            # Voltar ao diretório original
            os.chdir(original_dir)
            
            print(f"✅ Deploy concluído: {service_url}")
            return service_url
            
        except Exception as e:
            os.chdir(original_dir)
            print(f"❌ Erro no deploy: {e}")
            return None
    
    def _extract_service_url(self, deploy_output):
        """Extrai URL do serviço do output do gcloud run deploy"""
        for line in deploy_output.split('\\n'):
            if 'https://' in line and 'run.app' in line:
                return line.strip()
        return None
    
    def save_agent_metadata(self, agent_data, agent_id, cloud_run_url, dataset_name):
        """Salva metadados do agente no BigQuery"""
        now = datetime.utcnow()
        
        rows = [{
            "agent_id": agent_id,
            "agent_name": agent_data['agent_name'],
            "agent_type": agent_data['agent_type'],
            "conversation_style": agent_data['conversation_style'],
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "cloud_run_url": cloud_run_url,
            "dataset_name": dataset_name,
            "creator_email": "victor.campos@flowerclub.com.br",
            "prompt_template": agent_data['prompt_template'],
            "description": agent_data['description']
        }]
        
        table_id = f"{self.project_id}.ai_generator_metadata.agents"
        errors = self.bq_client.insert_rows_json(table_id, rows)
        
        if errors:
            print(f"❌ Erro ao salvar metadados: {errors}")
        else:
            print(f"✅ Metadados do agente salvos")

# Função principal para deploy completo
def deploy_complete_agent(agent_data):
    agent_id = str(uuid.uuid4())
    deployer = AgentDeployer(
        project_id=os.environ.get('GOOGLE_CLOUD_PROJECT', 'flower-ai-generator'),
        region='southamerica-east1'
    )
    
    print(f"🚀 Iniciando deploy do agente: {agent_data['agent_name']}")
    
    # 1. Criar dataset BigQuery
    dataset_name = deployer.create_agent_dataset(agent_id)
    if not dataset_name:
        return None
    
    # 2. Criar código personalizado
    agent_dir = deployer.create_agent_code(agent_data, agent_id)
    
    # 3. Deploy para Cloud Run
    cloud_run_url = deployer.deploy_to_cloud_run(agent_dir, agent_id, agent_data['agent_name'])
    if not cloud_run_url:
        return None
    
    # 4. Salvar metadados
    deployer.save_agent_metadata(agent_data, agent_id, cloud_run_url, dataset_name)
    
    print(f"🎉 Deploy concluído com sucesso!")
    print(f"   Agent ID: {agent_id}")
    print(f"   URL: {cloud_run_url}")
    print(f"   Dataset: {dataset_name}")
    
    return {
        'agent_id': agent_id,
        'cloud_run_url': cloud_run_url,
        'dataset_name': dataset_name
    }
