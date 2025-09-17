#!/usr/bin/env python3
"""
Corrigir tabela agents com schema completo
"""

from google.cloud import bigquery

def fix_agents_table():
    project_id = 'flower-ai-generator'
    client = bigquery.Client(project=project_id)
    
    # Deletar tabela existente
    table_ref = f"{project_id}.ai_generator_metadata.agents"
    
    try:
        client.delete_table(table_ref)
        print("Tabela agents deletada")
    except Exception as e:
        print(f"Tabela não existia: {e}")
    
    # Recriar com schema correto
    schema = [
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
    
    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table)
    print("Tabela agents recriada com schema correto")
    
    # Inserir agente Flor
    insert_query = f"""
    INSERT INTO `{table_ref}` 
    (agent_id, agent_name, agent_type, specialization, conversation_style, status, 
     cloud_run_url, bigquery_dataset, created_at, updated_at, creator_email, 
     prompt_template, description, claude_model, max_tokens, total_conversations, last_conversation_at)
    VALUES 
    ('flor-cto', 'Flor CTO AI', 'CTO/Tecnologia', 'CTO especializada do Flower Club Enterprise API v4.6.7', 
     'Formal e Técnico', 'active', 'https://flor-intelligent-365442086139.southamerica-east1.run.app', 
     'flor_cto_dataset', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), 'victor_campos@flowerdash.com.br',
     'Você é Flor, CTO especializada do Flower Club Enterprise API v4.6.7',
     'Agente CTO especializado em arquitetura, BigQuery, APIs REST e sistema FIFO',
     'claude-sonnet-4-20250514', 1500, 247, CURRENT_TIMESTAMP())
    """
    
    client.query(insert_query).result()
    print("Agente Flor inserido com sucesso")

if __name__ == "__main__":
    fix_agents_table()
