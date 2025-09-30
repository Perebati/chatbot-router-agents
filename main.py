
from __future__ import annotations

# === Existing imports (kept) ===
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# === New imports (incremental additions) ===
import re
from bs4 import BeautifulSoup
import argparse
import os
import sys
import traceback
from typing import List, Optional, Tuple

# LangChain loaders / splitters / vectorstore / embeddings
from langchain_community.document_loaders import SitemapLoader, RecursiveUrlLoader
from langchain_chroma import Chroma  # novo pacote
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings

# -----------------------------------------------------------------------------
# LLM setup (same backbone you already had)
# -----------------------------------------------------------------------------
model = OllamaLLM(model="llama3.2")

# -----------------------------------------------------------------------------
# Classification prompt (kept from your original code)
# -----------------------------------------------------------------------------
template = """
You are a RouterAgent.
Your goal is to analyze the user question and classify it into one of two categories:

- "knowledge" - for questions about InfinitePay app, features, help, or support
- "math" - for questions involving mathematical calculations or expressions

User question: {question}

You must respond with exactly one word: either "knowledge" or "math". Nothing else.

Classification:"""

prompt = ChatPromptTemplate.from_template(template)
router_chain = prompt | model

# -----------------------------------------------------------------------------
# New: RAG pieces (crawler, embedder, vector store, retriever)
# -----------------------------------------------------------------------------

DEFAULT_SEED = "https://ajuda.infinitepay.io/pt-BR/"
DEFAULT_SITEMAP = "https://ajuda.infinitepay.io/sitemap.xml"
PERSIST_DIR = os.environ.get("INFINITEPAY_DB_DIR", "./chroma_infinitepay")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "mxbai-embed-large")

def bs4_extractor(html: str) -> str:
    """Extrai texto limpo do HTML usando BeautifulSoup e normaliza quebras de linha."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text).strip()
    return text


def _ensure_persist_dir():
    os.makedirs(PERSIST_DIR, exist_ok=True)

def crawl_knowledge_base(
    sitemap_url: str = DEFAULT_SITEMAP,
    seed_url: str = DEFAULT_SEED,
    use_sitemap_first: bool = True,
    max_depth: int = 3,
    timeout: int = 10,
) -> List:
    """
    Attempts to load documents via sitemap first; if not available,
    falls back to a recursive crawler starting from the seed page.
    """
    docs: List = []
    if use_sitemap_first:
        try:
            print(f"[ingest] Trying sitemap: {sitemap_url}")
            loader = SitemapLoader(
                sitemap_url,
                is_local=False,
                filter_urls=[seed_url.rstrip("/")],
                # The loader will fetch URLs from the sitemap; extraction uses lxml/bs4 under the hood
            )
            docs = loader.load()
            if docs:
                print(f"[ingest] Loaded {len(docs)} docs from sitemap.")
                return docs
        except Exception as e:
            print(f"[ingest] Sitemap attempt failed: {e}")

    print(f"[ingest] Falling back to recursive crawl from: {seed_url}")
    try:
        headers = {
            "User-Agent": os.environ.get(
                "USER_AGENT",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }

        link_re = r'href="(https://ajuda\.infinitepay\.io/pt-BR/(?:articles|collections)/[^"]+)"'

        loader = RecursiveUrlLoader(
            url=seed_url,
            max_depth=max_depth,
            extractor=bs4_extractor,
            timeout=timeout,
            headers=headers,
            check_response_status=True,
            continue_on_failure=True,
            prevent_outside=True,
            base_url="https://ajuda.infinitepay.io",
            link_regex=link_re,  # stay in domain
        )
        docs = loader.load()
        print(f"[ingest] Loaded {len(docs)} docs via recursive crawl.")
        return docs
    except Exception as e:
        print(f"[ingest] Recursive crawl failed: {e}")
        raise

def split_docs(docs, chunk_size: int = 800, chunk_overlap: int = 120):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)

def build_vectorstore(chunks):
    _ensure_persist_dir()
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    vectordb = Chroma.from_documents(
        chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name="infinitepay_helpcenter",
    )
    return vectordb

def get_vectorstore():
    _ensure_persist_dir()
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
        collection_name="infinitepay_helpcenter",
    )

def ingest_command(args):
    print("[ingest] Starting ingestion...")
    docs = crawl_knowledge_base(
        sitemap_url=args.sitemap,
        seed_url=args.seed,
        use_sitemap_first=not args.no_sitemap,
        max_depth=args.max_depth,
        timeout=args.timeout,
    )
    print("[ingest] Splitting documents...")
    chunks = split_docs(docs, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    print(f"[ingest] {len(chunks)} chunks generated. Building vector store...")
    _ = build_vectorstore(chunks)
    print(f"[ingest] Done. Vector DB persisted at: {PERSIST_DIR}")

# -----------------------------------------------------------------------------
# New: Knowledge QA prompt (PT-BR + fontes)
# -----------------------------------------------------------------------------
rag_prompt = ChatPromptTemplate.from_template(
    """
