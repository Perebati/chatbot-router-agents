"""
Serviço para crawling e extração de conteúdo web.
"""
from typing import List

from langchain_community.document_loaders import RecursiveUrlLoader

from config.settings import (
    DEFAULT_SEED,
    BASE_URL, 
    LINK_REGEX,
    USER_AGENT,
    DEFAULT_MAX_DEPTH,
    DEFAULT_TIMEOUT
)
from utils.text_utils import bs4_extractor


class CrawlingService:
    """Serviço para fazer crawling de sites e extrair conteúdo."""
    
    def __init__(self):
        self.headers = {"User-Agent": USER_AGENT}
    
    def crawl_knowledge_base(
        self,
        seed_url: str = DEFAULT_SEED,
        max_depth: int = DEFAULT_MAX_DEPTH,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> List:
        """
        Faz crawling da base de conhecimento usando recursive loader.
        
        Args:
            seed_url: URL inicial para o crawling
            max_depth: Profundidade máxima do crawling
            timeout: Timeout para cada requisição
            
        Returns:
            List: Lista de documentos carregados
            
        Raises:
            Exception: Se o crawling falhar
        """
        print(f"[crawling] Iniciando crawling recursivo de: {seed_url}")
        
        try:
            loader = RecursiveUrlLoader(
                url=seed_url,
                max_depth=max_depth,
                extractor=bs4_extractor,
                timeout=timeout,
                headers=self.headers,
                check_response_status=True,
                continue_on_failure=True,
                prevent_outside=True,
                base_url=BASE_URL,
                link_regex=LINK_REGEX,  
            )
            
            docs = loader.load()
            print(f"[crawling] Carregados {len(docs)} documentos via crawling recursivo.")
            return docs
            
        except Exception as e:
            print(f"[crawling] Crawling recursivo falhou: {e}")
            raise