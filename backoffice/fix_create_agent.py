import requests
import json
from google.cloud import secretmanager

def test_claude_api():
    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        name = "projects/flower-ai-generator/secrets/claude-api-key/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        api_key = response.payload.data.decode("UTF-8").strip()
        
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "Diga apenas 'teste ok'"}]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers, 
            json=data, 
            timeout=30
        )
        
        print(f"Claude API Status: {response.status_code}")
        if response.status_code == 200:
            print("Claude API OK")
            return True
        else:
            print(f"Claude API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Claude API Exception: {e}")
        return False

def test_create_agent():
    try:
        agent_data = {
            "name": "Agente Teste",
            "type": "custom",
            "specialization": "Teste",
            "conversation_style": "professional",
            "system_prompt": "Você é um agente de teste."
        }
        
        response = requests.post(
            "https://ai-generator-backend-365442086139.southamerica-east1.run.app/api/create-agent",
            json=agent_data,
            timeout=60
        )
        
        print(f"Create Agent Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response.status_code == 200
            
    except Exception as e:
        print(f"Create Agent Exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing Claude API...")
    claude_ok = test_claude_api()
    print("\nTesting Create Agent...")
    create_ok = test_create_agent()
    
    print(f"\nResults:")
    print(f"Claude API: {'OK' if claude_ok else 'FAIL'}")
    print(f"Create Agent: {'OK' if create_ok else 'FAIL'}")
