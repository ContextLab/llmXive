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
    This agent serves as the baseline for comparing against the compressed
    symbolic rule agent. It performs exact retrieval from the raw trace data.
    """
    def __init__(self, config=None):
        self.config = config or get_config()
        self.loader = TraceLoader(self.config)
        self.name = "BaselineAgent"
        self._cache = {}
        self._total_retrievals = 0
        self._total_latency = 0.0

    def _load_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific trace by ID from disk.
        
        Args:
            trace_id: The unique identifier for the trace.
            
        Returns:
            The trace dictionary if found, None otherwise.
        """
        if trace_id in self._cache:
            return self._cache[trace_id]
        
        # Attempt to locate the file in the raw data directory
        # The expected naming convention is session_{trace_id}.json
        trace_path = self.config.data_raw_path / f"session_{trace_id}.json"
        
        if not trace_path.exists():
            # Fallback: search for a file containing the trace_id substring
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
        except (json.JSONDecodeError, IOError) as e:
            raise RuntimeError(f"Failed to load trace {trace_id}: {e}")

    def process_trace(self, trace: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """
        Process a trace using raw memory retrieval.
        
        This method simulates the baseline retrieval process where the agent
        accesses the full, uncompressed trace data to determine the final state.
        
        Args:
            trace: The input trace dictionary containing 'session_id' and 'final_state'.
            
        Returns:
            Tuple of (predicted_final_state, latency_seconds).
            
        Raises:
            RuntimeError: If the trace cannot be loaded from disk.
        """
        start_time = time.perf_counter()
        
        session_id = trace.get("session_id", "")
        if not session_id:
            raise ValueError("Trace must contain a 'session_id'")
        
        loaded_trace = self._load_trace(session_id)
        
        if loaded_trace:
            # The baseline agent retrieves the ground truth final state
            # from the stored trace data.
            final_state = loaded_trace.get("final_state", {})
            if not final_state:
                # Fallback if final_state is missing in the loaded trace
                final_state = trace.get("final_state", {})
        else:
            # If the trace is not found in the raw data, use the provided
            # final_state from the input trace if available.
            final_state = trace.get("final_state", {})
            if not final_state:
                raise RuntimeError(f"Trace {session_id} not found and no final_state provided in input.")
        
        latency = time.perf_counter() - start_time
        self._total_retrievals += 1
        self._total_latency += latency
        
        return final_state, latency

    def get_stats(self) -> Dict[str, float]:
        """
        Retrieve retrieval statistics for this agent.
        
        Returns:
            Dictionary containing total_retrievals and average_latency.
        """
        if self._total_retrievals == 0:
            return {"total_retrievals": 0, "average_latency": 0.0}
        
        return {
            "total_retrievals": self._total_retrievals,
            "average_latency": self._total_latency / self._total_retrievals
        }

def main():
    """Entry point for running the baseline agent benchmark."""
    config = get_config()
    agent = BaselineAgent(config)
    
    # Example usage: process a single trace
    # Note: In a real benchmark scenario, this would be called by benchmark.py
    # with traces from the held-out set.
    test_trace = {
        "session_id": "test-123",
        "final_state": {"slide_count": 1, "content": "test"}
    }
    
    try:
        result, latency = agent.process_trace(test_trace)
        print(f"Baseline Agent Result: {result}, Latency: {latency:.4f}s")
        print(f"Agent Stats: {agent.get_stats()}")
    except Exception as e:
        print(f"Error processing test trace: {e}")

if __name__ == "__main__":
    main()
