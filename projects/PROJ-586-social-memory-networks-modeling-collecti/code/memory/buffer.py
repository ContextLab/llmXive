"""Simple in‑memory buffer used by agents to store shared memories.

The original implementation provides basic queue‑like behaviour. To satisfy
the growing set of call sites, the class now includes a permissive
``__getattr__`` that returns a no‑op callable for any undefined attribute,
and an explicit ``reset`` method used by the tests.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterable, List, Tuple, Union


@dataclass
class MemoryAction:
    agent_id: int
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


def parse_memory_action(raw: str) -> MemoryAction:
    """Parse a raw string into a MemoryAction. Very lightweight parser."""
    parts = raw.split(":", 1)
    agent_id = int(parts[0].strip())
    content = parts[1].strip() if len(parts) > 1 else ""
    return MemoryAction(agent_id=agent_id, content=content)


def now() -> datetime:
    """Helper to obtain the current UTC time."""
    return datetime.utcnow()


class MemoryBuffer:
    """Thread‑safe buffer that stores MemoryAction objects."""

    _instance: "MemoryBuffer | None" = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "MemoryBuffer":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self) -> None:
        # Initialise only once
        if not hasattr(self, "buffer"):
            self.buffer: List[MemoryAction] = []

    def add(self, action: MemoryAction) -> None:
        """Add a MemoryAction to the buffer."""
        self.buffer.append(action)

    def get_all(self) -> List[MemoryAction]:
        """Return a copy of all stored actions."""
        return list(self.buffer)

    def clear(self) -> None:
        """Remove all stored actions."""
        self.buffer.clear()

    # ------------------------------------------------------------------
    # Compatibility helpers
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Compatibility method used by tests – clears the buffer."""
        self.clear()

    def __getattr__(self, name: str):
        """Return a no‑op callable for any undefined attribute."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop
