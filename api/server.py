from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from typing import AsyncGenerator, Iterable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from agents.router_agent import RouterAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.math_agent import MathAgent
from services.redis_service import RedisService
from api.schemas.chat_request import ChatRequest
from api.schemas.chat_response import ChatResponse
from utils.text_sanitazation import sanitize_text
from config.settings import (
    REDIS_URL, REDIS_LOG_STREAM, REDIS_CONV_TTL_SECONDS,
    RATE_LIMIT_WINDOW_SEC, RATE_LIMIT_MAX_REQUESTS,
)

app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
redis_service = RedisService(REDIS_URL, REDIS_LOG_STREAM, REDIS_CONV_TTL_SECONDS)
router = RouterAgent()
knowledge_agent = KnowledgeAgent()
math_agent = MathAgent()

def _fallback_stream(text: str, chunk_size: int = 20) -> Iterable[str]:
    # Se um agente não suportar streaming real, ainda enviamos pedaços
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]

def _agent_stream(agent, question: str) -> Iterable[str]:
    # Usa process_stream se existir; caso contrário, faz fallback
    if hasattr(agent, "process_stream"):
        return agent.process_stream(question)  # deve ser um iterador de tokens/strings
    # Fallback: process bloqueante e fatia
    full = agent.process(question)
    return _fallback_stream(full)

@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    # HTTP não-stream (útil para testes/e2e)
    user_id = body.user_id
    conversation_id = body.conversation_id
    message = sanitize_text(body.message)

    allowed, _ = redis_service.rate_limit_allow(user_id, RATE_LIMIT_WINDOW_SEC, RATE_LIMIT_MAX_REQUESTS)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    lock = redis_service.acquire_lock(conversation_id)
    if not lock:
        raise HTTPException(status_code=409, detail="Conversation is busy")

    try:
        redis_service.add_user_conversation(user_id, conversation_id)
        redis_service.append_message(conversation_id, "user", message, user_id=user_id)

        t0 = time.time()
        decision = router.process(message)
        t_router = (time.time() - t0) * 1000.0
        redis_service.log_json(level="INFO", agent="RouterAgent",
                               conversation_id=conversation_id, user_id=user_id,
                               execution_time_ms=t_router, decision=decision,
                               processed_content=message[:200])

        agent = knowledge_agent if decision == "knowledge" else math_agent

        t1 = time.time()
        response_full = "".join(_agent_stream(agent, message))
        t_agent = (time.time() - t1) * 1000.0

        redis_service.append_message(conversation_id, "assistant", response_full, user_id=user_id, agent=agent.__class__.__name__)
        redis_service.log_json(level="INFO", agent=agent.__class__.__name__,
                               conversation_id=conversation_id, user_id=user_id,
                               execution_time_ms=t_agent, processed_content=message[:200])

        return ChatResponse(
            response=response_full,
            source_agent_response=response_full,
            agent_workflow=[
                {"agent": "RouterAgent", "decision": "KnowledgeAgent" if decision == "knowledge" else "MathAgent"},
                {"agent": agent.__class__.__name__},
            ],
        )
    finally:
        redis_service.release_lock(conversation_id, lock)

@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    try:
        # Primeiro pacote do cliente deve conter user_id, conversation_id e message
        raw = await ws.receive_text()
        try:
            payload = json.loads(raw)
        except Exception:
            await ws.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
            await ws.close(code=1003)
            return

        try:
            body = ChatRequest(**payload)
        except ValidationError as ve:
            await ws.send_text(json.dumps({"type": "error", "message": "Validation error", "details": ve.errors()}))
            await ws.close(code=1003)
            return

        user_id = body.user_id
        conversation_id = body.conversation_id
        message = sanitize_text(body.message)

        await ws.send_text(json.dumps({
            "type": "ack",
            "connection_id": str(uuid.uuid4()),
            "user_id": user_id,
            "conversation_id": conversation_id,
        }))

        allowed, remaining = redis_service.rate_limit_allow(user_id, RATE_LIMIT_WINDOW_SEC, RATE_LIMIT_MAX_REQUESTS)
        if not allowed:
            await ws.send_text(json.dumps({"type": "error", "message": "Rate limit exceeded"}))
            await ws.close(code=1011)
            return

        lock = redis_service.acquire_lock(conversation_id)
        if not lock:
            await ws.send_text(json.dumps({"type": "error", "message": "Conversation is busy"}))
            await ws.close(code=1013)
            return

        try:
            redis_service.add_user_conversation(user_id, conversation_id)
            redis_service.append_message(conversation_id, "user", message, user_id=user_id)

            t0 = time.time()
            decision = router.process(message)
            t_router = (time.time() - t0) * 1000.0
            redis_service.log_json(level="INFO", agent="RouterAgent",
                                   conversation_id=conversation_id, user_id=user_id,
                                   execution_time_ms=t_router, decision=decision,
                                   processed_content=message[:200])

            agent = knowledge_agent if decision == "knowledge" else math_agent
            await ws.send_text(json.dumps({
                "type": "workflow",
                "agent_workflow": [
                    {"agent": "RouterAgent", "decision": "KnowledgeAgent" if decision == "knowledge" else "MathAgent"},
                    {"agent": agent.__class__.__name__},
                ]
            }))

            # Streaming do agente
            t1 = time.time()
            # Se o agente suportar streaming real, isso enviará tokens conforme gerados
            for token in _agent_stream(agent, message):
                await ws.send_text(json.dumps({"type": "token", "data": token}))
                await asyncio.sleep(0)  # cooperativo

            t_agent = (time.time() - t1) * 1000.0

            # Como _agent_stream pode ser fallback, reconstruímos a resposta completa via Redis last message ou acumulador local.
            # Para simplicidade, recomputamos de forma determinística:
            final_text = "".join(_agent_stream(agent, message))
            redis_service.append_message(conversation_id, "assistant", final_text, user_id=user_id, agent=agent.__class__.__name__)
            redis_service.log_json(level="INFO", agent=agent.__class__.__name__,
                                   conversation_id=conversation_id, user_id=user_id,
                                   execution_time_ms=t_agent, processed_content=message[:200])

            await ws.send_text(json.dumps({
                "type": "final",
                "response": final_text,
                "agent_workflow": [
                    {"agent": "RouterAgent", "decision": "KnowledgeAgent" if decision == "knowledge" else "MathAgent"},
                    {"agent": agent.__class__.__name__},
                ],
            }))
        finally:
            redis_service.release_lock(conversation_id, lock)

    except WebSocketDisconnect:
        # Cliente desconectou
        return
    except Exception as e:
        await ws.send_text(json.dumps({"type": "error", "message": "Internal error"}))
        await ws.close(code=1011)