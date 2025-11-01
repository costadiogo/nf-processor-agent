"""
Configurações globais da aplicação NFe Processor Agent.

Este módulo carrega todas as configurações a partir de variáveis de ambiente
e define valores padrão para a aplicação.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# =====================================================
# Carregar variáveis de ambiente do arquivo .env
# =====================================================

# Encontrar arquivo .env na raiz do projeto
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


# =====================================================
# ENUMS - Definir tipos e provedores suportados
# =====================================================

class LLMProvider(str, Enum):
    """Provedores de LLM suportados."""
    OPENAI = "openai"
    GROQ = "groq"
    GEMINI = "gemini"
    CLAUDE = "claude"
    OLLAMA = "ollama"  # Para modelos locais
    
    def __str__(self) -> str:
        """Representação em string do provider."""
        names = {
            "openai": "OpenAI",
            "groq": "Groq",
            "gemini": "Google Gemini",
            "claude": "Claude (Anthropic)",
            "ollama": "Ollama (Local)",
        }
        return names.get(self.value, self.value)


class LLMModel(str, Enum):
    """Modelos de LLM suportados por provider."""
    # OpenAI
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    
    # Groq
    LLAMA_3 = "llama-3.3-70b-versatile"
    LLAMA_2 = "llama2-70b-4096"
    
    # Google Gemini
    GEMINI_PRO = "gemini-pro"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    
    # Anthropic Claude
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Ollama (local)
    OLLAMA_LLAMA2 = "llama2"
    OLLAMA_MISTRAL = "mistral"


# Mapa de modelos por provider
MODELS_BY_PROVIDER = {
    LLMProvider.OPENAI: [
        LLMModel.GPT_4O,
        LLMModel.GPT_4O_MINI,
        LLMModel.GPT_4_TURBO,
    ],
    LLMProvider.GROQ: [
        LLMModel.LLAMA_3,
        LLMModel.LLAMA_2,
    ],
    LLMProvider.GEMINI: [
        LLMModel.GEMINI_PRO,
        LLMModel.GEMINI_1_5_PRO,
    ],
    LLMProvider.CLAUDE: [
        LLMModel.CLAUDE_3_OPUS,
        LLMModel.CLAUDE_3_SONNET,
        LLMModel.CLAUDE_3_HAIKU,
    ],
    LLMProvider.OLLAMA: [
        LLMModel.OLLAMA_LLAMA2,
        LLMModel.OLLAMA_MISTRAL,
    ],
}


# =====================================================
# Caminhos do Projeto
# =====================================================

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Diretório source
SRC_DIR = PROJECT_ROOT / "src"

# Diretório de dados
DATA_DIR = PROJECT_ROOT / "data"
DATA_SAMPLES_DIR = DATA_DIR / "samples"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

# Diretório de logs
LOGS_DIR = PROJECT_ROOT / "logs"

# Diretório de configuração
CONFIG_DIR = PROJECT_ROOT / "config"

# Criar diretórios se não existirem
for directory in [DATA_DIR, DATA_SAMPLES_DIR, DATA_PROCESSED_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# =====================================================
# Configurações de Banco de Dados
# =====================================================

# Caminho do banco de dados SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_PROCESSED_DIR}/notas_fiscais.db"
)

# Usar path direto para SQLite (sem prefixo sqlite:///)
DATABASE_PATH = DATA_PROCESSED_DIR / "notas_fiscais.db"

# Timeout para conexões com banco de dados (em segundos)
DATABASE_TIMEOUT = int(os.getenv("DATABASE_TIMEOUT", "30"))

# Echo SQL para debug
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"


# =====================================================
# Configurações de Logging
# =====================================================

# Nível de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Formato de log
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Arquivo de log principal
LOG_FILE = LOGS_DIR / "app.log"

# Arquivo de log do parser
LOG_FILE_PARSER = LOGS_DIR / "parser.log"

# Arquivo de log do agente
LOG_FILE_AGENT = LOGS_DIR / "agent.log"

# Tamanho máximo de arquivo de log (em MB)
LOG_MAX_SIZE_MB = int(os.getenv("LOG_MAX_SIZE_MB", "10"))

# Número máximo de arquivos de backup
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))


# =====================================================
# Configurações de LLM (Múltiplos Provedores)
# =====================================================

# Provedor padrão (pode ser alterado via Streamlit)
DEFAULT_LLM_PROVIDER = LLMProvider.GROQ  # Groq é gratuito e rápido!

# Modelo padrão por provider (será selecionado na interface)
DEFAULT_MODELS = {
    LLMProvider.OPENAI: LLMModel.GPT_4O_MINI,
    LLMProvider.GROQ: LLMModel.LLAMA_3,
    LLMProvider.GEMINI: LLMModel.GEMINI_PRO,
    LLMProvider.CLAUDE: LLMModel.CLAUDE_3_HAIKU,
    LLMProvider.OLLAMA: LLMModel.OLLAMA_LLAMA2,
}

# Temperatura (criatividade do modelo) - pode variar por provider
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# Token limit (pode variar por modelo)
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# Timeout para requisições LLM (em segundos)
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

# URL base para Ollama (se usando modelos locais)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# =====================================================
# Configurações de Upload de Arquivos
# =====================================================

# Tamanho máximo de upload (em MB)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))

# Formatos aceitos
ALLOWED_FILE_EXTENSIONS = [".xml", ".pdf", ".zip"]

# Diretório temporário para uploads
TEMP_DIR = DATA_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================
# Configurações de Processamento
# =====================================================

# Número máximo de notas para processar em batch
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

# Timeout para processamento de uma nota (em segundos)
PROCESSING_TIMEOUT = int(os.getenv("PROCESSING_TIMEOUT", "300"))

# Habilitar validação rigorosa
STRICT_VALIDATION = os.getenv("STRICT_VALIDATION", "True").lower() == "true"


# =====================================================
# Configurações de Streamlit
# =====================================================

# Título da aplicação
STREAMLIT_TITLE = "NFe Processor Agent 📄"

# Ícone da aplicação (emoji)
STREAMLIT_ICON = "📄"

# Layout da página
STREAMLIT_LAYOUT = "wide"

# Tema
STREAMLIT_THEME = os.getenv("STREAMLIT_THEME", "light")


# =====================================================
# Configurações de Memória do Agente
# =====================================================

# Tamanho máximo do histórico de memória
MEMORY_MAX_HISTORY = int(os.getenv("MEMORY_MAX_HISTORY", "50"))

# Habilitar persistência de memória
MEMORY_PERSIST = os.getenv("MEMORY_PERSIST", "True").lower() == "true"

# Arquivo para salvar memória
MEMORY_FILE = DATA_PROCESSED_DIR / "agent_memory.json"


# =====================================================
# Configurações de Relatórios
# =====================================================

# Formato padrão de exportação
REPORT_DEFAULT_FORMAT = os.getenv("REPORT_DEFAULT_FORMAT", "html")

# Habilitar gráficos interativos (Plotly)
REPORT_INTERACTIVE_CHARTS = os.getenv("REPORT_INTERACTIVE_CHARTS", "True").lower() == "true"

# Paleta de cores para gráficos
REPORT_COLOR_PALETTE = "Set2"


# =====================================================
# Configurações de Desenvolvimento
# =====================================================

# Modo debug
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Modo teste
TESTING = os.getenv("TESTING", "False").lower() == "true"

# Dados de exemplo para teste
USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "False").lower() == "true"


# =====================================================
# Função auxiliar para obter modelos por provider
# =====================================================

def get_models_for_provider(provider: LLMProvider) -> list[LLMModel]:
    """
    Retorna lista de modelos disponíveis para um provider específico.
    
    Args:
        provider: O provedor de LLM
        
    Returns:
        Lista de modelos disponíveis para o provider
    """
    return MODELS_BY_PROVIDER.get(provider, [])


def get_provider_display_name(provider: LLMProvider) -> str:
    """
    Retorna nome de exibição para um provider.
    
    Args:
        provider: O provedor de LLM
        
    Returns:
        String de exibição do provider
    """
    return str(provider)


# =====================================================
# Função auxiliar para validar config
# =====================================================

def validate_config() -> dict:
    """
    Valida as configurações e retorna um dicionário com status.
    
    Returns:
        dict: Dicionário com keys "valid" (bool) e "issues" (list)
    """
    issues: list[str] = []
    
    # Validar diretórios críticos
    if not SRC_DIR.exists():
        issues.append(f"Diretório src não encontrado: {SRC_DIR}")
    
    if not DATA_DIR.exists():
        issues.append(f"Diretório data não criado: {DATA_DIR}")
    
    # Validar limites
    if MAX_UPLOAD_SIZE_MB <= 0:
        issues.append("MAX_UPLOAD_SIZE_MB deve ser positivo")
    
    if BATCH_SIZE <= 0:
        issues.append("BATCH_SIZE deve ser positivo")
    
    # Validar LLM Provider padrão
    if DEFAULT_LLM_PROVIDER not in LLMProvider:
        issues.append(f"Provider padrão inválido: {DEFAULT_LLM_PROVIDER}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }
