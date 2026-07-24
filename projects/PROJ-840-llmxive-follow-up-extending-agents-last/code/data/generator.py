import json
import os
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import argparse
import sys

# Import from existing project utilities
try:
    from utils.seeds import verify_pairing, set_seed
except ImportError:
    # Fallback for direct execution if path not set up correctly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.seeds import verify_pairing, set_seed


@dataclass
class FileState:
    path: str
    content: str
    deleted: bool

@dataclass
class VariableState:
    name: str
    value: str
    type: str

@dataclass
class StepState:
    files: List[Dict[str, Any]]
    variables: List[Dict[str, Any]]

@dataclass
class ExecutionTrace:
    trace_id: str
    ground_truth_label: str  # "State Persistence Error" | "Reasoning Deficit"
    step_state: Dict[str, Any]
    task_description: str

class FailureType:
    STATE_PERSISTENCE = "State Persistence Error"
    REASONING_DEFICIT = "Reasoning Deficit"

def generate_task_description(seed: int, mode: str) -> str:
    """Generate a deterministic task description based on seed and mode."""
    set_seed(seed)
    templates = {
        "state_error": [
            "Create a file named 'config.txt' with content 'key=value'. Then, attempt to delete a file named 'nonexistent.txt' which does not exist in the directory.",
            "Initialize a variable 'counter' to 0. Then, increment 'counter' by 1. Finally, try to access a variable 'undefined_var' that was never defined.",
            "Write a log entry to 'app.log'. Then, delete 'app.log'. Finally, attempt to read from 'app.log' expecting valid data."
        ],
        "reasoning_deficit": [
            "The goal is to calculate the sum of numbers in a list. The agent opens 'data.json', reads the content, but instead of parsing the JSON, it attempts to perform arithmetic on the raw string object directly without conversion.",
            "The goal is to sort a list of names. The agent loads 'names.txt', but then attempts to sort the file handle object itself instead of the list of strings read from it.",
            "The goal is to count occurrences of a word. The agent reads 'text.txt', but instead of counting, it attempts to overwrite the file with the count value without reading the content first."
        ]
    }

    key = "state_error" if mode == "state_error" else "reasoning_deficit"
    # Deterministic selection based on seed state
    idx = seed % len(templates[key])
    return templates[key][idx]

def generate_step_state(seed: int, label: str) -> Dict[str, Any]:
    """Generate a step state that aligns with the ground truth label."""
    set_seed(seed)
    
    files = []
    variables = []

    if label == FailureType.STATE_PERSISTENCE:
        # Simulate state inconsistency: e.g., trying to delete a file that doesn't exist
        # or accessing a variable that wasn't created.
        # Example: File list shows 'config.txt' exists, but action tries to delete 'missing.txt'
        files.append({
            "path": "config.txt",
            "content": "key=value",
            "deleted": False
        })
        # The error comes from the mismatch between state and action logic
        # We record the state *before* the failing action
        variables.append({
            "name": "counter",
            "value": "0",
            "type": "int"
        })
    elif label == FailureType.REASONING_DEFICIT:
        # Simulate logical invalidity: e.g., operating on wrong types
        files.append({
            "path": "data.json",
            "content": "[1, 2, 3]",
            "deleted": False
        })
        variables.append({
            "name": "data_handle",
            "value": "<open file 'data.json'>",
            "type": "file_object"
        })
    
    return {
        "files": files,
        "variables": variables
    }

def generate_trace(seed: int, label: str, task_desc: str, step_state: Dict[str, Any]) -> ExecutionTrace:
    """Create a single execution trace object."""
    # Generate a deterministic trace ID
    trace_id_hash = hashlib.sha256(f"{seed}-{label}".encode()).hexdigest()[:12]
    trace_id = f"trace_{trace_id_hash}"
    
    return ExecutionTrace(
        trace_id=trace_id,
        ground_truth_label=label,
        step_state=step_state,
        task_description=task_desc
    )

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic ALE execution traces for research.")
    parser.add_argument("--mode", type=str, required=True, choices=["golden", "state_error", "reasoning_deficit"],
                        help="Mode: 'golden' generates a mix, others generate specific types.")
    parser.add_argument("--seed", type=int, required=True, help="Random seed for reproducibility.")
    parser.add_argument("--num-tasks", type=int, default=10, help="Number of traces to generate.")
    parser.add_argument("--output", type=str, default="data/raw/golden_subset.json",
                        help="Output file path.")
    
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    traces = []
    
    # Verify pairing capability (FR-008 precondition)
    # We generate a pairing verification hash for the dataset itself
    dataset_seed_state = verify_pairing(args.seed, "dataset_generation")
    
    for i in range(args.num_tasks):
        # Alternate or mix labels based on mode
        if args.mode == "golden":
            label = FailureType.STATE_PERSISTENCE if i % 2 == 0 else FailureType.REASONING_DEFICIT
        else:
            label = FailureType.STATE_PERSISTENCE if args.mode == "state_error" else FailureType.REASONING_DEFICIT
        
        # Use a unique seed for each trace derived from the main seed
        trace_seed = args.seed + i
        
        task_desc = generate_task_description(trace_seed, label)
        step_state = generate_step_state(trace_seed, label)
        trace = generate_trace(trace_seed, label, task_desc, step_state)
        
        traces.append(asdict(trace))

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(traces, f, indent=2)

    print(f"Successfully generated {len(traces)} traces to {output_path}")
    print(f"Dataset pairing seed state: {dataset_seed_state}")

if __name__ == "__main__":
    main()
