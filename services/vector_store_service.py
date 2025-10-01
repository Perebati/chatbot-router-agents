"""
Serviço para gerenciar o banco de dados vetorial (Chroma).
"""
import os
from typing import List

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import (
    PERSIST_DIR, 
    COLLECTION_NAME, 
    EMBED_MODEL,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP
)


class VectorStoreService:
    """Serviço para operações com o banco de dados vetorial."""
    
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBED_MODEL)
        self._ensure_persist_dir()
    
    def _ensure_persist_dir(self):
        """Garante que o diretório de persistência existe."""
        os.makedirs(PERSIST_DIR, exist_ok=True)
    
    def get_vectorstore(self) -> Chroma:
        """
        Retorna uma instância do vectorstore existente.
        
        Returns:
            Chroma: Instância do banco vetorial
        """
        return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=self.embeddings,
            collection_name=COLLECTION_NAME,
        )
    
    def build_vectorstore(self, chunks: List) -> Chroma:
        """
        Cria um novo vectorstore a partir de chunks de documentos.
        
        Args:
            chunks: Lista de chunks de documentos
            
        Returns:
            Chroma: Instância do banco vetorial criado
        """
        vectordb = Chroma.from_documents(
            chunks,
            embedding=self.embeddings,
            persist_directory=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
        )
        return vectordb
    
    def split_documents(
        self, 
        docs: List, 
        chunk_size: int = DEFAULT_CHUNK_SIZE, 
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ) -> List:
        """
        Divide documentos em chunks menores.
        
        Args:
            docs: Lista de documentos
            chunk_size: Tamanho do chunk
            chunk_overlap: Sobreposição entre chunks
            
        Returns:
            List: Lista de chunks
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap, 
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_documents(docs)