"""
Shared memory buffer for multi-agent social memory networks.

This module provides a thread-safe memory buffer that agents can
use to store and retrieve shared information using <MEMORY_ACTION> tokens.
"""

import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import time

class MemoryAction(Enum):
    """Types of memory actions."""
    STORE = "store"
    RETRIEVE = "retrieve"
    DELETE = "delete"
    QUERY = "query"

@dataclass
class MemoryEntry:
    """Single memory entry in the buffer."""
    entry_id: int
    agent_id: int
    content: str
    action: MemoryAction
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryActionRequest:
    """Request to perform a memory action."""
    agent_id: int
    action: MemoryAction
    content: Optional[str] = None
    query: Optional[str] = None

@dataclass
class MemoryActionResult:
    """Result of a memory action."""
    success: bool
    entry_id: Optional[int] = None
    retrieved_content: Optional[str] = None
    message: str = ""

class MemoryBuffer:
    """
    Thread-safe shared memory buffer for multi-agent systems.
    
    Provides operations for:
    - Storing memory entries
    - Retrieving memory by query
    - Managing memory capacity
    - Tracking memory actions
    """
    
    def __init__(self, capacity: int = 1000):
        """
        Initialize memory buffer.
        
        Args:
            capacity: Maximum number of entries
        """
        self.capacity = capacity
        self.entries: List[MemoryEntry] = []
        self.entry_counter = 0
        self.lock = threading.RLock()
        self.action_history: List[Dict[str, Any]] = []
    
    def store(self, agent_id: int, content: str, metadata: Dict[str, Any] = None) -> MemoryActionResult:
        """
        Store a new memory entry.
        
        Args:
            agent_id: Agent storing the memory
            content: Memory content
            metadata: Optional metadata
        
        Returns:
            MemoryActionResult with success status
        """
        with self.lock:
            # Check capacity
            if len(self.entries) >= self.capacity:
                # Remove oldest entry
                self.entries.pop(0)
            
            # Create entry
            entry = MemoryEntry(
                entry_id=self.entry_counter,
                agent_id=agent_id,
                content=content,
                action=MemoryAction.STORE,
                timestamp=time.time(),
                metadata=metadata or {}
            )
            
            self.entries.append(entry)
            self.entry_counter += 1
            
            # Log action
            self.action_history.append({
                "agent_id": agent_id,
                "action": "store",
                "entry_id": entry.entry_id,
                "timestamp": entry.timestamp
            })
            
            return MemoryActionResult(
                success=True,
                entry_id=entry.entry_id,
                message=f"Stored entry {entry.entry_id}"
            )
    
    def retrieve(self, agent_id: int, query: str) -> MemoryActionResult:
        """
        Retrieve memory entries matching query.
        
        Args:
            agent_id: Agent requesting retrieval
            query: Search query
        
        Returns:
            MemoryActionResult with retrieved content
        """
        with self.lock:
            # Simple keyword matching
            matches = [
                entry for entry in self.entries
                if query.lower() in entry.content.lower()
            ]
            
            if not matches:
                return MemoryActionResult(
                    success=False,
                    message="No matching entries found"
                )
            
            # Return most recent match
            latest = max(matches, key=lambda e: e.timestamp)
            
            # Log action
            self.action_history.append({
                "agent_id": agent_id,
                "action": "retrieve",
                "entry_id": latest.entry_id,
                "timestamp": time.time()
            })
            
            return MemoryActionResult(
                success=True,
                entry_id=latest.entry_id,
                retrieved_content=latest.content,
                message=f"Retrieved entry {latest.entry_id}"
            )
    
    def query(self, agent_id: int, query: str) -> List[MemoryEntry]:
        """
        Query memory entries without logging as retrieval.
        
        Args:
            agent_id: Agent making query
            query: Search query
        
        Returns:
            List of matching entries
        """
        with self.lock:
            return [
                entry for entry in self.entries
                if query.lower() in entry.content.lower()
            ]
    
    def clear(self) -> None:
        """Clear all memory entries."""
        with self.lock:
            self.entries.clear()
            self.action_history.clear()
    
    def get_actions(self, agent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get action history, optionally filtered by agent.
        
        Args:
            agent_id: Filter by agent (None for all)
        
        Returns:
            List of action records
        """
        with self.lock:
            if agent_id is None:
                return self.action_history.copy()
            return [
                action for action in self.action_history
                if action.get("agent_id") == agent_id
            ]

# Global shared memory buffer instance
_shared_buffer: Optional[MemoryBuffer] = None
_buffer_lock = threading.Lock()

def get_shared_memory_buffer(capacity: int = 1000) -> MemoryBuffer:
    """
    Get or create the shared memory buffer instance.
    
    Args:
        capacity: Buffer capacity
    
    Returns:
        MemoryBuffer instance
    """
    global _shared_buffer
    with _buffer_lock:
        if _shared_buffer is None:
            _shared_buffer = MemoryBuffer(capacity=capacity)
        return _shared_buffer

def reset_shared_memory_buffer() -> None:
    """Reset the shared memory buffer to a new instance."""
    global _shared_buffer
    with _buffer_lock:
        _shared_buffer = MemoryBuffer(capacity=1000)

def parse_memory_action(text: str) -> Optional[MemoryActionRequest]:
    """
    Parse a <MEMORY_ACTION> token from text.
    
    Args:
        text: Text containing action token
    
    Returns:
        MemoryActionRequest or None
    """
    if "<MEMORY_ACTION>" not in text:
        return None
    
    # Extract action details
    parts = text.split("<MEMORY_ACTION>")
    if len(parts) < 2:
        return None
    
    action_text = parts[1].strip()
    
    # Parse action type and content
    if action_text.startswith("STORE:"):
        content = action_text[6:].strip()
        return MemoryActionRequest(
            agent_id=0,
            action=MemoryAction.STORE,
            content=content
        )
    elif action_text.startswith("RETRIEVE:"):
        query = action_text[9:].strip()
        return MemoryActionRequest(
            agent_id=0,
            action=MemoryAction.RETRIEVE,
            query=query
        )
    
    return None

def execute_memory_action(
    buffer: MemoryBuffer,
    request: MemoryActionRequest
) -> MemoryActionResult:
    """
    Execute a memory action request.
    
    Args:
        buffer: Memory buffer instance
        request: Action request
    
    Returns:
        Action result
    """
    if request.action == MemoryAction.STORE:
        return buffer.store(request.agent_id, request.content or "")
    elif request.action == MemoryAction.RETRIEVE:
        return buffer.retrieve(request.agent_id, request.query or "")
    else:
        return MemoryActionResult(
            success=False,
            message=f"Unsupported action: {request.action}"
        )

def handle_agent_output(
    agent_id: int,
    output: str,
    buffer: MemoryBuffer
) -> Optional[MemoryActionResult]:
    """
    Handle agent output and extract memory actions.
    
    Args:
        agent_id: Agent identifier
        output: Agent's output text
        buffer: Memory buffer instance
    
    Returns:
        MemoryActionResult if action found, None otherwise
    """
    request = parse_memory_action(output)
    if request is None:
        return None
    
    request.agent_id = agent_id
    return execute_memory_action(buffer, request)

if __name__ == "__main__":
    # Test buffer
    buffer = MemoryBuffer(capacity=10)
    
    # Store entries
    result = buffer.store(0, "Test memory entry 1")
    print(f"Store result: {result}")
    
    result = buffer.store(1, "Test memory entry 2")
    print(f"Store result: {result}")
    
    # Retrieve entries
    result = buffer.retrieve(0, "entry 1")
    print(f"Retrieve result: {result}")
    
    # Query entries
    entries = buffer.query(0, "test")
    print(f"Query results: {len(entries)} entries")
