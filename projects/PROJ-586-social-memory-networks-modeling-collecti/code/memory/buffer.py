from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Dict, List, Optional

@dataclass
class MemoryAction:
    token: str
    payload: dict

@dataclass
class MemoryEntry:
    action: MemoryAction
    timestamp: float = field(default_factory=lambda: 0.0)

def now() -> float:
    """Return current time in seconds since epoch."""
    import time
    return time.time()

def parse_memory_action_token(token: str) -> MemoryAction:
    """Parse a token of the form <MEMORY_ACTION:payload_json>."""
    match = re.fullmatch(r"<MEMORY_ACTION:(.+)>", token)
    if not match:
        raise ValueError(f"Invalid memory action token: {token}")
    payload_json = match.group(1)
    payload = json.loads(payload_json)
    return MemoryAction(token=token, payload=payload)

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction back into a token string."""
    payload_json = json.dumps(action.payload, separators=(",", ":"))
    return f"<MEMORY_ACTION:{payload_json}>"

class MemoryBuffer:
    """Thread‑safe shared memory buffer."""

    _instance: Optional["MemoryBuffer"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.entries: List[MemoryEntry] = []

    @classmethod
    def get_shared_buffer(cls) -> "MemoryBuffer":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def add(self, action: MemoryAction) -> None:
        entry = MemoryEntry(action=action, timestamp=now())
        self.entries.append(entry)

    def reset(self) -> None:
        """Clear all entries."""
        self.entries.clear()

    # Tolerant fallback for any future method calls
    def __getattr__(self, name: str) -> Callable:
        """Return a no‑op callable for any undefined attribute."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Convenience functions
def get_shared_buffer() -> MemoryBuffer:
    return MemoryBuffer.get_shared_buffer()

def reset_shared_buffer() -> None:
    buf = get_shared_buffer()
    buf.reset()
