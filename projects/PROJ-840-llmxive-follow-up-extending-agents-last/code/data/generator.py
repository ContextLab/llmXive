import json
import os
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum

# Import from sibling module as per API surface
from utils.seeds import verify_pairing, set_seed, get_seed_state, save_seed_state

class FailureType(Enum):
    STATE_PERSISTENCE_ERROR = "State Persistence Error"
    REASONING_DEFICIT = "Reasoning Deficit"

class FileState:
    def __init__(self, path: str, content: str, deleted: bool = False):
        self.path = path
        self.content = content
        self.deleted = deleted

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "content": self.content,
            "deleted": self.deleted
        }

class VariableState:
    def __init__(self, name: str, value: str, type_: str):
        self.name = name
        self.value = value
        self.type = type_

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.type
        }

class StepState:
    def __init__(self, files: List[FileState], variables: List[VariableState]):
        self.files = files
        self.variables = variables

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files": [f.to_dict() for f in self.files],
            "variables": [v.to_dict() for v in self.variables]
        }

class ExecutionTrace:
    def __init__(self, trace_id: str, ground_truth_label: str, step_state: StepState, task_description: str):
        self.trace_id = trace_id
        self.ground_truth_label = ground_truth_label
        self.step_state = step_state
        self.task_description = task_description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "ground_truth_label": self.ground_truth_label,
            "step_state": self.step_state.to_dict(),
            "task_description": self.task_description
        }

def generate_task_description(seed: int, failure_type: FailureType) -> str:
    set_seed(seed)
    templates = [
        "Create a python script that calculates the Fibonacci sequence up to {n} and saves it to {file}.",
        "Read the data from {file} and compute the average of the 'value' column, storing the result in {var}.",
        "Implement a function to sort a list of dictionaries by {key} and write the sorted list to {file}.",
        "Parse the JSON file {file} and extract all keys starting with {prefix}, saving them to {var}."
    ]
    template = random.choice(templates)
    
    # Generate deterministic parameters based on seed
    n = random.randint(5, 20)
    file_name = f"output_{seed}.txt"
    var_name = f"result_{seed}"
    key_name = f"score_{seed}"
    prefix = f"data_{seed}"

    return template.format(n=n, file=file_name, var=var_name, key=key_name, prefix=prefix)

def generate_step_state(seed: int, failure_type: FailureType) -> StepState:
    set_seed(seed)
    
    files = []
    variables = []

    if failure_type == FailureType.STATE_PERSISTENCE_ERROR:
        # Scenario: File was deleted or variable lost between steps
        file_path = f"output_{seed}.txt"
        # Simulate a state where the file exists but is marked deleted in the next step
        files.append(FileState(file_path, "some content", deleted=True))
        variables.append(VariableState(f"result_{seed}", "None", "NoneType"))
    elif failure_type == FailureType.REASONING_DEFICIT:
        # Scenario: File exists but content is logically wrong or variable type mismatch
        file_path = f"output_{seed}.txt"
        files.append(FileState(file_path, "garbage_data", deleted=False))
        variables.append(VariableState(f"result_{seed}", "error", "str"))
    
    return StepState(files, variables)

def generate_trace(seed: int, failure_type: FailureType) -> ExecutionTrace:
    set_seed(seed)
    trace_id = hashlib.md5(f"trace_{seed}".encode()).hexdigest()[:16]
    
    task_description = generate_task_description(seed, failure_type)
    step_state = generate_step_state(seed, failure_type)
    
    # Verify pairing as per FR-008 precondition
    # verify_pairing expects trace_id and seed_val (task_instance)
    # We construct a minimal task instance dict to satisfy the type check in seeds.py
    task_instance = {
        "trace_id": trace_id,
        "seed": seed,
        "failure_type": failure_type.value
    }
    
    try:
        verify_pairing(trace_id, task_instance)
    except Exception as e:
        # If pairing verification fails, we must raise to fail loudly
        raise RuntimeError(f"Pairing verification failed for trace {trace_id}: {e}")

    return ExecutionTrace(
        trace_id=trace_id,
        ground_truth_label=failure_type.value,
        step_state=step_state,
        task_description=task_description
    )

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic ALE execution traces")
    parser.add_argument("--seed", type=int, required=True, help="Base seed for generation")
    parser.add_argument("--num-tasks", type=int, default=10, help="Number of traces to generate")
    parser.add_argument("--output", type=str, default="data/raw/golden_subset.json", help="Output file path")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    traces = []
    
    # Generate balanced dataset: half State Persistence, half Reasoning Deficit
    num_persistence = args.num_tasks // 2
    num_reasoning = args.num_tasks - num_persistence
    
    # Generate State Persistence Errors
    for i in range(num_persistence):
        trace_seed = args.seed + i
        trace = generate_trace(trace_seed, FailureType.STATE_PERSISTENCE_ERROR)
        traces.append(trace.to_dict())
        
    # Generate Reasoning Deficits
    for i in range(num_reasoning):
        trace_seed = args.seed + num_persistence + i
        trace = generate_trace(trace_seed, FailureType.REASONING_DEFICIT)
        traces.append(trace.to_dict())
    
    # Write to JSON file
    with open(output_path, 'w') as f:
        json.dump(traces, f, indent=2)
        
    print(f"Generated {len(traces)} traces to {output_path}")

if __name__ == "__main__":
    main()
