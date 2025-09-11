"""
MathAgent - Handles simple mathematical calculations.
Starting with basic eval() approach. Later we can make it safer.
"""
import re
from typing import Dict, Any
from .base_agent import BaseAgent


class MathAgent(BaseAgent):
    """Handles mathematical calculations and expressions."""
    
    def __init__(self):
        super().__init__("MathAgent")
    
    def _extract_math_expression(self, message: str) -> str:
        """Extract and clean the mathematical expression from the message."""
        message = message.lower()
        
        # Replace common words with operators
        replacements = {
            'x': '*',
            '×': '*',
            '÷': '/',
            'vezes': '*',
            'mais': '+',
            'menos': '-',
            'dividido por': '/',
            'multiplicado por': '*'
        }
        
        for word, operator in replacements.items():
            message = message.replace(word, operator)
        
        # Extract numbers and operators
        expression_pattern = r'[\d+\-*/().\s]+'
        matches = re.findall(expression_pattern, message)
        
        if matches:
            # Take the longest match (most complete expression)
            expression = max(matches, key=len).strip()
            return expression
        
        return ""
    
    def _safe_evaluate(self, expression: str) -> float:
        """Safely evaluate a mathematical expression."""
        # Remove any spaces
        expression = expression.replace(' ', '')
        
        # Only allow safe characters (numbers, operators, parentheses, decimal point)
        if not re.match(r'^[0-9+\-*/().\s]+$', expression):
            raise ValueError("Invalid characters in expression")
        
        try:
            # Use eval with restricted environment for safety
            # In production, you'd want a proper math parser
            result = eval(expression, {"__builtins__": {}}, {})
            return float(result)
        except Exception as e:
            raise ValueError(f"Could not evaluate expression: {str(e)}")
    
    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a math query and return the calculation result."""
        
        try:
            # Extract the math expression
            expression = self._extract_math_expression(message)
            
            if not expression:
                return {
                    "response": "Desculpe, não consegui identificar uma expressão matemática válida na sua mensagem.",
                    "error": "No valid expression found",
                    "agent_type": "math"
                }
            
            # Calculate the result
            result = self._safe_evaluate(expression)
            
            # Format the response nicely
            if result == int(result):
                result_str = str(int(result))
            else:
                result_str = f"{result:.2f}"
            
            response = f"O resultado de {expression} é {result_str}."
            
            # Log what we processed
            self._log("INFO", {
                "processed_content": f"Calculated: {expression} = {result}",
                "expression": expression,
                "result": result
            }, context)
            
            return {
                "response": response,
                "expression": expression,
                "result": result,
                "agent_type": "math"
            }
            
        except Exception as e:
            self._log("ERROR", {
                "processed_content": f"Failed to calculate: {message}",
                "error": str(e)
            }, context)
            
            return {
                "response": "Desculpe, não consegui realizar esse cálculo. Verifique se a expressão está correta.",
                "error": str(e),
                "agent_type": "math"
            }