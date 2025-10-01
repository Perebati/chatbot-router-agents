"""
Agente de conhecimento que responde usando RAG.
"""
import traceback
from typing import List, Tuple

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseAgent
from config.settings import ROUTER_MODEL
from services.vector_store_service import VectorStoreService


class KnowledgeAgent(BaseAgent):
    """Agente que responde perguntas usando RAG sobre a base do InfinitePay."""
    
    def __init__(self):
        super().__init__(ROUTER_MODEL)
        self.model = OllamaLLM(model=self.model_name)
        self.vector_service = VectorStoreService()
        
        self.template = """
Você é um assistente de suporte da InfinitePay. Responda em português do Brasil.
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
        
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.chain = self.prompt | self.model
    
    def _retrieve_context(self, query: str, k: int = 5) -> Tuple[str, List]:
        """Recupera contexto relevante da base vetorial."""
        try:
            vectordb = self.vector_service.get_vectorstore()
            retriever = vectordb.as_retriever(search_kwargs={"k": k})
            docs = retriever.invoke(query)
            
            parts = []
            for i, d in enumerate(docs, start=1):
                src = d.metadata.get("source") or d.metadata.get("link") or d.metadata.get("url") or "N/A"
                parts.append(f"[{i}] Fonte: {src}\n{d.page_content.strip()}")
            
            return "\n\n---\n\n".join(parts), docs
        except Exception:
            return "", []
    
    def process(self, query: str) -> str:
        """
        Processa uma pergunta de conhecimento usando RAG.
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            str: Resposta baseada na base de conhecimento
        """
        try:
            context, docs = self._retrieve_context(query, k=5)
            
            if not context:
                return "Desculpe, não encontrei informações relevantes na base de conhecimento."
            
            answer = self.chain.invoke({"question": query, "context": context})
            
            # Adicionar links das fontes
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