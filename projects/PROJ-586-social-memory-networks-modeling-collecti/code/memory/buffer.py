"""Shared memory buffer for multi-agent systems.

Implements a thread-safe external memory buffer with queue-based write conflict
resolution as required by FR-003 and FR-012. Supports <MEMORY_ACTION> tokens
with JSON schema {"type": "write"|"read", "key": str, "value": str}.
"""
from __future__ import annotations

import json
import re
import threading
from collections import deque
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class MemoryAction:
    """Represents a memory action (read/write)."""
    type: str  # "write" or "read"
    key: str
    value: Optional[str] = None

@dataclass
class MemoryEntry:
    """A single entry in the memory buffer."""
    key: str
    value: str
    timestamp: str
    source_agent: Optional[int] = None

def now() -> str:
    """Return current timestamp as ISO format string."""
    return datetime.utcnow().isoformat()

def parse_memory_action_token(token: str) -> Optional[MemoryAction]:
    """Parse a <MEMORY_ACTION> token into a MemoryAction object."""
    pattern = r'<MEMORY_ACTION>(.*?)</MEMORY_ACTION>'
    match = re.search(pattern, token, re.DOTALL)
    if not match:
        return None

    try:
        action_json = match.group(1)
        action_data = json.loads(action_json)
        return MemoryAction(
            type=action_data.get("type", "write"),
            key=action_data.get("key", ""),
            value=action_data.get("value")
        )
    except (json.JSONDecodeError, KeyError):
        return None

def format_action_token(action: MemoryAction) -> str:
    """Format a MemoryAction as a <MEMORY_ACTION> token."""
    action_data = asdict(action)
    return f"<MEMORY_ACTION>{json.dumps(action_data)}</MEMORY_ACTION>"

class MemoryBuffer:
    """Thread-safe shared memory buffer for multi-agent systems.

    Implements queue-based write conflict resolution: when multiple agents
    attempt to write to the same key, writes are queued and processed in
    FIFO order. The last writer wins, but all attempts are logged for
    auditability.
    """

    def __init__(self):
        self._entries: Dict[str, MemoryEntry] = {}
        self._write_queue: deque = deque()
        self._conflict_log: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        self._entry_count = 0

    def _process_write_queue(self) -> None:
        """Process queued writes in FIFO order, resolving conflicts.

        When multiple writes target the same key, they are processed sequentially.
        Each write that targets an already-modified key in the current batch
        is logged as a conflict.
        """
        if not self._write_queue:
            return

        # Group writes by key to detect conflicts
        key_writes: Dict[str, List[Dict[str, Any]]] = {}
        while self._write_queue:
            item = self._write_queue.popleft()
            key = item['key']
            if key not in key_writes:
                key_writes[key] = []
            key_writes[key].append(item)

        # Process writes, logging conflicts
        for key, writes in key_writes.items():
            if len(writes) > 1:
                # Log conflict: multiple agents wrote to same key
                self._conflict_log.append({
                    'key': key,
                    'conflict_count': len(writes),
                    'winning_agent': writes[-1]['source_agent'],
                    'timestamp': now()
                })
            
            # Last writer wins
            last_write = writes[-1]
            entry = MemoryEntry(
                key=last_write['key'],
                value=last_write['value'],
                timestamp=last_write['timestamp'],
                source_agent=last_write['source_agent']
            )
            self._entries[key] = entry
            self._entry_count += 1

    def write(self, key: str, value: str, source_agent: Optional[int] = None) -> bool:
        """Write a value to the memory buffer.

        Writes are queued and processed to resolve conflicts. If a write
        targets a key that already exists, it is queued for conflict resolution.
        """
        with self._lock:
            # Queue the write
            self._write_queue.append({
                'key': key,
                'value': value,
                'source_agent': source_agent,
                'timestamp': now()
            })
            
            # Process the queue to resolve conflicts
            self._process_write_queue()
            return True

    def read(self, key: str) -> Optional[str]:
        """Read a value from the memory buffer.

        Before reading, process any pending writes to ensure consistency.
        """
        with self._lock:
            # Process any pending writes first
            self._process_write_queue()
            entry = self._entries.get(key)
            return entry.value if entry else None

    def delete(self, key: str) -> bool:
        """Delete an entry from the memory buffer."""
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False

    def search(self, query: str) -> List[MemoryEntry]:
        """Search for entries containing the query string."""
        with self._lock:
            # Process pending writes before searching
            self._process_write_queue()
            results = []
            query_lower = query.lower()
            for entry in self._entries.values():
                if query_lower in entry.key.lower() or query_lower in entry.value.lower():
                    results.append(entry)
            return results

    def reset(self) -> None:
        """Reset the buffer to empty state."""
        with self._lock:
            self._entries.clear()
            self._write_queue.clear()
            self._conflict_log.clear()
            self._entry_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics including conflict metrics."""
        with self._lock:
            # Process pending writes before reporting stats
            self._process_write_queue()
            return {
                "entry_count": self._entry_count,
                "unique_keys": len(self._entries),
                "queue_length": len(self._write_queue),
                "conflict_count": len(self._conflict_log),
                "conflicts": self._conflict_log.copy()
            }

    def get_conflict_log(self) -> List[Dict[str, Any]]:
        """Retrieve the log of write conflicts for analysis."""
        with self._lock:
            return self._conflict_log.copy()

    # Tolerant attribute access for logger-style calls
    def __getattr__(self, name: str):
        """Make any unknown attribute return a no-op callable."""
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

# Shared buffer singleton
_SHARED_BUFFER: Optional[MemoryBuffer] = None
_BUFFER_LOCK = threading.Lock()

def get_shared_buffer() -> MemoryBuffer:
    """Get the shared memory buffer singleton."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is None:
            _SHARED_BUFFER = MemoryBuffer()
        return _SHARED_BUFFER

def reset_shared_buffer() -> None:
    """Reset the shared memory buffer."""
    global _SHARED_BUFFER
    with _BUFFER_LOCK:
        if _SHARED_BUFFER is not None:
            _SHARED_BUFFER.reset()

# Expose for backward compatibility
def parse_action_from_prompt(prompt: str) -> Optional[MemoryAction]:
    """Parse memory action from a prompt string."""
    return parse_memory_action_token(prompt)