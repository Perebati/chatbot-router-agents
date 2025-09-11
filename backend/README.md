# BTC Sideproject ChatAI - Backend

A simple modular chatbot system with agent routing, built with FastAPI.

## 🏗️ Architecture

- **RouterAgent**: Decides which specialized agent should handle each message
- **KnowledgeAgent**: Handles InfinitePay-related questions (currently with hardcoded responses)
- **MathAgent**: Processes mathematical calculations
- **FastAPI**: REST API that coordinates the agents

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Test the Agents
```bash
python test_agents.py
```

### 3. Start the Server
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 📡 API Usage

### Send a Chat Message
```bash
POST /chat
{
  "message": "Qual é a taxa da maquininha?",
  "user_id": "user123",
  "conversation_id": "conv456"  // optional
}
```

### Response Format
```json
{
  "response": "As taxas da InfinitePay variam...",
  "source_agent_response": "As taxas da InfinitePay variam...",
  "agent_workflow": [
    {"agent": "RouterAgent", "decision": "KnowledgeAgent"},
    {"agent": "KnowledgeAgent"}
  ]
}
```

## 🧪 Example Messages

Try these messages to test different agents:

**Knowledge Queries:**
- "Qual é a taxa da maquininha?"
- "O que é PIX?"
- "Como funciona o cartão InfinitePay?"

**Math Queries:**
- "How much is 10 x 5?"
- "Calculate 100 / 4"
- "What is 25 + 15?"

## 📊 Logs

All agents generate structured JSON logs that you'll see in the console:
```json
{
  "timestamp": "2025-09-26T22:05:12Z",
  "level": "INFO",
  "agent": "RouterAgent",
  "conversation_id": "conv456",
  "user_id": "user123",
  "decision": "KnowledgeAgent"
}
```

## 🔄 Next Steps

This is a learning-focused implementation. Future improvements:
- Replace hardcoded knowledge with real RAG system
- Add Redis for conversation persistence
- Implement proper security measures
- Add more sophisticated routing logic
- Create comprehensive tests