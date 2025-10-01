"""
Agente matemático que resolve expressões e cálculos.
"""
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from .base_agent import BaseAgent
from config.settings import ROUTER_MODEL


class MathAgent(BaseAgent):
    """Agente que resolve problemas matemáticos."""
    
    def __init__(self):
        super().__init__(ROUTER_MODEL)
        self.model = OllamaLLM(model=self.model_name)
        
        self.template = """
                        Resolva passo a passo, em português, depois dê a resposta final clara. 

                        Pergunta: {question}

                        Resolução:
                        """
        
        self.prompt = ChatPromptTemplate.from_template(self.template)
        self.chain = self.prompt | self.model
    
    def process(self, query: str) -> str:
        """
        Resolve uma expressão ou problema matemático.
        
        Args:
            query: Pergunta matemática do usuário
            
        Returns:
            str: Solução passo a passo
        """
        return self.chain.invoke({"question": query})