
#!/usr/bin/env python3
"""
Sistema de chatbot modular com roteamento de agentes para InfinitePay.

Este sistema roteia perguntas entre agentes especializados:
- RouterAgent: Classifica perguntas como 'knowledge' ou 'math'
- KnowledgeAgent: Responde usando RAG na base do InfinitePay
- MathAgent: Resolve expressões matemáticas
"""

import argparse

from agents.router_agent import RouterAgent
from agents.knowledge_agent import KnowledgeAgent  
from agents.math_agent import MathAgent
from services.crawling_service import CrawlingService
from services.vector_store_service import VectorStoreService
from config.settings import DEFAULT_SEED, PERSIST_DIR
from services.redis_service import RedisService
from config.settings import (
    REDIS_URL, REDIS_LOG_STREAM, REDIS_CONV_TTL_SECONDS,
    RATE_LIMIT_WINDOW_SEC, RATE_LIMIT_MAX_REQUESTS,
)
import time


def ingest_command(args):
    """Executa o processo de ingestão de dados."""
    print("[ingest] Iniciando ingestão...")
    
    crawling_service = CrawlingService()
    vector_service = VectorStoreService()
    
    docs = crawling_service.crawl_knowledge_base(
        seed_url=args.seed,
        max_depth=args.max_depth,
        timeout=args.timeout,
    )
    
    print("[ingest] Dividindo documentos...")
    chunks = vector_service.split_documents(
        docs, 
        chunk_size=args.chunk_size, 
        chunk_overlap=args.chunk_overlap
    )
    
    print(f"[ingest] {len(chunks)} chunks gerados. Construindo vector store...")
    vector_service.build_vectorstore(chunks)
    
    print(f"[ingest] Concluído. Vector DB persistido em: {PERSIST_DIR}")


def interactive_loop():
    """Loop interativo principal do chatbot."""
    router = RouterAgent()
    knowledge_agent = KnowledgeAgent()
    math_agent = MathAgent()
    redis_service = RedisService(
        REDIS_URL, REDIS_LOG_STREAM, REDIS_CONV_TTL_SECONDS
    )

    print("=== Sistema de Chatbot InfinitePay ===")
    print("Digite 'q' para sair")
    user_id = "local-user"
    conversation_id = "local-conv"
    redis_service.add_user_conversation(user_id, conversation_id)

    while True:
        print("\n" + "="*50)
        question = input("Sua pergunta: ")
        print()
        if question.strip().lower() == "q":
            print("Até logo!")
            break

        # Rate limit
        allowed, remaining = redis_service.rate_limit_allow(
            user_id, RATE_LIMIT_WINDOW_SEC, RATE_LIMIT_MAX_REQUESTS
        )
        if not allowed:
            print("Muitas requisições. Tente novamente em instantes.")
            continue

        # Persist user message
        redis_service.append_message(
            conversation_id, role="user", content=question, user_id=user_id
        )

        t0 = time.time()
        route = router.process(question)
        dt = (time.time() - t0) * 1000.0
        print(f"[Router] Direcionando para: {route}")

        redis_service.log_json(
            level="INFO",
            agent="RouterAgent",
            conversation_id=conversation_id,
            user_id=user_id,
            execution_time_ms=dt,
            decision=route,
            processed_content=question[:200],
        )

        if route == "knowledge":
            response = knowledge_agent.process(question)
            agent_name = "KnowledgeAgent"
        else:
            response = math_agent.process(question)
            agent_name = "MathAgent"

        redis_service.append_message(
            conversation_id, role="assistant", content=response,
            user_id=user_id, agent=agent_name
        )

        print(f"\n[{agent_name}] {response}")

def main():
    """Função principal do sistema."""
    parser = argparse.ArgumentParser(description="InfinitePay RAG with LangChain + Ollama (incremental).")
    sub = parser.add_subparsers(dest="cmd")

    p_ingest = sub.add_parser("ingest", help="Crawl + embed + persist the InfinitePay help center.")
    p_ingest.add_argument("--seed", default=DEFAULT_SEED, help="Seed URL for recursive crawl fallback.")
    p_ingest.add_argument("--no-sitemap", action="store_true", help="Skip sitemap and force recursive crawl.")
    p_ingest.add_argument("--max-depth", type=int, default=3, help="Max recursive depth when crawling.")
    p_ingest.add_argument("--timeout", type=int, default=10, help="HTTP timeout per request.")
    p_ingest.add_argument("--chunk-size", type=int, default=800)
    p_ingest.add_argument("--chunk-overlap", type=int, default=120)

    p_ask = sub.add_parser("ask", help="Ask one question against the persisted vector DB.")
    p_ask.add_argument("--q", required=True, help="Your question.")
    p_ask.add_argument("--route", choices=["auto", "knowledge", "math"], default="auto", help="Force a route or auto.")

    args = parser.parse_args()

    if args.cmd == "ingest":
        ingest_command(args)
        return

    if args.cmd == "ask":
        router = RouterAgent()
        knowledge_agent = KnowledgeAgent()
        math_agent = MathAgent()
        
        if args.route == "auto":
            route = router.process(args.q)
        else:
            route = args.route

        if route == "knowledge":
            print(knowledge_agent.process(args.q))
        else:
            print(math_agent.process(args.q))
        return

    interactive_loop()


if __name__ == "__main__":
    main()
