"""
RouterAgent - Decides which specialized agent should handle the message.
Keeps it simple with keyword-based routing for now.
"""
import re
from typing import Dict, Any
from .base_agent import BaseAgent


class RouterAgent(BaseAgent):
    """Routes messages to the appropriate specialized agent."""
    
    def __init__(self):
        super().__init__("RouterAgent")
        
        # Simple patterns to detect math expressions
        self.math_patterns = [
            r'\d+\s*[\+\-\*\/x×÷]\s*\d+',  # Basic operations like "5 + 3" or "10 x 2"
            r'\d+\s*\*\s*\d+',              # Multiplication with *
            r'\d+\s*\/\s*\d+',              # Division
            r'\(\d+.*\)',                   # Expressions in parentheses
            r'how much is',                 # Natural language math questions
            r'what is \d+',                 # "What is 5 + 3?"
            r'calculate',                   # "Calculate 10 * 5"
        ]
        
        # Keywords that suggest knowledge queries (InfinitePay related)
        self.knowledge_keywords = [
            'taxa', 'fee', 'maquininha', 'cartão', 'card', 'infinitepay',
            'pagamento', 'payment', 'conta', 'account', 'transferência',
            'transfer', 'saldo', 'balance', 'pix', 'boleto'
        ]
    
    def _is_math_query(self, message: str) -> bool:
        """Check if the message looks like a math query."""
        message_lower = message.lower()
        
        # Check against math patterns
        for pattern in self.math_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _is_knowledge_query(self, message: str) -> bool:
        """Check if the message looks like a knowledge query."""
        message_lower = message.lower()
        
        # Check for InfinitePay related keywords
        for keyword in self.knowledge_keywords:
            if keyword in message_lower:
                return True
        
        # If it's not clearly math and contains question words, assume knowledge
        question_words = ['what', 'how', 'when', 'where', 'why', 'qual', 'como', 'quando', 'onde', 'por que']
        if any(word in message_lower for word in question_words) and not self._is_math_query(message):
            return True
        
        return False
    
    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Decide which agent should handle this message."""
        
        # Simple routing logic
        if self._is_math_query(message):
            decision = "MathAgent"
            reasoning = "Detected mathematical expression or calculation request"
        elif self._is_knowledge_query(message):
            decision = "KnowledgeAgent" 
            reasoning = "Detected knowledge query or InfinitePay related question"
        else:
            # Default to knowledge agent for general queries
            decision = "KnowledgeAgent"
            reasoning = "Default routing for general queries"
        
        # Log the decision
        self._log("INFO", {
            "decision": decision,
            "reasoning": reasoning,
            "message": message
        }, context)
        
        return {
            "agent": decision,
            "reasoning": reasoning,
            "confidence": 0.8  # Simple confidence score
        }