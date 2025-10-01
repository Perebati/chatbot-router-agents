
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
    
    print("=== Sistema de Chatbot InfinitePay ===")
    print("Digite 'q' para sair")
    
    while True:
        print("\n" + "="*50)
        question = input("Sua pergunta: ")
        print()
        
        if question.strip().lower() == "q":
            print("Até logo!")
            break

        route = router.process(question)
        print(f"[Router] Direcionando para: {route}")
        
        if route == "knowledge":
            response = knowledge_agent.process(question)
        else:  
            response = math_agent.process(question)
        
        print(f"\n[{route.title()}Agent] {response}")

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
