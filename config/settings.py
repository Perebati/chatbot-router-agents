"""
Configurações do projeto carregadas de variáveis de ambiente.
"""
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se existir
load_dotenv()

# Modelos Ollama
ROUTER_MODEL = os.environ.get("ROUTER_MODEL", "llama3.2")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "mxbai-embed-large")

# URLs e configurações de crawling
DEFAULT_SEED = os.environ.get("DEFAULT_SEED", "https://ajuda.infinitepay.io/pt-BR/")
BASE_URL = os.environ.get("BASE_URL", "https://ajuda.infinitepay.io")

# User Agent para requisições HTTP
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Configurações do banco de dados vetorial
PERSIST_DIR = os.environ.get("INFINITEPAY_DB_DIR", "./chroma_infinitepay")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "infinitepay_helpcenter")

# Configurações de chunk para processamento de documentos
DEFAULT_CHUNK_SIZE = int(os.environ.get("DEFAULT_CHUNK_SIZE", "800"))
DEFAULT_CHUNK_OVERLAP = int(os.environ.get("DEFAULT_CHUNK_OVERLAP", "120"))

# Configurações de crawling
DEFAULT_MAX_DEPTH = int(os.environ.get("DEFAULT_MAX_DEPTH", "3"))
DEFAULT_TIMEOUT = int(os.environ.get("DEFAULT_TIMEOUT", "10"))
DEFAULT_RETRIEVAL_K = int(os.environ.get("DEFAULT_RETRIEVAL_K", "5"))

# Regex para links do InfinitePay
LINK_REGEX = r'href="(https://ajuda\.infinitepay\.io/pt-BR/(?:articles|collections)/[^"]+)"'

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_LOG_STREAM = os.getenv("REDIS_LOG_STREAM", "logs:chat")
REDIS_CONV_TTL_SECONDS = int(os.getenv("REDIS_CONV_TTL_SECONDS", "604800"))
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60"))