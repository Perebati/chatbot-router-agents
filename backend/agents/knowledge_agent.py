"""
KnowledgeAgent - Handles questions about InfinitePay services.
Starting simple with hardcoded responses. Later we'll add RAG.
"""
from typing import Dict, Any
from .base_agent import BaseAgent


class KnowledgeAgent(BaseAgent):
    """Handles knowledge queries with predefined responses."""
    
    def __init__(self):
        super().__init__("KnowledgeAgent")
        
        # Simple knowledge base with common InfinitePay questions
        # In a real implementation, this would be replaced by RAG
        self.knowledge_base = {
            "taxa": "As taxas da InfinitePay variam de acordo com o plano escolhido. Para cartão de débito, a taxa é de 1,79% e para cartão de crédito é de 3,19%.",
            "maquininha": "A maquininha da InfinitePay aceita cartões de débito e crédito, além de pagamentos por aproximação (contactless) e QR Code.",
            "pix": "O PIX na InfinitePay é gratuito para recebimentos e tem liquidação imediata, caindo na sua conta na hora.",
            "conta": "A conta InfinitePay é digital, gratuita e oferece cartão de débito sem anuidade.",
            "cartão": "O cartão InfinitePay é aceito em milhões de estabelecimentos no Brasil e no exterior, sem anuidade.",
            "saldo": "Você pode consultar seu saldo pelo app InfinitePay, disponível para iOS e Android.",
            "transferência": "Transferências via PIX são gratuitas e instantâneas. TED e DOC têm taxas que variam conforme o plano.",
            "suporte": "O suporte InfinitePay está disponível 24/7 pelo app, WhatsApp ou telefone 0800.",
        }
    
    def _find_relevant_response(self, message: str) -> str:
        """Find the most relevant response based on keywords."""
        message_lower = message.lower()
        
        # Simple keyword matching
        for keyword, response in self.knowledge_base.items():
            if keyword in message_lower:
                return response
        
        # Default response if no specific match found
        return "Desculpe, não tenho informações específicas sobre isso. Para mais detalhes sobre os produtos e serviços da InfinitePay, consulte nosso site de ajuda ou entre em contato com nosso suporte."
    
    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a knowledge query and return a response."""
        
        # Find the most relevant response
        response = self._find_relevant_response(message)
        
        # Log what we processed
        self._log("INFO", {
            "processed_content": f"Matched knowledge query about: {message[:30]}...",
            "response_source": "hardcoded_knowledge_base"
        }, context)
        
        return {
            "response": response,
            "source": "InfinitePay Knowledge Base",
            "confidence": 0.7,
            "agent_type": "knowledge"
        }