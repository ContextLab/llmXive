"""
Synthetic workflow generator
----------------------------
Generates a deterministic set of synthetic workflows conforming to
``contracts/workflow.schema.yaml``.  The generator is deliberately
lightweight – it creates a simple linear chain of agents whose depth
and policy‑complexity are drawn from a deterministic pseudo‑random
sequence seeded by the ``--seed`` argument.
"""
import argparse
import json
import random
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths

def _create_workflow(idx: int, rng: random.Random) -> Dict:
    """Create a single workflow dictionary."""
    # Deterministic depth and complexity in a modest range
    depth = rng.randint(1, 5)          # delegation depth
    complexity = rng.randint(1, 5)    # number of policy constraints per node

    # Build a linear chain of ``depth + 1`` nodes
    nodes = []
    edges = []
    for d in range(depth + 1):
        node_id = f"n_{idx}_{d}"
        nodes.append(
            {
                "id": node_id,
                "type": "agent",
                "constraints": [
                    {"id": f"c_{node_id}_{c}", "type": "budget_cap", "compliant": True}
                    for c in range(complexity)
                ],
            }
        )
        if d > 0:
            edges.append({"source": f"n_{idx}_{d-1}", "target": node_id})

    workflow = {
        "id": f"wf_{idx:05d}",
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "depth": depth,
            "complexity": complexity,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }
    return workflow

def generate_workflows(count: int, seed: int, output_path: Path) -> None:
    rng = random.Random(seed)
    workflows: List[Dict] = [_create_workflow(i, rng) for i in range(count)]

    # Write the JSON array to the requested location
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(workflows, indent=2), encoding="utf-8")
    print(f"[synthetic_workflow] generated {count} workflows → {output_path}")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python synthetic_workflow.py",
        description="Deterministic synthetic workflow generator",
    )
    parser.add_argument("--count", type=int, required=True, help="Number of workflows to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the generated workflows JSON file",
    )
    return parser

def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    generate_workflows(args.count, args.seed, args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
