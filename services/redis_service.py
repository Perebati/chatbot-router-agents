from __future__ import annotations
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from redis import Redis
from datetime import datetime, timezone


class RedisService:
    def __init__(self, url: str, log_stream: str = "logs:chat", conv_ttl_seconds: int = 7 * 24 * 3600):
        self.client = Redis.from_url(url, decode_responses=True)
        self.log_stream = log_stream
        self.conv_ttl = conv_ttl_seconds

    # Conversation storage
    def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        user_id: Optional[str] = None,
        agent: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        key = f"conv:{conversation_id}:messages"
        msg = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "content": content,
            "agent": agent,
            "user_id": user_id,
            "extra": extra or {},
        }
        self.client.rpush(key, json.dumps(msg))
        # Ensure TTL
        if self.client.ttl(key) == -1:
            self.client.expire(key, self.conv_ttl)

    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        key = f"conv:{conversation_id}:messages"
        length = self.client.llen(key)
        start = max(0, length - limit)
        raw = self.client.lrange(key, start, -1)
        return [json.loads(x) for x in raw]

    # User → conversations index
    def add_user_conversation(self, user_id: str, conversation_id: str) -> None:
        self.client.sadd(f"user:{user_id}:conversations", conversation_id)

    def list_user_conversations(self, user_id: str) -> List[str]:
        return sorted(self.client.smembers(f"user:{user_id}:conversations"))

    # Structured logs via Streams
    def log_json(
        self,
        *,
        level: str,
        agent: str,
        conversation_id: Optional[str],
        user_id: Optional[str],
        execution_time_ms: Optional[float] = None,
        decision: Optional[str] = None,
        processed_content: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "agent": agent,
            "conversation_id": conversation_id or "",
            "user_id": user_id or "",
        }
        if execution_time_ms is not None:
            payload["execution_time"] = execution_time_ms
        if decision is not None:
            payload["decision"] = decision
        if processed_content is not None:
            payload["processed_content"] = processed_content
        if extra:
            for k, v in extra.items():
                payload[f"extra.{k}"] = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
        return self.client.xadd(self.log_stream, payload)

    # Rate limiting
    def rate_limit_allow(self, user_id: str, window_sec: int, max_requests: int) -> Tuple[bool, int]:
        now_window = int(time.time() // window_sec)
        key = f"rl:{user_id}:{now_window}"
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window_sec)
        remaining = max(0, max_requests - int(current))
        return (current <= max_requests, remaining)

    # Router cache
    def get_router_decision(self, q_hash: str) -> Optional[str]:
        return self.client.get(f"router:decision:{q_hash}")

    def set_router_decision(self, q_hash: str, decision: str, ttl_sec: int = 24 * 3600) -> None:
        self.client.setex(f"router:decision:{q_hash}", ttl_sec, decision)

    # Simple lock per conversation to avoid concurrent processing overlap
    def acquire_lock(self, conversation_id: str, ttl_ms: int = 10000) -> Optional[str]:
        lock_key = f"lock:conv:{conversation_id}"
        lock_val = str(uuid.uuid4())
        ok = self.client.set(lock_key, lock_val, nx=True, px=ttl_ms)
        return lock_val if ok else None

    def release_lock(self, conversation_id: str, lock_val: str) -> None:
        lock_key = f"lock:conv:{conversation_id}"
        pipe = self.client.pipeline()
        while True:
            try:
                pipe.watch(lock_key)
                if pipe.get(lock_key) == lock_val:
                    pipe.multi()
                    pipe.delete(lock_key)
                    pipe.execute()
                pipe.unwatch()
                break
            except Exception:
                pipe.unwatch()
                break