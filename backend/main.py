"""
FastAPI application for the BTC Sideproject ChatAI system.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

# Import our agents
from agents import RouterAgent, KnowledgeAgent, MathAgent


# Pydantic models for API requests and responses
class ChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: str = None  # Optional, we'll generate one if not provided


class AgentWorkflowStep(BaseModel):
    agent: str
    decision: str = None


class ChatResponse(BaseModel):
    response: str
    source_agent_response: str
    agent_workflow: List[AgentWorkflowStep]


# Initialize FastAPI app
app = FastAPI(
    title="BTC Sideproject ChatAI",
    description="A modular chatbot system with agent routing",
    version="1.0.0"
)

# Initialize agents
router_agent = RouterAgent()
knowledge_agent = KnowledgeAgent()
math_agent = MathAgent()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "BTC Sideproject ChatAI is running!", "status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that processes messages through the agent system.
    """
    try:
        # Generate conversation_id if not provided
        if not request.conversation_id:
            request.conversation_id = f"conv-{uuid.uuid4().hex[:8]}"
        
        # Create context for agents
        context = {
            "user_id": request.user_id,
            "conversation_id": request.conversation_id
        }
        
        # Initialize workflow tracking
        workflow = []
        
        # Step 1: Use RouterAgent to decide which agent should handle the message
        router_result = router_agent.execute(request.message, context)
        chosen_agent = router_result["agent"]
        
        workflow.append(AgentWorkflowStep(
            agent="RouterAgent", 
            decision=chosen_agent
        ))
        
        # Step 2: Execute the chosen specialized agent
        if chosen_agent == "KnowledgeAgent":
            agent_result = knowledge_agent.execute(request.message, context)
            workflow.append(AgentWorkflowStep(agent="KnowledgeAgent"))
        elif chosen_agent == "MathAgent":
            agent_result = math_agent.execute(request.message, context)
            workflow.append(AgentWorkflowStep(agent="MathAgent"))
        else:
            # Fallback to knowledge agent
            agent_result = knowledge_agent.execute(request.message, context)
            workflow.append(AgentWorkflowStep(agent="KnowledgeAgent"))
        
        # Step 3: Prepare the response
        response_text = agent_result.get("response", "Desculpe, não consegui processar sua mensagem.")
        
        return ChatResponse(
            response=response_text,
            source_agent_response=response_text,  # For now, same as response
            agent_workflow=workflow
        )
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error processing chat request: {str(e)}")
        
        # Return a user-friendly error message
        raise HTTPException(
            status_code=500,
            detail="Ocorreu um erro interno. Tente novamente mais tarde."
        )


@app.get("/health")
async def health_check():
    """Extended health check with agent status."""
    return {
        "status": "healthy",
        "agents": {
            "router": "active",
            "knowledge": "active", 
            "math": "active"
        },
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)