from pydantic import BaseModel

class ChatResponse(BaseModel):
    response: str
    source_agent_response: str
    agent_workflow: list[dict]