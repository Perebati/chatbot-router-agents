# Sistema de Chatbot Modular InfinitePay

Sistema de chatbot modular que demonstra roteamento de agentes, implementação RAG, segurança e observabilidade. O sistema roteia mensagens de usuários entre agentes especializados (KnowledgeAgent para consultas RAG, MathAgent para cálculos) com logging abrangente e gerenciamento de conversas.

## 🏗️ Arquitetura

### Sistema de Agentes
- **RouterAgent**: Orquestrador central que analisa mensagens e roteia para agentes especializados apropriados
- **KnowledgeAgent**: Implementação RAG usando conteúdo de https://ajuda.infinitepay.io/pt-BR/
- **MathAgent**: Interpretador de expressões matemáticas com LLM

### Estrutura do Projeto

```
├── agents/                     # Sistema de agentes
│   ├── __init__.py
│   ├── base_agent.py          # Classe base para todos os agentes
│   ├── router_agent.py        # Agente de roteamento
│   ├── knowledge_agent.py     # Agente RAG para conhecimento
│   └── math_agent.py          # Agente matemático
├── services/                  # Camada de serviços
│   ├── __init__.py
│   ├── crawling_service.py    # Serviço de web crawling
│   └── vector_store_service.py # Gerenciamento do banco vetorial
├── config/                    # Configurações
│   ├── __init__.py
│   └── settings.py           # Configurações centralizadas
├── utils/                     # Utilitários
│   ├── __init__.py
│   └── text_utils.py         # Processamento de texto
├── chroma_infinitepay/       # Banco de dados vetorial
├── main.py                   # Ponto de entrada principal
├── requirements.txt          # Dependências Python
├── .env.example             # Exemplo de variáveis de ambiente
└── .env                     # Variáveis de ambiente (local)
```

## 🚀 Instalação e Configuração

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e ajuste as configurações:

```bash
cp .env.example .env
```

### 3. Configurar Ollama

Certifique-se de que o Ollama esteja instalado e os modelos necessários baixados:

```bash
ollama pull llama3.2
ollama pull mxbai-embed-large
```

## 📊 Uso

### Ingestão de Dados

Primeiro, faça a ingestão da base de conhecimento:

```bash
python main.py ingest
```

Com parâmetros personalizados:

```bash
python main.py ingest --seed "https://ajuda.infinitepay.io/pt-BR/" --max-depth 3 --chunk-size 800
```

### Modo Interativo

Execute o chatbot em modo interativo:

```bash
python main.py
```

### Pergunta Única

Faça uma pergunta direta:

```bash
python main.py ask --q "Como criar uma conta no InfinitePay?"
```

Force um roteamento específico:

```bash
python main.py ask --q "Quanto é 25 x 4?" --route math
```

## 🔧 Configurações

### Variáveis de Ambiente (.env)

```env
# Modelos Ollama
ROUTER_MODEL=llama3.2
EMBED_MODEL=mxbai-embed-large

# URLs e configurações de crawling
DEFAULT_SEED=https://ajuda.infinitepay.io/pt-BR/
BASE_URL=https://ajuda.infinitepay.io

# User Agent para requisições HTTP
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36

# Configurações do banco de dados vetorial
INFINITEPAY_DB_DIR=./chroma_infinitepay
COLLECTION_NAME=infinitepay_helpcenter

# Configurações de processamento
DEFAULT_CHUNK_SIZE=800
DEFAULT_CHUNK_OVERLAP=120
DEFAULT_MAX_DEPTH=3
DEFAULT_TIMEOUT=10
DEFAULT_RETRIEVAL_K=5
```

## 📝 Exemplos de Uso

### Perguntas de Conhecimento

```
> Como faço para criar uma conta no InfinitePay?
[Router] Direcionando para: knowledge
[KnowledgeAgent] Para criar uma conta no InfinitePay, você precisa...
```

### Perguntas Matemáticas

```
> Quanto é 25 x 4 + 10?
[Router] Direcionando para: math
[MathAgent] Vamos resolver passo a passo:
25 x 4 = 100
100 + 10 = 110
Resposta final: 110
```

## 🔍 Arquitetura dos Componentes

### Agentes (agents/)
- **BaseAgent**: Classe abstrata base para todos os agentes
- **RouterAgent**: Classifica perguntas como 'knowledge' ou 'math'
- **KnowledgeAgent**: Implementa RAG com recuperação de contexto
- **MathAgent**: Resolve expressões matemáticas

### Serviços (services/)
- **CrawlingService**: Web crawling da central de ajuda
- **VectorStoreService**: Gerenciamento do Chroma DB

### Configurações (config/)
- **settings.py**: Configurações centralizadas carregadas do .env

### Utilitários (utils/)
- **text_utils.py**: Extração e processamento de texto HTML

## 🚀 Próximos Passos

Para expandir este projeto para uma API completa, considere implementar:

1. **API REST**: Endpoint `/chat` com FastAPI
2. **Gerenciamento de Conversas**: Redis para persistência
3. **Logging Estruturado**: Logs JSON com timing e decisões
4. **Frontend React**: Interface de chat com múltiplas conversas
5. **Segurança**: Sanitização de entrada e prevenção de prompt injection
6. **Testes**: Unidade, integração e E2E
7. **Containerização**: Docker e Kubernetes

## 📄 Licença

Este projeto é um exemplo educacional para demonstração de arquitetura de chatbot modular.