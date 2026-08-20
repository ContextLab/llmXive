"""
Data Generator for ALE Execution Traces.

This module orchestrates the generation of the full dataset by importing
logic from generator_logic.py and writing the output to data/raw/golden_fixture.json.

It implements the strict mapping rules for generating synthetic traces
representing "State Persistence Error" and "Reasoning Deficit" scenarios.
"""
import json
import os
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import random

# Import from sibling module
from code.data.generator_logic import (
    generate_trace,
    generate_task_description,
    StepState,
    ExecutionTrace,
    FailureType
)
from code.utils.seeds import set_seed, get_seed_state

# Constants for the 10 scenarios (5 State Persistence, 5 Reasoning Deficit)
# These map scenario indices to their specific types and descriptions
SCENARIOS = [
    {"id": 0, "type": "State Persistence Error", "description": "SP_01: Edit file A.txt after it was deleted in step 2."},
    {"id": 1, "type": "State Persistence Error", "description": "SP_02: Read variable x after it was reset to None in step 1."},
    {"id": 2, "type": "State Persistence Error", "description": "SP_03: Move file B.txt to a directory that was deleted in step 3."},
    {"id": 3, "type": "State Persistence Error", "description": "SP_04: Write to file C.txt after the file handle was closed in step 1."},
    {"id": 4, "type": "State Persistence Error", "description": "SP_05: Execute command on process P1 after it was terminated in step 2."},
    {"id": 5, "type": "Reasoning Deficit", "description": "RD_01: Open A.txt (exists) but read the wrong line (logical planning error)."},
    {"id": 6, "type": "Reasoning Deficit", "description": "RD_02: Calculate sum([1, 2]) but return 4 (arithmetic logic error)."},
    {"id": 7, "type": "Reasoning Deficit", "description": "RD_03: Sort list [3, 1, 2] but return [1, 3, 2] (sorting logic error)."},
    {"id": 8, "type": "Reasoning Deficit", "description": "RD_04: Filter list [1, 2, 3] for >1 but return [2] (missing element logic error)."},
    {"id": 9, "type": "Reasoning Deficit", "description": "RD_05: Concatenate strings \"a\" and \"b\" but return \"ba\" (order logic error)."},
]

def generate_golden_fixture(seed_base: int = 42, num_tasks: int = 10, output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate the golden fixture dataset containing 10 traces with ground truth labels.

    Args:
        seed_base: The base seed for the first task. Subsequent tasks use seed_base + i.
        num_tasks: Number of tasks to generate (default 10).
        output_path: Optional path to write the JSON file. If None, returns data only.

    Returns:
        List of dictionaries representing the execution traces with ground truth labels.
    """
    if num_tasks != 10:
        # Enforce the specific requirement for T015c to generate exactly 10 tasks
        # as defined by the 10 scenarios in SCENARIOS
        print(f"Warning: num_tasks requested as {num_tasks}, but standard fixture requires 10. Adjusting to 10.")
        num_tasks = 10

    traces = []

    # Ensure output directory exists
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(num_tasks):
        # Calculate seed for this specific task instance
        current_seed = seed_base + i

        # Select the scenario for this task index
        scenario = SCENARIOS[i]

        # Set seed for reproducibility
        set_seed(current_seed)

        # Generate the trace using the logic module
        # We pass the scenario type and description to guide generation
        trace = generate_trace(
            scenario_type=scenario["type"],
            scenario_description=scenario["description"],
            seed=current_seed
        )

        # Add ground truth label based on the scenario
        trace_with_label = {
            "task_id": f"task_{i:02d}",
            "seed": current_seed,
            "scenario_id": scenario["id"],
            "ground_truth_label": scenario["type"],
            "description": scenario["description"],
            "trace": trace
        }

        traces.append(trace_with_label)

    # Write to file if path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(traces, f, indent=2, ensure_ascii=False)
        print(f"Generated golden fixture with {len(traces)} traces at {output_path}")

        # Verify file exists and is non-empty
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print("Verification: File exists and is non-empty.")
            # Calculate checksum for verification
            with open(output_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            print(f"Checksum (SHA256): {checksum}")
        else:
            raise RuntimeError("Verification failed: File is missing or empty.")

    return traces

def main():
    """CLI entry point for generating the golden fixture."""
    parser = argparse.ArgumentParser(description="Generate synthetic ALE execution traces for the golden fixture.")
    parser.add_argument("--seed", type=int, default=42, help="Base seed for generation (default: 42)")
    parser.add_argument("--num-tasks", type=int, default=10, help="Number of tasks to generate (default: 10)")
    parser.add_argument("--output", type=str, default="data/raw/golden_fixture.json", help="Output path for the JSON file")

    args = parser.parse_args()

    try:
        generate_golden_fixture(
            seed_base=args.seed,
            num_tasks=args.num_tasks,
            output_path=args.output
        )
    except Exception as e:
        print(f"Error generating golden fixture: {e}")
        raise

if __name__ == "__main__":
    main()