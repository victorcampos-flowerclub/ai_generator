#!/usr/bin/env python3
"""
Deploy Automático de Agentes AI
Script para criar e deployar novos agentes no Cloud Run
"""

import os
import json
import tempfile
import subprocess
import shutil
from datetime import datetime
from google.cloud import bigquery, storage

class AgentDeployer:
    def __init__(self, project_id='flower-ai-generator', region='southamerica-east1'):
        self.project_id = project_id
        self.region = region
        self.bq_client = bigquery.Client(project=project_id)
        self.storage_client = storage.Client(project=project_id)
        
    def create_agent_directory(self, agent_id, agent_code):
        """Criar estrutura de diretórios para o agente"""
        base_path = f"../agents/{agent_id}"
        
        # Criar diretórios
        os.makedirs(f"{base_path}/app", exist_ok=True)
        os.makedirs(f"{base_path}/templates", exist_ok=True)
        
        # Escrever arquivos
        with open(f"{base_path}/app/main.py", 'w') as f:
            f.write(agent_code['main_py'])
            
        with open(f"{base_path}/requirements.txt", 'w') as f:
            f.write(agent_code['requirements_txt'])
            
        with open(f"{base_path}/Dockerfile", 'w') as f:
            f.write(agent_code['dockerfile'])
            
        with open(f"{base_path}/templates/chat.html", 'w') as f:
            f.write(agent_code['chat_html'])
            
        return base_path
    
    def create_bigquery_dataset(self, agent_id):
        """Criar dataset BigQuery específico para o agente"""
        try:
            dataset_id = f"{agent_id.replace('-', '_')}_dataset"
            dataset_ref = f"{self.project_id}.{dataset_id}"
            
            # Criar dataset
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            dataset.description = f"Dataset para agente {agent_id}"
            
            dataset = self.bq_client.create_dataset(dataset, exists_ok=True)
            
            # Criar tabelas básicas
            tables_schema = {
                'conversations': [
                    bigquery.SchemaField("conversation_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("user_message", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("agent_response", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                    bigquery.SchemaField("session_id", "STRING"),
                    bigquery.SchemaField("response_time_ms", "INTEGER"),
                ],
                'agent_config': [
                    bigquery.SchemaField("config_key", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("config_value", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
                ],
                'knowledge_base': [
                    bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("document_name", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("uploaded_at", "TIMESTAMP", mode="REQUIRED"),
                    bigquery.SchemaField("file_size", "INTEGER"),
                ]
            }
            
            for table_name, schema in tables_schema.items():
                table_ref = f"{dataset_ref}.{table_name}"
                table = bigquery.Table(table_ref, schema=schema)
                self.bq_client.create_table(table, exists_ok=True)
                
            return dataset_id
            
        except Exception as e:
            print(f"Erro ao criar dataset: {e}")
            return None
    
    def deploy_to_cloud_run(self, agent_id, agent_path):
        """Deploy do agente no Cloud Run"""
        try:
            service_name = f"{agent_id}-ai"
            
            # Comandos de deploy
            commands = [
                f"cd {agent_path}",
                f"gcloud run deploy {service_name} --source . --region={self.region} --memory=2Gi --cpu=1 --timeout=300s --allow-unauthenticated --project={self.project_id}"
            ]
            
            # Executar deploy
            result = subprocess.run(" && ".join(commands), shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extrair URL do serviço
                service_url = f"https://{service_name}-{self.project_id}.{self.region}.run.app"
                return service_url
            else:
                print(f"Erro no deploy: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Erro no deploy: {e}")
            return None
    
    def save_agent_metadata(self, agent_config, agent_id, service_url, dataset_id):
        """Salvar metadados do agente no BigQuery"""
        try:
            # Usar dataset de metadados central
            table_ref = f"{self.project_id}.ai_generator_metadata.agents"
            
            row = {
                "agent_id": agent_id,
                "agent_name": agent_config['name'],
                "agent_type": agent_config['type'],
                "specialization": agent_config['specialization'],
                "conversation_style": agent_config['conversation_style'],
                "status": "active",
                "cloud_run_url": service_url,
                "bigquery_dataset": dataset_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "creator_email": "victor_campos@flowerdash.com.br",
                "prompt_template": agent_config.get('system_prompt', ''),
                "description": f"Agente {agent_config['type']} especializado em {agent_config['specialization']}"
            }
            
            errors = self.bq_client.insert_rows_json(table_ref, [row])
            
            if not errors:
                return True
            else:
                print(f"Erro ao salvar metadados: {errors}")
                return False
                
        except Exception as e:
            print(f"Erro ao salvar metadados: {e}")
            return False
    
    def deploy_agent(self, agent_config, agent_code):
        """Processo completo de deploy do agente"""
        agent_id = agent_config['name'].lower().replace(' ', '-').replace('.', '')
        
        print(f"Iniciando deploy do agente: {agent_id}")
        
        # 1. Criar estrutura de arquivos
        print("1. Criando estrutura de arquivos...")
        agent_path = self.create_agent_directory(agent_id, agent_code)
        
        # 2. Criar dataset BigQuery
        print("2. Criando dataset BigQuery...")
        dataset_id = self.create_bigquery_dataset(agent_id)
        if not dataset_id:
            return False
        
        # 3. Deploy no Cloud Run
        print("3. Fazendo deploy no Cloud Run...")
        service_url = self.deploy_to_cloud_run(agent_id, agent_path)
        if not service_url:
            return False
        
        # 4. Salvar metadados
        print("4. Salvando metadados...")
        if not self.save_agent_metadata(agent_config, agent_id, service_url, dataset_id):
            return False
        
        print(f"Deploy concluído com sucesso!")
        print(f"Agent ID: {agent_id}")
        print(f"Service URL: {service_url}")
        print(f"Dataset: {dataset_id}")
        
        return {
            'agent_id': agent_id,
            'service_url': service_url,
            'dataset_id': dataset_id,
            'status': 'success'
        }

def main():
    """Exemplo de uso do deployer"""
    deployer = AgentDeployer()
    
    # Configuração de exemplo
    config = {
        'name': 'Dr. Silva',
        'type': 'Médico Cardiologista',
        'specialization': 'Cardiologia clínica e intervencionista',
        'conversation_style': 'Formal e técnico',
        'system_prompt': 'Você é Dr. Silva, médico cardiologista especializado...'
    }
    
    # Código de exemplo (seria gerado pelo sistema)
    code = {
        'main_py': '# Código gerado automaticamente...',
        'requirements_txt': 'Flask==2.3.3\n...',
        'dockerfile': 'FROM python:3.9-slim\n...',
        'chat_html': '<html>...</html>'
    }
    
    # Deploy
    result = deployer.deploy_agent(config, code)
    print(f"Resultado: {result}")

if __name__ == "__main__":
    main()
