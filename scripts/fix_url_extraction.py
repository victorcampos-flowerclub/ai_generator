import subprocess
import re

def get_cloud_run_service_url(service_name, project_id, region):
    """Busca URL do serviço Cloud Run de forma mais robusta"""
    try:
        # Comando para obter URL do serviço
        cmd = [
            "gcloud", "run", "services", "describe", service_name,
            "--region", region,
            "--format", "value(status.url)"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            url = result.stdout.strip()
            if url and url.startswith('https://'):
                return url
        
        # Método alternativo - listar serviços e encontrar o nosso
        list_cmd = [
            "gcloud", "run", "services", "list",
            "--region", region,
            "--filter", f"metadata.name={service_name}",
            "--format", "value(status.url)"
        ]
        
        result = subprocess.run(list_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            if url and url.startswith('https://'):
                return url
                
        return None
        
    except Exception as e:
        print(f"Erro ao buscar URL: {e}")
        return None

# Testar função
if __name__ == "__main__":
    # Tentar encontrar o serviço criado
    result = subprocess.run([
        "gcloud", "run", "services", "list", 
        "--region", "southamerica-east1",
        "--format", "table(metadata.name,status.url)"
    ], capture_output=True, text=True)
    
    print("=== SERVIÇOS CLOUD RUN ENCONTRADOS ===")
    print(result.stdout)
    
    # Buscar especificamente serviços que começam com "agent-"
    lines = result.stdout.split('\n')
    for line in lines:
        if 'agent-' in line and 'https://' in line:
            parts = line.split()
            if len(parts) >= 2:
                service_name = parts[0]
                url = parts[1] if parts[1].startswith('https://') else parts[-1]
                print(f"Serviço encontrado: {service_name} -> {url}")
