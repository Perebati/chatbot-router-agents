"""
Classe base para todos os agentes do sistema.
"""
from abc import ABC, abstractmethod
from typing import Iterable

class BaseAgent(ABC):
    """Classe base abstrata para todos os agentes."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    def process(self, query: str) -> str:
        """Processa uma query e retorna uma resposta."""
        pass
    