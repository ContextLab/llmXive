import json
import os
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# Import from existing utils
from utils.seeds import verify_pairing, set_seed
from utils.logging_config import get_logger

logger = get_logger(__name__)


class FailureType(Enum):
    """Enumeration of failure modes for ALE traces."""
    STATE_PERSISTENCE_ERROR = "state_persistence_error"
    REASONING_DEFICIT = "reasoning_deficit"
    TIMEOUT = "timeout"
    MEMORY_OOM = "memory_oom"


@dataclass
class ExecutionTrace:
    """
    Base data structure for an ALE execution trace.
    Represents a single run of an agent on a task, including state history and outcome.
    """
    trace_id: str
    task_description: str
    steps: List[Dict[str, Any]]  # List of step states and actions
    final_state: Dict[str, Any]
    success: bool
    failure_type: FailureType | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the trace to a dictionary for JSON serialization."""
        return {
            "trace_id": self.trace_id,
            "task_description": self.task_description,
            "steps": self.steps,
            "final_state": self.final_state,
            "success": self.success,
            "failure_type": self.failure_type.value if self.failure_type else None,
            "metadata": self.metadata
        }


@dataclass
class FailureLabel:
    """
    Base data structure for a failure label.
    Represents the ground truth classification of a failure in a trace.
    """
    trace_id: str
    label: FailureType
    confidence: float
    reasoning: str
    step_index: int | None = None  # Optional: index of the step where failure occurred

    def to_dict(self) -> Dict[str, Any]:
        """Convert the label to a dictionary for JSON serialization."""
        return {
            "trace_id": self.trace_id,
            "label": self.label.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "step_index": self.step_index
        }


def generate_task_description(seed: int, task_index: int) -> str:
    """Generate a deterministic task description string."""
    set_seed(seed)
    templates = [
        "Navigate to {location} and retrieve the {item}.",
        "Solve the puzzle by moving {item_a} to {location_a} and {item_b} to {location_b}.",
        "Identify the correct key for {door} and open it.",
        "Collect all {count} {item_type} items and bring them to {target_location}."
    ]
    template = templates[task_index % len(templates)]
    
    # Deterministic random generation based on seed
    locations = ["kitchen", "bedroom", "garage", "garden", "bathroom"]
    items = ["key", "ball", "book", "cup", "lamp"]
    
    return template.format(
        location=random.choice(locations),
        item=random.choice(items),
        item_a=random.choice(items),
        location_a=random.choice(locations),
        item_b=random.choice(items),
        location_b=random.choice(locations),
        door=random.choice(["door1", "door2", "secret_door"]),
        count=random.randint(1, 5),
        item_type=random.choice(items),
        target_location=random.choice(locations)
    )


def generate_step_state(seed: int, step_index: int, task_desc: str) -> Dict[str, Any]:
    """Generate a deterministic step state for a trace."""
    set_seed(seed + step_index)
    
    state = {
        "step_index": step_index,
        "agent_position": (random.randint(0, 10), random.randint(0, 10)),
        "inventory": [random.choice(["key", "ball", "book"]) for _ in range(random.randint(0, 3))],
        "observed_objects": [random.choice(["door", "box", "table", "chair"]) for _ in range(random.randint(1, 5))],
        "timestamp": 1000.0 + step_index * 0.5
    }
    
    # Add some deterministic variation based on task description hash
    desc_hash = hashlib.md5(task_desc.encode()).hexdigest()
    state["hash_suffix"] = desc_hash[:8]
    
    return state


def generate_trace(
    task_id: str,
    task_description: str,
    num_steps: int,
    failure_type: FailureType | None,
    seed: int
) -> ExecutionTrace:
    """
    Generate a complete execution trace with deterministic steps.
    """
    set_seed(seed)
    
    steps = []
    for i in range(num_steps):
        step_state = generate_step_state(seed, i, task_description)
        steps.append({
            "state": step_state,
            "action": f"action_{i}_{random.choice(['move', 'pick', 'drop', 'interact'])}"
        })
    
    final_state = steps[-1]["state"] if steps else {}
    success = failure_type is None
    
    return ExecutionTrace(
        trace_id=task_id,
        task_description=task_description,
        steps=steps,
        final_state=final_state,
        success=success,
        failure_type=failure_type,
        metadata={"seed": seed, "num_steps": num_steps}
    )


def main():
    """
    Entry point for the generator module.
    Demonstrates the base data structures and generates a sample trace.
    """
    logger.info("Initializing data generator module...")
    
    # Demonstrate base data structures
    sample_trace = ExecutionTrace(
        trace_id="demo_trace_001",
        task_description="Navigate to kitchen and retrieve the key.",
        steps=[{"state": {"x": 1, "y": 2}, "action": "move"}],
        final_state={"x": 1, "y": 2},
        success=True,
        failure_type=None
    )
    
    sample_label = FailureLabel(
        trace_id="demo_trace_001",
        label=FailureType.STATE_PERSISTENCE_ERROR,
        confidence=0.95,
        reasoning="Agent lost track of item location after step 3."
    )
    
    logger.info(f"Created sample trace: {sample_trace.trace_id}")
    logger.info(f"Created sample label: {sample_label.label.value}")
    
    # Generate a full trace with failure
    seed_val = 42
    task_desc = generate_task_description(seed_val, 0)
    trace = generate_trace(
        task_id=f"trace_{seed_val}",
        task_description=task_desc,
        num_steps=5,
        failure_type=FailureType.REASONING_DEFICIT,
        seed=seed_val
    )
    
    # Verify pairing (dummy check for demonstration, assumes pairing logic exists)
    pairing_check = verify_pairing(trace.trace_id, seed_val)
    logger.info(f"Pairing verification for {trace.trace_id}: {pairing_check}")
    
    # Output structure for documentation
    print(json.dumps(asdict(trace), indent=2, default=str))
    print(json.dumps(asdict(sample_label), indent=2, default=str))


if __name__ == "__main__":
    main()