Você é um assistente de suporte da InfinitePay. Responda de forma breve, em português do Brasil.
Use APENAS as informações do contexto ao responder. Se não houver contexto suficiente, diga que não sabe.

Pergunta do usuário:
{question}

Contexto (trechos relevantes de artigos da Central de Ajuda da InfinitePay):
{context}

Instruções:
- Seja direto e prático.
- Se existir, inclua os links/fonte dos artigos mencionados (use as metadatas 'source' ou 'link').
- Se a pergunta não se relacionar à InfinitePay, diga que está fora do escopo.
Resposta:
"""
)

def retrieve_context(query: str, k: int = 5) -> Tuple[str, List]:
    vectordb = get_vectorstore()
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    docs = retriever.invoke(query)
    # Concat text and keep sources
    parts = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source") or d.metadata.get("link") or d.metadata.get("url") or "N/A"
        parts.append(f"[{i}] Fonte: {src}\n{d.page_content.strip()}")
    return "\n\n---\n\n".join(parts), docs

def knowledge_answer(query: str) -> str:
    try:
        context, docs = retrieve_context(query, k=5)
        chain = rag_prompt | model
        answer = chain.invoke({"question": query, "context": context})
        # Pretty-print sources at the end (unique)
        links = []
        for d in docs:
            link = d.metadata.get("source") or d.metadata.get("link") or d.metadata.get("url")
            if link and link not in links:
                links.append(link)
        if links:
            answer = f"{answer}\n\nFontes:\n" + "\n".join(f"- {u}" for u in links)
        return answer
    except Exception:
        traceback.print_exc()
        return "Desculpe, ocorreu um erro ao consultar a base. Tente reindexar com --ingest."

def math_answer(query: str) -> str:
    # Sem ferramentas extras: o próprio LLM responde.
    # Se quiser, você pode plugar um agente de calculadora depois.
    math_prompt = ChatPromptTemplate.from_template(
        "Resolva passo a passo, em português, depois dê a resposta final clara. Pergunta: {q}"
    )
    chain = math_prompt | model
    return chain.invoke({"q": query})

# -----------------------------------------------------------------------------
# CLI / Interactive
# -----------------------------------------------------------------------------
def interactive_loop():
    while True:
        print("\n\n-------------------------------")
        question = input("Ask your question (q to quit): ")
        print("\n\n")
        if question.strip().lower() == "q":
            break

        route = router_chain.invoke({"question": question}).strip().lower()
        if route not in {"knowledge", "math"}:
            route = "knowledge"  # default

        if route == "knowledge":
            print(knowledge_answer(question))
        else:
            print(math_answer(question))

def main():
    parser = argparse.ArgumentParser(description="InfinitePay RAG with LangChain + Ollama (incremental).")
    sub = parser.add_subparsers(dest="cmd")

    # Ingest command
    p_ingest = sub.add_parser("ingest", help="Crawl + embed + persist the InfinitePay help center.")
    p_ingest.add_argument("--sitemap", default=DEFAULT_SITEMAP, help="Sitemap URL.")
    p_ingest.add_argument("--seed", default=DEFAULT_SEED, help="Seed URL for recursive crawl fallback.")
    p_ingest.add_argument("--no-sitemap", action="store_true", help="Skip sitemap and force recursive crawl.")
    p_ingest.add_argument("--max-depth", type=int, default=3, help="Max recursive depth when crawling.")
    p_ingest.add_argument("--timeout", type=int, default=10, help="HTTP timeout per request.")
    p_ingest.add_argument("--chunk-size", type=int, default=800)
    p_ingest.add_argument("--chunk-overlap", type=int, default=120)

    # Ask once (non-interactive)
    p_ask = sub.add_parser("ask", help="Ask one question against the persisted vector DB.")
    p_ask.add_argument("--q", required=True, help="Your question.")
    p_ask.add_argument("--route", choices=["auto", "knowledge", "math"], default="auto", help="Force a route or auto.")

    args = parser.parse_args()

    if args.cmd == "ingest":
        ingest_command(args)
        return

    if args.cmd == "ask":
        if args.route == "auto":
            route = router_chain.invoke({"question": args.q}).strip().lower()
            if route not in {"knowledge", "math"}:
                route = "knowledge"
        else:
            route = args.route

        if route == "knowledge":
            print(knowledge_answer(args.q))
        else:
            print(math_answer(args.q))
        return

    # If no subcommand: fall back to the original interactive loop
    interactive_loop()

if __name__ == "__main__":
    main()
