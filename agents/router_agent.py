"""
Agente roteador que classifica perguntas entre knowledge e math.
"""
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseAgent
from config.settings import ROUTER_MODEL


class RouterAgent(BaseAgent):
    """Agente responsável por rotear perguntas para o agente apropriado."""
    
    def __init__(self):
        super().__init__(ROUTER_MODEL)
        self.model = OllamaLLM(model=self.model_name)
        self.template = """
You are a RouterAgent.
Your goal is to analyze the user question and classify it into one of two categories:

- "knowledge" - for questions about InfinitePay app, features, help, or support
- "math" - for questions involving mathematical calculations or expressions

User question: {question}

You must respond with exactly one word: either "knowledge" or "math". Nothing else.

Classification:"""
        
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.chain = self.prompt | self.model
    
    def process(self, query: str) -> str:
        """
        Classifica a query e retorna 'knowledge' ou 'math'.
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            str: 'knowledge' ou 'math'
        """
        result = self.chain.invoke({"question": query}).strip().lower()
        
        # Garantir que a resposta seja válida
        if result not in {"knowledge", "math"}:
            return "knowledge"  # default para knowledge
            
        return result