"""
code/generators/synthetic_workflow.py
-------------------------------------

Deterministic synthetic workflow generator.

The script can be used as a command‑line tool (via ``--count``, ``--seed`` and
``--output``) or imported as a module exposing the ``SyntheticWorkflowGenerator``
class.  The generated workflows conform to ``contracts/workflow.schema.yaml``.
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Dict

DEFAULT_SEED = 42


class SyntheticWorkflowGenerator:
    """Generate a list of synthetic workflow dictionaries.

    Each workflow contains a minimal directed graph with ``nodes`` and ``edges``,
    plus a ``metadata`` block required by the schema.  The generation is fully
    deterministic given a ``seed`` and ``count``.
    """

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed
        self.rng = random.Random(seed)

    def _make_node(self, idx: int) -> Dict:
        """Create a single node dictionary."""
        return {
            "id": f"node-{idx}",
            "type": "agent",
            "constraints": [
                {
                    "id": f"constraint-{idx}",
                    "type": "budget_cap",
                    "compliant": self.rng.choice([True, False]),
                }
            ],
        }

    def _make_edge(self, src_idx: int, dst_idx: int) -> Dict:
        """Create a directed edge from ``src_idx`` to ``dst_idx``."""
        return {"source": f"node-{src_idx}", "target": f"node-{dst_idx}"}

    def generate_workflows(self, count: int) -> List[Dict]:
        """Generate ``count`` workflow objects."""
        workflows = []
        for i in range(count):
            depth = self.rng.randint(1, 5)          # delegation depth
            complexity = self.rng.randint(1, 10)    # arbitrary complexity metric
            node_count = depth + 1                  # simple chain plus root
            nodes = [self._make_node(j) for j in range(node_count)]
            edges = [
                self._make_edge(j, j + 1) for j in range(node_count - 1)
            ]

            workflow = {
                "id": f"workflow-{i}",
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "depth": depth,
                    "complexity": complexity,
                    "node_count": node_count,
                    "edge_count": len(edges),
                },
            }
            workflows.append(workflow)
        return workflows

    def write_to_file(self, workflows: List[Dict], output_path: Path) -> None:
        """Serialize ``workflows`` as a JSON array to ``output_path``."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(workflows, fh, indent=2)

def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="synthetic_workflow",
        description="Generate deterministic synthetic workflows."
    )
    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of workflows to generate."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for deterministic generation."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the generated workflows JSON file."
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    generator = SyntheticWorkflowGenerator(seed=args.seed)
    workflows = generator.generate_workflows(count=args.count)
    generator.write_to_file(workflows, args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
