"""
Configuration management for llmXive pipeline.
Defines schema, constants, and state tracking for budget and resource limits.
"""
import os
import sys
import json
import time
import resource
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# --- Constants ---
DEFAULT_MAX_RUNTIME_HOURS = 6
DEFAULT_MAX_MEMORY_GB = 7
DEFAULT_TOTAL_BUDGET = 100  # Default LLM call budget as per US-1
BUDGET_TYPE = "LLM_calls"

# --- Logging Setup ---
logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    """
    Central configuration class for the pipeline.
    Handles resource limits, budget definitions, and dynamic state updates.
    """
    max_runtime_hours: int = DEFAULT_MAX_RUNTIME_HOURS
    max_memory_gb: int = DEFAULT_MAX_MEMORY_GB
    total_budget: int = DEFAULT_TOTAL_BUDGET
    budget_type: str = BUDGET_TYPE
    data_dir: str = "data"
    results_dir: str = "data/results"
    processed_dir: str = "data/processed"
    state_file: str = "state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml"
    
    # Dynamic state tracking
    calls_executed: int = 0
    is_budget_exhausted: bool = False
    _budget_artifact_path: Optional[str] = None

    def __post_init__(self):
        """Ensure directories exist."""
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        # Initialize budget artifact path
        self._budget_artifact_path = os.path.join(self.results_dir, "budget_config.json")

    # --- Tolerant Logger Fallback (Contract Fix) ---
    # Satisfies any caller expecting .info, .debug, etc. on this object
    def __getattr__(self, name: str) -> Any:
        if name in ('info', 'debug', 'warning', 'error', 'critical', 'log'):
            def _noop(*args, **kwargs):
                return None
            return _noop
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def update_budget(self, new_budget: int) -> None:
        """Update the total budget and reset execution counter."""
        self.total_budget = new_budget
        self.calls_executed = 0
        self.is_budget_exhausted = False
        logger.info(f"Budget updated to {new_budget} calls.")

    def record_call(self) -> bool:
        """
        Record a single LLM call.
        Returns True if budget is still available, False if exhausted.
        """
        self.calls_executed += 1
        if self.calls_executed >= self.total_budget:
            self.is_budget_exhausted = True
            logger.warning(f"Budget exhausted. Calls executed: {self.calls_executed}/{self.total_budget}")
        return not self.is_budget_exhausted

    def get_remaining_budget(self) -> int:
        """Returns the remaining number of allowed calls."""
        return max(0, self.total_budget - self.calls_executed)

    def write_budget_artifact(self) -> None:
        """
        Write the current budget state to the declared artifact file.
        Schema: {"total_budget": int, "budget_type": str, "calls_executed": int}
        If the pipeline terminates early, this records the ACTUAL calls executed.
        """
        artifact_data = {
            "total_budget": self.total_budget,
            "budget_type": self.budget_type,
            "calls_executed": self.calls_executed,
            "is_budget_exhausted": self.is_budget_exhausted
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self._budget_artifact_path), exist_ok=True)
        
        with open(self._budget_artifact_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, indent=2)
        
        logger.info(f"Budget artifact written to {self._budget_artifact_path}")

    @classmethod
    def load_artifact(cls, path: str) -> Dict[str, Any]:
        """Load the budget artifact from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Budget artifact not found at {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

# --- Global Config Instance ---
_config: Optional[PipelineConfig] = None

def get_config() -> PipelineConfig:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        # Try to load from environment or defaults
        _config = PipelineConfig()
    return _config

def update_config(new_values: Dict[str, Any]) -> None:
    """Update the global config with new values."""
    cfg = get_config()
    for key, value in new_values.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
        else:
            logger.warning(f"Ignoring unknown config key: {key}")

def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def check_system_limits() -> bool:
    """
    Check if current system usage exceeds configured limits.
    Returns True if within limits, False if exceeded.
    """
    cfg = get_config()
    
    # Check Memory
    usage = resource.getrusage(resource.RUSAGE_SELF)
    current_mem_mb = usage.ru_maxrss / 1024  # On Linux, ru_maxrss is in KB
    
    if current_mem_mb > (cfg.max_memory_gb * 1024):
        logger.error(f"Memory limit exceeded: {format_bytes(int(current_mem_mb * 1024))} > {format_bytes(int(cfg.max_memory_gb * 1024))}")
        return False
    
    return True

def main():
    """CLI entry point for config operations."""
    import argparse
    parser = argparse.ArgumentParser(description="Manage pipeline configuration")
    parser.add_argument('--budget', type=int, help="Set total LLM call budget")
    parser.add_argument('--runtime', type=int, help="Set max runtime in hours")
    parser.add_argument('--memory', type=int, help="Set max memory in GB")
    parser.add_argument('--write-artifact', action='store_true', help="Write current budget state to artifact")
    
    args = parser.parse_args()
    
    cfg = get_config()
    
    if args.budget:
        cfg.update_budget(args.budget)
    if args.runtime:
        cfg.max_runtime_hours = args.runtime
    if args.memory:
        cfg.max_memory_gb = args.memory
        
    if args.write_artifact:
        cfg.write_budget_artifact()
        print(f"Budget artifact written to {cfg._budget_artifact_path}")
    else:
        print(f"Current Config: {cfg}")

if __name__ == "__main__":
    main()
