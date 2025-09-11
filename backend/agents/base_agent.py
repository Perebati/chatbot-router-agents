"""
Base Agent class that all other agents inherit from.
This defines the common interface and logging behavior.
"""
import time
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
    
    @abstractmethod
    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message and return the response.
        
        Args:
            message: The user's message
            context: Additional context (user_id, conversation_id, etc.)
        
        Returns:
            Dict with response and any additional data
        """
        pass
    
    def _log(self, level: str, data: Dict[str, Any], context: Dict[str, Any]):
        """Create structured logs for observability."""
        log_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "level": level,
            "agent": self.agent_name,
            "conversation_id": context.get("conversation_id", "unknown"),
            "user_id": context.get("user_id", "unknown"),
            **data
        }
        
        # For now, just print to console. Later we can send to a proper logging system
        print(json.dumps(log_entry, indent=2))
    
    def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with timing and logging.
        This is the main method that external code should call.
        """
        start_time = time.time()
        
        self._log("INFO", {"action": "started", "message_preview": message[:50]}, context)
        
        try:
            result = self.process(message, context)
            execution_time = time.time() - start_time
            
            self._log("INFO", {
                "action": "completed",
                "execution_time": round(execution_time, 3),
                "response_preview": result.get("response", "")[:50]
            }, context)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._log("ERROR", {
                "action": "failed",
                "execution_time": round(execution_time, 3),
                "error": str(e)
            }, context)
            raise