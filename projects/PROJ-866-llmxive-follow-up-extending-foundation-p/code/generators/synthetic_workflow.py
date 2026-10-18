"""
synthetic_workflow.py
---------------------

Minimal deterministic workflow generator used by the pipeline orchestrator
(`code/main.py`). Generates a JSON array of workflow objects conforming to
the contract `contracts/workflow.schema.yaml`. The generator is deliberately
simple: each workflow contains an identifier, a delegation depth, a policy
complexity, and a validity flag. All values are deterministic given the
supplied seed and count.

Command‑line interface (mirrors the expectations of `code/main.py`):
    python synthetic_workflow.py --count N --seed S --output PATH

The script writes the output to *PATH* as a UTF‑8 encoded JSON file.
"""
import argparse
import json
import random
from pathlib import Path
from typing import List, Dict

def _make_workflow(idx: int, rng: random.Random) -> Dict:
    """Create a single workflow dictionary."""
    # Deterministic but varied fields.
    workflow_id = f"wf_{idx:05d}"
    delegation_depth = rng.randint(1, 5)          # Example depth range.
    policy_complexity = rng.randint(1, 3)        # Example complexity range.
    # Simple validity rule: depth > 1 is considered valid.
    is_valid = delegation_depth > 1
    return {
        "id": workflow_id,
        "delegation_depth": delegation_depth,
        "policy_complexity": policy_complexity,
        "is_valid": is_valid,
    }

def generate_workflows(count: int, seed: int) -> List[Dict]:
    """Generate *count* workflows deterministically."""
    rng = random.Random(seed)
    return [_make_workflow(i, rng) for i in range(count)]

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
