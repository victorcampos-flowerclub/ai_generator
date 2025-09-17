// Função para mostrar loading
function showLoading(element) {
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
    element.disabled = true;
}

// Função para esconder loading
function hideLoading(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

// Validação de formulários
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar validações personalizadas aqui
    console.log('AI Agent Generator - Backoffice carregado');
});
