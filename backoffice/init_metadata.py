#!/usr/bin/env python3
"""
Inicializar estrutura de metadados do AI Agent Generator - CORRIGIDO
Criar datasets e tabelas necessárias no BigQuery
"""

from google.cloud import bigquery
from datetime import datetime

def create_metadata_structure():
    """Criar estrutura completa de metadados no BigQuery"""
    
    project_id = 'flower-ai-generator'
    client = bigquery.Client(project=project_id)
    
    # 1. Criar dataset principal de metadados
    dataset_id = 'ai_generator_metadata'
    dataset_ref = f"{project_id}.{dataset_id}"
    
    try:
        # Criar dataset
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        dataset.description = "Metadados centrais do AI Agent Generator"
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"Dataset {dataset_id} criado/verificado")
        
        # 2. Tabela de agentes
        agents_schema = [
            bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("specialization", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("conversation_style", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("cloud_run_url", "STRING"),
            bigquery.SchemaField("bigquery_dataset", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("creator_email", "STRING"),
            bigquery.SchemaField("prompt_template", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("claude_model", "STRING"),
            bigquery.SchemaField("max_tokens", "INTEGER"),
            bigquery.SchemaField("total_conversations", "INTEGER"),
            bigquery.SchemaField("last_conversation_at", "TIMESTAMP"),
        ]
        
        agents_table_ref = f"{dataset_ref}.agents"
        agents_table = bigquery.Table(agents_table_ref, schema=agents_schema)
        agents_table = client.create_table(agents_table, exists_ok=True)
        print(f"Tabela agents criada/verificada")
        
        # 3. Tabela de documentos por agente
        documents_schema = [
            bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("document_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("file_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("file_size", "INTEGER"),
            bigquery.SchemaField("storage_path", "STRING"),
            bigquery.SchemaField("processed_content", "STRING"),
            bigquery.SchemaField("uploaded_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("processed_at", "TIMESTAMP"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        ]
        
        docs_table_ref = f"{dataset_ref}.agent_documents"
        docs_table = bigquery.Table(docs_table_ref, schema=documents_schema)
        docs_table = client.create_table(docs_table, exists_ok=True)
        print(f"Tabela agent_documents criada/verificada")
        
        # 4. Tabela de analytics agregadas
        analytics_schema = [
            bigquery.SchemaField("agent_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("total_conversations", "INTEGER"),
            bigquery.SchemaField("total_messages", "INTEGER"),
            bigquery.SchemaField("avg_response_time_ms", "FLOAT"),
            bigquery.SchemaField("error_count", "INTEGER"),
            bigquery.SchemaField("uptime_percentage", "FLOAT"),
            bigquery.SchemaField("unique_users", "INTEGER"),
        ]
        
        analytics_table_ref = f"{dataset_ref}.daily_analytics"
        analytics_table = bigquery.Table(analytics_table_ref, schema=analytics_schema)
        analytics_table = client.create_table(analytics_table, exists_ok=True)
        print(f"Tabela daily_analytics criada/verificada")
        
        # 5. Inserir agente Flor usando SQL direto (evita problema de serialização)
        insert_flor_query = f"""
        INSERT INTO `{agents_table_ref}` 
        (agent_id, agent_name, agent_type, specialization, conversation_style, status, 
         cloud_run_url, bigquery_dataset, created_at, updated_at, creator_email, 
         prompt_template, description, claude_model, max_tokens, total_conversations, last_conversation_at)
        SELECT 
            'flor-cto' as agent_id,
            'Flor CTO AI' as agent_name,
            'CTO/Tecnologia' as agent_type,
            'CTO especializada do Flower Club Enterprise API v4.6.7' as specialization,
            'Formal e Técnico' as conversation_style,
            'active' as status,
            'https://flor-intelligent-365442086139.southamerica-east1.run.app' as cloud_run_url,
            'flor_cto_dataset' as bigquery_dataset,
            CURRENT_TIMESTAMP() as created_at,
            CURRENT_TIMESTAMP() as updated_at,
            'victor_campos@flowerdash.com.br' as creator_email,
            'Você é Flor, CTO especializada do Flower Club Enterprise API v4.6.7' as prompt_template,
            'Agente CTO especializado em arquitetura, BigQuery, APIs REST e sistema FIFO' as description,
            'claude-sonnet-4-20250514' as claude_model,
            1500 as max_tokens,
            247 as total_conversations,
            CURRENT_TIMESTAMP() as last_conversation_at
        WHERE NOT EXISTS (
            SELECT 1 FROM `{agents_table_ref}` WHERE agent_id = 'flor-cto'
        )
        """
        
        query_job = client.query(insert_flor_query)
        result = query_job.result()
        
        if query_job.num_dml_affected_rows > 0:
            print("Agente Flor CTO inserido como exemplo")
        else:
            print("Agente Flor já existe na tabela")
        
        print("\nEstrutura de metadados criada com sucesso!")
        print("Datasets e tabelas:")
        print(f"- {dataset_ref}.agents")
        print(f"- {dataset_ref}.agent_documents") 
        print(f"- {dataset_ref}.daily_analytics")
        
        return True
        
    except Exception as e:
        print(f"Erro ao criar estrutura: {e}")
        return False

if __name__ == "__main__":
    create_metadata_structure()
