"""
Data Generator for ALE Execution Traces.

This module orchestrates the generation of the full dataset by importing
logic from ``generator_logic.py`` and writing the output to
``data/raw/golden_fixture.json``.

It implements the strict mapping rules for generating synthetic traces
representing "State Persistence Error" and "Reasoning Deficit" scenarios.
"""
import json
import os
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Standard library imports
from enum import Enum

# Import generation logic that creates concrete trace structures.
# ``generator_logic.py`` provides the heavy‑lifting for trace construction.
from code.data.generator_logic import (
    generate_trace,
    generate_task_description,
    StepState,
    ExecutionTrace,
    SCENARIOS,
)
# Import the FailureType enum defined in a dedicated module to avoid
# circular import issues.
from code.data.failure_type import FailureType

# Import seed‑pinning utilities.
from code.utils.seeds import set_seed, get_seed_state

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def generate_golden_fixture(
    seed_base: int = 42,
    num_tasks: int = 10,
    output_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Generate the golden fixture dataset containing exactly ten traces
    with deterministic ground‑truth labels.

    Parameters
    ----------
    seed_base : int, optional
        Base seed for the first task. Subsequent tasks use ``seed_base + i``.
    num_tasks : int, optional
        Number of tasks to generate. The specification requires ten
        scenarios; any other value is coerced to ten with a warning.
    output_path : str | None, optional
        If supplied, the JSON representation is written to this file.
        The directory hierarchy is created automatically.

    Returns
    -------
    List[Dict[str, Any]]
        In‑memory representation of all generated traces.
    """
    if num_tasks != 10:
        # Enforce the exact 10‑scenario requirement.
        print(
            f"Warning: num_tasks requested as {num_tasks}, but the golden fixture "
            f"requires exactly 10 scenarios. Adjusting to 10."
        )
        num_tasks = 10

    traces: List[Dict[str, Any]] = []

    # Prepare the output directory early so that any failure during generation
    # does not leave a half‑written file.
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(num_tasks):
        # Derive a deterministic seed for this scenario.
        current_seed = seed_base + i

        # Select the pre‑defined scenario.
        scenario = SCENARIOS[i]

        # Pin the seed for reproducibility.
        set_seed(current_seed)

        # Build the trace using the shared generation logic.
        # ``generate_trace`` expects a textual type and description.
        trace = generate_trace(
            scenario_type=str(scenario["type"]),
            scenario_description=scenario["description"],
            seed=current_seed,
        )

        # Assemble the record that will be persisted.
        trace_record = {
            "task_id": f"task_{i:02d}",
            "seed": current_seed,
            "scenario_id": scenario["id"],
            "ground_truth_label": str(scenario["type"]),
            "description": scenario["description"],
            "trace": trace,
        }

        traces.append(trace_record)

    # Persist if requested.
    if output_path:
        # Write the JSON file.
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(traces, f, indent=2, ensure_ascii=False)

        # Basic verification – raise if anything went wrong.
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError(
                "Verification failed: generated file is missing or empty."
            )

        # Compute SHA‑256 checksum.
        with open(output_path, "rb") as f:
            checksum = hashlib.sha256(f.read()).hexdigest()

        # Write checksum to the processed folder as required by the task.
        checksum_path = Path("data/processed/golden_fixture_checksum.txt")
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checksum_path, "w", encoding="utf-8") as cf:
            cf.write(checksum)

        print(
            f"Generated golden fixture with {len(traces)} traces at {output_path}"
        )
        print(f"Checksum (SHA256) written to {checksum_path}")

    return traces

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Command‑line interface for generating the golden fixture."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic ALE execution traces for the golden fixture."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base seed for generation (default: 42)",
    )
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=10,
        help="Number of tasks to generate (default: 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/golden_fixture.json",
        help="Output path for the JSON file",
    )

    args = parser.parse_args()

    try:
        generate_golden_fixture(
            seed_base=args.seed,
            num_tasks=args.num_tasks,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"Error generating golden fixture: {exc}")
        raise

if __name__ == "__main__":
    main()
