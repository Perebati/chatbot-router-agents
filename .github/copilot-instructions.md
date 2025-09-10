# Copilot Instructions - BTC Sideproject ChatAI

## Project Overview
This is a modular chatbot system demonstrating agent routing, RAG implementation, security, and observability. The system routes user messages between specialized agents (KnowledgeAgent for RAG-based queries, MathAgent for calculations) with comprehensive logging and conversation management.

## Architecture Components

### Agent System
- **RouterAgent**: Central orchestrator that analyzes messages and routes to appropriate specialized agents
- **KnowledgeAgent**: RAG implementation using content from https://ajuda.infinitepay.io/pt-BR/ 
- **MathAgent**: LLM-powered mathematical expression interpreter
- All agents must generate structured JSON logs with execution time, decisions, and context

### API Structure
- Single endpoint: `POST /chat` with payload: `{message, user_id, conversation_id}`
- Response format: `{response, source_agent_response, agent_workflow[]}`
- Agent workflow array tracks decision path: `[{agent: "RouterAgent", decision: "KnowledgeAgent"}, {agent: "KnowledgeAgent"}]`

### Data Flow
1. Message → RouterAgent → Decision logging → Specialized Agent → Response + logging
2. Conversation state managed via Redis using `conversation_id`
3. User context tracked via `user_id` for personalization/security

## Technology Stack Patterns

### Backend Structure
- Use dependency injection for agent management
- Implement agent interface/abstract class for consistent behavior
- Redis client for conversation persistence and optionally structured logging
- Environment-based configuration (API keys, Redis connection, etc.)

### Security Implementation
- Input sanitization: Strip HTML/JS, validate message length and format
- Prompt injection prevention: Template-based prompts with parameter injection, input validation
- Error handling: Custom exception classes, never expose internal errors to API responses

### Logging Standards
Required structured log fields:
```json
{
  "timestamp": "2025-08-07T14:32:12Z",
  "level": "INFO|DEBUG|ERROR", 
  "agent": "RouterAgent|KnowledgeAgent|MathAgent",
  "conversation_id": "string",
  "user_id": "string", 
  "execution_time": "number",
  "decision": "string (for RouterAgent)",
  "processed_content": "string (for processing agents)"
}
```

### Frontend Patterns (React)
- Conversation management: Multiple conversations via `conversation_id` switching
- Message display: Show agent attribution per response
- State management: Track active conversation, message history per conversation
- UI components: ChatMessage component showing agent workflow transparency

## Development Workflows

### Project Structure
```
├── backend/
│   ├── agents/          # RouterAgent, KnowledgeAgent, MathAgent classes
│   ├── services/        # Redis, logging, security services
│   ├── api/            # FastAPI/Flask route handlers
│   └── tests/          # Agent decision tests, math expression tests, E2E API tests
├── frontend/           # React app with conversation management
├── infrastructure/     # Docker, docker-compose, k8s YAML files  
└── .github/           # This file
```

### Key Implementation Notes
- **RAG Implementation**: Use LangChain/LlamaIndex for InfinitePay help center indexing
- **Agent Decision Logic**: RouterAgent should detect math expressions vs. knowledge queries via regex/NLP patterns
- **Redis Schema**: `conv:{conversation_id}:messages` for message history, `user:{user_id}:conversations` for user's conversation list
- **Math Agent**: Handle expressions like `"65 x 3.11"`, `"70 + 12"`, `"(42 * 2) / 6"` - parse natural language math into evaluable expressions

### Testing Strategy
- Unit tests: Agent decision accuracy, math expression parsing, sanitization functions
- Integration tests: Redis conversation persistence, logging format validation
- E2E tests: Complete `/chat` API flows with different message types
- Load testing: Multiple concurrent conversations

### Infrastructure Requirements  
- Docker: Multi-stage builds for frontend/backend
- docker-compose: Include Redis, backend, frontend services with proper networking
- Kubernetes: Separate deployments for each service, Redis StatefulSet, Ingress for external access
- Environment variables: Database URLs, API keys, logging levels

## Critical Patterns
- Always log before and after agent execution with timing
- Sanitize inputs before any LLM interaction
- Maintain conversation context in Redis with TTL
- Agent responses must be deterministic for the same input (cache when possible)
- Handle Redis connection failures gracefully (fallback to in-memory for dev)

## Example Implementation Flow
1. `/chat` endpoint receives message → validate and sanitize
2. RouterAgent analyzes message → logs decision rationale  
3. Specialized agent processes → logs execution time and sources
4. Response assembly → logs final response structure
5. Redis persistence → conversation history update
6. Return structured response with agent workflow transparency