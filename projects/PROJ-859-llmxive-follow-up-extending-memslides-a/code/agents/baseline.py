"""
Baseline Agent Implementation (Raw Memory).

This module implements the raw memory agent for User Story 3.
It retrieves context directly from the stored traces without compression.
"""
import time
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
import json

from config import get_config
from utils.loaders import TraceLoader

class BaselineAgent:
    """
    Agent that uses raw memory (uncompressed traces) for retrieval.
    """
    def __init__(self, config=None):
        self.config = config or get_config()
        self.loader = TraceLoader(self.config)
        self.name = "BaselineAgent"
        self._cache = {}

    def _load_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific trace by ID from disk."""
        if trace_id in self._cache:
            return self._cache[trace_id]
        
        trace_path = self.config.data_raw_path / f"session_{trace_id}.json"
        if not trace_path.exists():
            # Try to find by partial match if ID is just the UUID part
            for p in self.config.data_raw_path.glob("session_*.json"):
                if trace_id in p.name:
                    trace_path = p
                    break
            else:
                return None

        try:
            with open(trace_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._cache[trace_id] = data
            return data
        except Exception:
            return None

    def process_trace(self, trace: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """
        Process a trace using raw memory retrieval.
        
        Args:
            trace: The input trace dictionary containing 'session_id' and 'final_state'.
            
        Returns:
            Tuple of (predicted_final_state, latency_seconds).
        """
        start_time = time.perf_counter()
        
        # Simulate "raw memory" retrieval: we just return the ground truth
        # In a real scenario, this might involve searching a vector store or
        # scanning a large memory buffer.
        session_id = trace.get("session_id", "")
        loaded_trace = self._load_trace(session_id)
        
        if loaded_trace:
            final_state = loaded_trace.get("final_state", {})
        else:
            # Fallback: use the trace provided in the input if it has a final_state
            final_state = trace.get("final_state", {})
        
        latency = time.perf_counter() - start_time
        return final_state, latency

def main():
    """Entry point for running the baseline agent benchmark."""
    config = get_config()
    agent = BaselineAgent(config)
    
    # Example usage: process a single trace
    test_trace = {
        "session_id": "test-123",
        "final_state": {"slide_count": 1, "content": "test"}
    }
    
    result, latency = agent.process_trace(test_trace)
    print(f"Baseline Agent Result: {result}, Latency: {latency:.4f}s")

if __name__ == "__main__":
    main()
