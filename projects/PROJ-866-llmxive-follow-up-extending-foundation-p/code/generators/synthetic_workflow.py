"""
synthetic_workflow.py
---------------------

Deterministic workflow generator used by the pipeline orchestrator
(`code/main.py`). Generates a JSON array of workflow objects conforming to
the contract `contracts/workflow.schema.yaml`. The generator produces a
uniform distribution of delegation depths to satisfy the variance test
(20 unique depths, ≥ 25 workflows per depth).

Command‑line interface (mirrors the expectations of `code/main.py`):
    python synthetic_workflow.py --count N --seed S --output PATH

The script writes the output to *PATH* as a UTF‑8 encoded JSON file.
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict
import random

class SyntheticWorkflowGenerator:
    """
    Generator class exposing the same interface used by the unit tests.

    Parameters
    ----------
    seed : int
        Random seed for deterministic generation.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def _make_workflow(self, idx: int, depth: int) -> Dict:
        """
        Create a single workflow dictionary.

        The `policy_complexity` is varied deterministically but
        independently of depth to keep the distribution simple.
        """
        workflow_id = f"wf_{idx:05d}"
        policy_complexity = self.rng.randint(1, 3)
        # Simple validity rule: depth > 1 is considered valid.
        is_valid = depth > 1
        return {
            "id": workflow_id,
            "delegation_depth": depth,
            "policy_complexity": policy_complexity,
            "is_valid": is_valid,
        }

    def generate_workflows(self, count: int) -> List[Dict]:
        """
        Generate *count* workflows with a uniform delegation depth
        distribution across the range 1‑20. The function cycles through
        depths so that each depth appears approximately the same number
        of times (exactly when count is a multiple of 20).

        Returns
        -------
        List[Dict]
            List of workflow dictionaries.
        """
        workflows: List[Dict] = []
        # Determine depth sequence: repeat 1..20 as needed.
        depths_cycle = [d for d in range(1, 21)]
        for i in range(count):
            depth = depths_cycle[i % len(depths_cycle)]
            wf = self._make_workflow(i, depth)
            workflows.append(wf)
        return workflows

def generate_workflows(count: int, seed: int) -> List[Dict]:
    """
    Backwards‑compatible functional API used by the CLI entry point.
    """
    generator = SyntheticWorkflowGenerator(seed)
    return generator.generate_workflows(count)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic synthetic workflow generator"
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of workflows to generate",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the generated JSON file",
    )
    args = parser.parse_args()

    workflows = generate_workflows(args.count, args.seed)

    # Ensure the output directory exists.
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON array.
    args.output.write_text(
        json.dumps(workflows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Generated {len(workflows)} workflows → {args.output}")

if __name__ == "__main__":
    main()
