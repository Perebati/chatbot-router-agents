from __future__ import annotations
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, Iterable

from redis import Redis
from datetime import datetime, timezone

import inspect
from typing import cast


class RedisService:
    def __init__(self, url: str, log_stream: str = "logs:chat", conv_ttl_seconds: int = 7 * 24 * 3600):
        # explicitly annotate as sync Redis client to help Pylance
        self.client: Redis = Redis.from_url(url, decode_responses=True)
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
        # rpush returns int (list length); cast to int for type clarity
        _ = cast(int, self.client.rpush(key, json.dumps(msg)))
        # Ensure TTL
        ttl = cast(int, self.client.ttl(key))
        if ttl == -1:
            # expire returns bool/int, ignore return value
            _ = cast(int, self.client.expire(key, self.conv_ttl))

    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        key = f"conv:{conversation_id}:messages"

        # llen may be sync int or an awaitable in some environments; guard for both
        length_raw = self.client.llen(key)
        if inspect.isawaitable(length_raw):
            # run to completion (rare in normal sync runtime) to give a concrete int
            import asyncio

            length = int(asyncio.get_event_loop().run_until_complete(length_raw))
        else:
            length = int(cast(int, length_raw))

        start = max(0, length - limit)
        raw = self.client.lrange(key, start, -1)
        if inspect.isawaitable(raw):
            import asyncio
            raw = asyncio.get_event_loop().run_until_complete(raw)  # type: ignore

        # ensure elements are strings
        def to_str(x: Union[bytes, str]) -> str:
            return x.decode() if isinstance(x, (bytes, bytearray)) else str(x)

        return [json.loads(to_str(x)) for x in raw]

    # User → conversations index
    def add_user_conversation(self, user_id: str, conversation_id: str) -> None:
        _ = cast(int, self.client.sadd(f"user:{user_id}:conversations", conversation_id))

    def list_user_conversations(self, user_id: str) -> List[str]:
        members = self.client.smembers(f"user:{user_id}:conversations")
        if inspect.isawaitable(members):
            import asyncio
            members = asyncio.get_event_loop().run_until_complete(members)  # type: ignore

        # members may be set of bytes or strings
        def _dec(x: Union[bytes, str]) -> str:
            return x.decode() if isinstance(x, (bytes, bytearray)) else str(x)

        return sorted(_dec(m) for m in cast(Iterable[Union[bytes, str]], members))

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
        payload: Dict[str, str] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "agent": agent,
            "conversation_id": conversation_id or "",
            "user_id": user_id or "",
        }
        if execution_time_ms is not None:
            # redis stream fields must be strings; stringify floats
            payload["execution_time"] = str(execution_time_ms)
        if decision is not None:
            payload["decision"] = decision
        if processed_content is not None:
            payload["processed_content"] = processed_content
        if extra:
            for k, v in extra.items():
                payload[f"extra.{k}"] = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
        # xadd returns an id (bytes/str); cast to str for callers
        # cast to Any mapping to satisfy redis-py type expectations
        # cast to Any and ignore type-checker for this call to satisfy redis-py signature
        res = self.client.xadd(self.log_stream, cast(Any, payload))  # type: ignore[arg-type]
        if inspect.isawaitable(res):
            import asyncio
            res = asyncio.get_event_loop().run_until_complete(res)  # type: ignore
        return cast(str, res)

    # Rate limiting
    def rate_limit_allow(self, user_id: str, window_sec: int, max_requests: int) -> Tuple[bool, int]:
        now_window = int(time.time() // window_sec)
        key = f"rl:{user_id}:{now_window}"
        current_raw = self.client.incr(key)
        if inspect.isawaitable(current_raw):
            import asyncio
            current = int(asyncio.get_event_loop().run_until_complete(current_raw))
        else:
            current = int(cast(int, current_raw))

        if current == 1:
            _ = cast(bool, self.client.expire(key, window_sec))
        remaining = max(0, max_requests - int(current))
        return (int(current) <= max_requests, remaining)

    # Router cache
    def get_router_decision(self, q_hash: str) -> Optional[str]:
        res = self.client.get(f"router:decision:{q_hash}")
        if inspect.isawaitable(res):
            import asyncio
            res = asyncio.get_event_loop().run_until_complete(res)  # type: ignore
        return cast(Optional[str], res)

    def set_router_decision(self, q_hash: str, decision: str, ttl_sec: int = 24 * 3600) -> None:
        _ = cast(bool, self.client.setex(f"router:decision:{q_hash}", ttl_sec, decision))

    # Simple lock per conversation to avoid concurrent processing overlap
    def acquire_lock(self, conversation_id: str, ttl_ms: int = 10000) -> Optional[str]:
        lock_key = f"lock:conv:{conversation_id}"
        lock_val = str(uuid.uuid4())
        ok_raw = self.client.set(lock_key, lock_val, nx=True, px=ttl_ms)
        if inspect.isawaitable(ok_raw):
            import asyncio
            ok = asyncio.get_event_loop().run_until_complete(ok_raw)  # type: ignore
        else:
            ok = bool(cast(int, ok_raw))
        return lock_val if ok else None

    def release_lock(self, conversation_id: str, lock_val: str) -> None:
        lock_key = f"lock:conv:{conversation_id}"
        # Use pipeline for atomicity in sync client
        pipe = self.client.pipeline()
        while True:
            try:
                pipe.watch(lock_key)
                current = pipe.get(lock_key)
                if inspect.isawaitable(current):
                    import asyncio
                    current = asyncio.get_event_loop().run_until_complete(current)  # type: ignore
                if current == lock_val:
                    pipe.multi()
                    pipe.delete(lock_key)
                    pipe.execute()
                pipe.unwatch()
                break
            except Exception:
                try:
                    pipe.unwatch()
                except Exception:
                    pass
                break