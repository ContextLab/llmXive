"""
Synthetic Workflow Generator
----------------------------

This module provides a deterministic generator for synthetic multi‑agent
workflows used throughout the llmXive follow‑up project. It is invoked
directly by the pipeline orchestrator (`code/main.py`) and also imported
by the test suite (`generators.synthetic_workflow`).

The generator produces a list of workflow dictionaries, each containing:
  * ``id`` – a unique string identifier.
  * ``metadata`` – a mapping with at least ``depth`` and ``complexity``.
  * Additional fields may be added later without breaking the contract.

The deterministic design guarantees exactly 20 distinct delegation depths
(0‑19) with a minimum of 25 workflows per depth when the total count is
500 (the default used in the experiments). The random number generator
is seeded to ensure reproducibility across runs.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict
import random

class SyntheticWorkflowGenerator:
    """Generate deterministic synthetic workflows.

    Parameters
    ----------
    seed: int
        Seed for the deterministic random number generator.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = random.Random(seed)

    def generate_workflows(self, count: int) -> List[Dict]:
        """Generate ``count`` synthetic workflow specifications.

        The generator creates exactly 20 distinct ``depth`` values (0‑19)
        and distributes the workflows uniformly across those depths.
        Each workflow receives a random ``complexity`` value between 1
        and 5 (inclusive). The ``id`` field is a zero‑padded string.

        Parameters
        ----------
        count: int
            Number of workflows to generate. Must be a multiple of 20
            to guarantee the minimum‑per‑depth requirement; otherwise
            the remaining workflows are distributed starting from depth 0.

        Returns
        -------
        List[Dict]
            List of workflow dictionaries.
        """
        if count <= 0:
            raise ValueError("count must be a positive integer")

        workflows: List[Dict] = []
        depths = 20  # fixed number of distinct depths required by tests

        for i in range(count):
            depth = i % depths
            # Random complexity per workflow; deterministic because of the seeded RNG
            complexity = self._rng.randint(1, 5)

            workflow = {
                "id": f"wf_{i:04d}",
                "metadata": {
                    "depth": depth,
                    "complexity": complexity,
                },
            }
            workflows.append(workflow)

        return workflows

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="synthetic_workflow_generator",
        description="Generate deterministic synthetic workflows for the llmXive pipeline."
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of workflows to generate (e.g., 500)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation (default: 42)."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the generated workflows JSON file."
    )
    return parser.parse_args()

def main() -> int:
    args = _parse_args()
    generator = SyntheticWorkflowGenerator(seed=args.seed)
    workflows = generator.generate_workflows(count=args.count)

    # Ensure the output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write the list of workflows as a JSON array
    args.output.write_text(json.dumps(workflows, indent=2), encoding="utf-8")
    print(f"[synthetic_workflow] generated {len(workflows)} workflows → {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
