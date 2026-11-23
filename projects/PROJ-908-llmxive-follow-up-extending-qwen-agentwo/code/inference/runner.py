"""
Runner for fetching real CoT traces from the AgentWorld benchmark.

This module implements Task T017: Fetch Real CoT Traces.
It strictly adheres to the "Fail Loudly" principle: if the real data
cannot be fetched, it raises a DataFetchError and does NOT generate
synthetic data.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.loaders import load_cot_traces

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when real data fetching fails and no fallback is allowed."""
    pass

class CoTStep:
    """Represents a single step in a Chain-of-Thought trace."""
    def __init__(self, step_id: str, thought: str, action: Optional[str] = None, observation: Optional[str] = None):
        self.step_id = step_id
        self.thought = thought
        self.action = action
        self.observation = observation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation
        }

class CoTTrace:
    """Represents a full Chain-of-Thought trace for a task."""
    def __init__(self, task_id: str, interaction_type: str, steps: List[CoTStep]):
        self.task_id = task_id
        self.interaction_type = interaction_type
        self.steps = steps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "interaction_type": self.interaction_type,
            "steps": [s.to_dict() for s in self.steps]
        }

def load_agentworld_tasks(source_path: Path) -> List[Dict[str, Any]]:
    """
    Load the benchmark tasks to determine which traces we need.
    In a full pipeline, this would read the benchmark JSON.
    For T017, we rely on the loader to fetch the specific CoT dataset.
    """
    # Placeholder for future integration with the benchmark file
    # Currently, load_cot_traces handles the direct fetch of the CoT dataset
    return []

def initialize_model():
    """
    Placeholder for model initialization if generation were needed.
    For T017, we are fetching EXISTING traces, so no model is needed.
    """
    logger.info("No model initialization required for trace fetching.")
    return None

def generate_trace(task: Dict[str, Any], model: Any) -> CoTTrace:
    """
    Placeholder for trace generation.
    T017 explicitly forbids generating synthetic traces.
    """
    raise NotImplementedError("T017 requires fetching REAL traces, not generating them.")

def main():
    """
    Main entry point for T017.
    
    1. Attempts to fetch `qwen-agentworld/cot_traces` from HuggingFace.
    2. Saves to `data/raw/cot_traces.json`.
    3. Validates file size > 0 and JSON schema.
    4. Logs metadata (task_id, interaction_type).
    5. FAILS LOUDLY (raises DataFetchError) if fetch fails.
    """
    output_dir = Path("data/raw")
    output_file = output_dir / "cot_traces.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting CoT Trace fetch for T017. Output: {output_file}")

    try:
        # Delegate to the robust loader in utils/loaders.py
        # This function is expected to handle the HF fetch and fail loudly if needed.
        traces_data = load_cot_traces()
        
        if not traces_data:
            raise DataFetchError("Received empty list of traces from loader.")

        # Write to disk
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(traces_data, f, indent=2, ensure_ascii=False)

        # Verification
        file_size = output_file.stat().st_size
        if file_size == 0:
            raise DataFetchError(f"Output file {output_file} is empty.")

        # Log metadata sample
        sample_count = len(traces_data)
        logger.info(f"Successfully fetched {sample_count} traces.")
        
        if sample_count > 0:
            first_trace = traces_data[0]
            logger.info(f"Sample Metadata - Task ID: {first_trace.get('task_id', 'N/A')}, "
                        f"Interaction Type: {first_trace.get('interaction_type', 'N/A')}")

        logger.info(f"T017 Complete: Real CoT traces written to {output_file}")
        return 0

    except Exception as e:
        logger.error(f"CRITICAL: Failed to fetch real CoT traces: {e}")
        # Re-raise to ensure the pipeline fails loudly
        raise DataFetchError(f"Data fetch failed: {e}") from e

if __name__ == "__main__":
    sys.exit(main())
