#!/usr/bin/env python3
import os
import sys
sys.path.append('/home/victor_campos/ai-generator-system/scripts')

from deploy_agent import deploy_complete_agent
from google.cloud import bigquery

# Configurar projeto
os.environ['GOOGLE_CLOUD_PROJECT'] = 'flower-ai-generator'

def create_flor_agent():
    """Cria o agente Flor - CTO AI com documentação do Flower Club"""
    
    # Dados do agente Flor baseados na documentação
    flor_agent_data = {
        'agent_name': 'Flor - CTO AI',
        'agent_type': 'cto',
        'conversation_style': 'professional',
        'description': 'CTO especializada em arquitetura Cloud, BigQuery, Cloud Run e sistemas de alta performance. Expert em APIs REST e ETL pipelines.',
        'prompt_template': '''Você é Flor, uma CTO (Chief Technology Officer) altamente experiente e especializada em:

🔧 ESPECIALIDADES TÉCNICAS:
- Arquitetura Cloud (Google Cloud Platform)
- BigQuery e Data Engineering
- Cloud Run e containerização
- APIs REST e microserviços
- Sistemas ETL e pipelines de dados
- Performance optimization
- Flower Club Enterprise API (sistema FIFO)

📊 CONHECIMENTO ESPECÍFICO:
Você tem conhecimento profundo do sistema Flower Club Enterprise API v4.6.7, incluindo:
- Sistema FIFO de créditos/débitos
- ETL v1.0.7 com inadimplentes e cancelados
- 25 endpoints funcionais com autenticação Bearer
- Arquitetura BigQuery com 7 projetos integrados
- Performance otimizada (todos endpoints < 20s)
- Base real de 10.177 clientes
- R$ 15.958.267,81+ movimentados

🎯 SEU PAPEL:
- Fornecer soluções técnicas precisas e práticas
- Explicar arquiteturas complexas de forma clara
- Sugerir otimizações de performance
- Resolver problemas de infraestrutura
- Orientar sobre melhores práticas de desenvolvimento

💼 ESTILO DE COMUNICAÇÃO:
- Profissional mas acessível
- Foco em soluções práticas
- Use exemplos concretos
- Seja direta e objetiva
- Demonstre expertise técnica

Sempre que relevante, referencie o conhecimento específico do sistema Flower Club para dar contexto e exemplos práticos.'''
    }
    
    print("🚀 Iniciando criação do agente Flor...")
    print(f"Nome: {flor_agent_data['agent_name']}")
    print(f"Tipo: {flor_agent_data['agent_type']}")
    print(f"Estilo: {flor_agent_data['conversation_style']}")
    print()
    
    # Primeiro, salvar os dados básicos no BigQuery
    bq_client = bigquery.Client(project='flower-ai-generator')
    
    # Inserir agente na tabela metadata
    agent_row = {
        'agent_id': 'temp-flor-id',  # Será atualizado pelo deploy
        'agent_name': flor_agent_data['agent_name'],
        'agent_type': flor_agent_data['agent_type'],
        'conversation_style': flor_agent_data['conversation_style'],
        'status': 'creating',
        'created_at': 'CURRENT_TIMESTAMP()',
        'updated_at': 'CURRENT_TIMESTAMP()',
        'creator_email': 'victor.campos@flowerclub.com.br',
        'prompt_template': flor_agent_data['prompt_template'],
        'description': flor_agent_data['description']
    }
    
    # Executar deploy completo
    result = deploy_complete_agent(flor_agent_data)
    
    if result:
        print("🎉 AGENTE FLOR CRIADO COM SUCESSO!")
        print(f"   🆔 Agent ID: {result['agent_id']}")
        print(f"   🌐 URL: {result['cloud_run_url']}")
        print(f"   📊 Dataset: {result['dataset_name']}")
        print()
        print("🔗 PRÓXIMOS PASSOS:")
        print(f"   1. Acesse: {result['cloud_run_url']}")
        print("   2. Teste conversas com Flor")
        print("   3. Verifique logs no Cloud Run")
        print("   4. Monitore dados no BigQuery")
        
        return result
    else:
        print("❌ Erro na criação do agente Flor")
        return None

if __name__ == "__main__":
    create_flor_agent()
