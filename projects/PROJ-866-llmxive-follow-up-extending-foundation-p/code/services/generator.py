"""
code.services.generator
-----------------------

Deterministic synthetic workflow generator.

This script creates ``data/raw/workflows.json`` containing a
configurable number of synthetic workflows that conform to the
``contracts/workflow.schema.yaml`` JSON‑schema.

Usage (as a module):
    python -m code.services.generator --n 500 --seed 42

The generator is fully deterministic given the same ``seed`` value.
It guarantees:
    * exactly ``n`` workflow objects,
    * ``metadata.depth`` (delegation depth) between 1 and 10,
    * at least 25 workflows per depth level,
    * schema compliance for every workflow.
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Dict

import yaml
import jsonschema

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DEFAULT_WORKFLOW_COUNT = 500
DEFAULT_SEED = 42
MIN_DEPTH = 1
MAX_DEPTH = 10
MIN_WORKFLOWS_PER_DEPTH = 25

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_schema(schema_path: Path) -> Dict:
    """Load a JSON‑schema from *schema_path*."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_workflow(workflow: Dict, schema: Dict) -> None:
    """Validate a single workflow against *schema*; raise on failure."""
    jsonschema.validate(instance=workflow, schema=schema)

def generate_node(workflow_idx: int, node_idx: int) -> Dict:
    """Create a node dictionary."""
    return {
        "id": f"node_{workflow_idx}_{node_idx}",
        "type": "agent",
        "constraints": [
            {
                "id": f"budget_{workflow_idx}_{node_idx}",
                "type": "budget_cap",
                # Randomly decide compliance; deterministic because RNG is seeded.
                "compliant": random.choice([True, False]),
            }
        ],
    }

def generate_workflow(workflow_idx: int, depth: int) -> Dict:
    """
    Generate a single workflow.

    * ``depth`` is stored in ``metadata.depth`` and also determines the
      minimum number of nodes (a simple linear chain).
    """
    # Random complexity for the workflow (1‑5)
    complexity = random.randint(1, 5)

    # Number of nodes: depth + 1‑3 extra nodes for variability
    extra_nodes = random.randint(1, 3)
    node_count = depth + extra_nodes

    # Build nodes
    nodes = [generate_node(workflow_idx, i) for i in range(node_count)]

    # Build a simple linear edge list (source -> target)
    edges = [
        {"source": nodes[i]["id"], "target": nodes[i + 1]["id"]}
        for i in range(node_count - 1)
    ]

    workflow = {
        "id": f"workflow_{workflow_idx:04d}",
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "depth": depth,
            "complexity": complexity,
            "node_count": node_count,
            "edge_count": len(edges),
        },
    }
    return workflow

def distribute_depths(total: int) -> List[int]:
    """
    Return a list of ``total`` delegation depths (1‑10) such that
    each depth appears at least ``MIN_WORKFLOWS_PER_DEPTH`` times.
    The distribution is deterministic: we first allocate the minimum
    per depth, then fill the remainder cyclically.
    """
    depths = []
    # Allocate the mandatory minimum per depth
    for d in range(MIN_DEPTH, MAX_DEPTH + 1):
        depths.extend([d] * MIN_WORKFLOWS_PER_DEPTH)

    remaining = total - len(depths)
    # Fill remaining slots cyclically over the depth range
    depth_cycle = list(range(MIN_DEPTH, MAX_DEPTH + 1))
    idx = 0
    while remaining > 0:
        depths.append(depth_cycle[idx % len(depth_cycle)])
        idx += 1
        remaining -= 1

    # Trim in case we overshot (should not happen)
    return depths[:total]

def generate_workflows(count: int, seed: int) -> List[Dict]:
    """Generate *count* workflows using *seed* for reproducibility."""
    random.seed(seed)
    depths = distribute_depths(count)

    workflows = [
        generate_workflow(i, depth) for i, depth in enumerate(depths)
    ]
    return workflows

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic synthetic workflow generator"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=DEFAULT_WORKFLOW_COUNT,
        help="Number of workflows to generate (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for deterministic generation (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.data("raw", "workflows.json")),
        help="Output JSON file path (default: data/raw/workflows.json)",
    )
    args = parser.parse_args()

    log.info(
        "Generating %d synthetic workflows with seed %d", args.n, args.seed
    )

    # ------------------------------------------------------------------
    # 1️⃣ Generate data
    # ------------------------------------------------------------------
    workflows = generate_workflows(args.n, args.seed)

    # ------------------------------------------------------------------
    # 2️⃣ Validate against schema
    # ------------------------------------------------------------------
    schema_path = paths.root / "contracts" / "workflow.schema.yaml"
    schema = load_schema(schema_path)

    for wf in workflows:
        validate_workflow(wf, schema)

    # ------------------------------------------------------------------
    # 3️⃣ Write output
    # ------------------------------------------------------------------
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(workflows, f, indent=2, sort_keys=False)

    log.info("Wrote %d workflows to %s", len(workflows), output_path)

if __name__ == "__main__":
    main()