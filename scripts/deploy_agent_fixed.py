import os
import uuid
import shutil
import subprocess
from datetime import datetime
from google.cloud import bigquery, storage, secretmanager
import time
import re

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
            ]
        }
        
        for table_name, schema in tables.items():
            table_id = f"{self.project_id}.{dataset_name}.{table_name}"
            table = bigquery.Table(table_id, schema=schema)
            table = self.bq_client.create_table(table)
            print(f"  ✅ Tabela criada: {table_name}")
    
    def get_service_url(self, service_name):
        """Busca URL do serviço Cloud Run de forma robusta"""
        try:
            # Método 1: Descrever serviço específico
            cmd = [
                "gcloud", "run", "services", "describe", service_name,
                "--region", self.region,
                "--format", "value(status.url)"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                url = result.stdout.strip()
                if url and url.startswith('https://'):
                    print(f"✅ URL encontrada via describe: {url}")
                    return url
            
            # Método 2: Listar e filtrar
            list_cmd = [
                "gcloud", "run", "services", "list",
                "--region", self.region,
                "--format", "table(metadata.name,status.url)"
            ]
            
            result = subprocess.run(list_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if service_name in line and 'https://' in line:
                        # Extrair URL da linha
                        url_match = re.search(r'https://[^\s]+', line)
                        if url_match:
                            url = url_match.group(0)
                            print(f"✅ URL encontrada via list: {url}")
                            return url
                            
            print(f"❌ URL não encontrada para {service_name}")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar URL: {e}")
            return None
    
    def update_agent_with_url(self, agent_id, service_name):
        """Atualiza agente com URL do Cloud Run depois que descobrimos"""
        url = self.get_service_url(service_name)
        
        if url:
            query = f"""
            UPDATE `{self.project_id}.ai_generator_metadata.agents`
            SET 
                cloud_run_url = @cloud_run_url,
                status = 'active',
                updated_at = CURRENT_TIMESTAMP()
            WHERE agent_id = @agent_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("agent_id", "STRING", agent_id),
                    bigquery.ScalarQueryParameter("cloud_run_url", "STRING", url),
                ]
            )
            
            self.bq_client.query(query, job_config=job_config)
            print(f"✅ Agente atualizado com URL: {url}")
            return url
        
        return None

# Função para corrigir agente existente
def fix_existing_agent():
    """Corrige o agente que foi criado mas ficou sem URL"""
    
    deployer = AgentDeployer(
        project_id='flower-ai-generator',
        region='southamerica-east1'
    )
    
    # Buscar agente criado recentemente sem URL
    query = """
    SELECT agent_id, agent_name, dataset_name
    FROM `flower-ai-generator.ai_generator_metadata.agents`
    WHERE cloud_run_url IS NULL 
       OR cloud_run_url = 'None'
       OR cloud_run_url = ''
    ORDER BY created_at DESC
    LIMIT 1
    """
    
    results = list(deployer.bq_client.query(query))
    
    if results:
        agent = results[0]
        agent_id = agent.agent_id
        print(f"🔍 Encontrado agente sem URL: {agent.agent_name} ({agent_id})")
        
        # Construir nome do serviço
        service_name = f"agent-{agent_id}"
        
        # Buscar e atualizar URL
        url = deployer.update_agent_with_url(agent_id, service_name)
        
        if url:
            print(f"🎉 Agente corrigido com sucesso!")
            print(f"   🆔 Agent ID: {agent_id}")
            print(f"   🌐 URL: {url}")
            print(f"   📊 Dataset: {agent.dataset_name}")
            return True
        else:
            print(f"❌ Não foi possível encontrar URL do serviço")
            return False
    else:
        print("ℹ️ Nenhum agente sem URL encontrado")
        return False

if __name__ == "__main__":
    fix_existing_agent()
