import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


class SyntheticWorkflowGenerator:
    """Deterministic synthetic workflow generator."""

    def __init__(self, seed: int = 42):
        """Initialize the generator with a seed.

        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed
        random.seed(seed)

    def _generate_node(
        self, node_id: str, depth: int, complexity: int
    ) -> Dict[str, Any]:
        """Generate a single workflow node.

        Args:
            node_id: Unique node identifier.
            depth: Current depth level.
            complexity: Complexity level.

        Returns:
            Node dictionary.
        """
        # Generate constraints based on complexity
        num_constraints = min(complexity, 3)
        constraints = []
        rule_types = ["data_sovereignty", "access_control", "audit_logging"]

        for i in range(num_constraints):
            rule_type = rule_types[i % len(rule_types)]
            constraints.append({
                "id": f"{rule_type}_{i}",
                "type": rule_type,
                "compliant": random.random() > 0.05  # 95% compliant
            })

        return {
            "id": node_id,
            "type": "task",
            "depth": depth,
            "constraints": constraints,
            "edges": []
        }

    def _generate_dag(
        self, depth: int, complexity: int, workflow_id: str
    ) -> Dict[str, Any]:
        """Generate a DAG workflow.

        Args:
            depth: Maximum depth of the DAG.
            complexity: Complexity level (1-10).
            workflow_id: Unique workflow identifier.

        Returns:
            Workflow dictionary.
        """
        nodes = {}
        edges = []

        # Generate nodes
        node_count = max(2, complexity * 2)
        for i in range(node_count):
            node_depth = min(i % (depth + 1), depth)
            node_id = f"{workflow_id}_node_{i}"
            nodes[node_id] = self._generate_node(node_id, node_depth, complexity)

        # Generate edges (ensure DAG property)
        node_ids = list(nodes.keys())
        for i, src_id in enumerate(node_ids):
            # Connect to next few nodes
            for j in range(1, min(3, len(node_ids) - i)):
                if i + j < len(node_ids):
                    target_id = node_ids[i + j]
                    edges.append({
                        "source": src_id,
                        "target": target_id
                    })
                    nodes[src_id]["edges"].append({"target": target_id})

        return {
            "id": workflow_id,
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "depth": depth,
                "complexity": complexity,
                "node_count": node_count,
                "edge_count": len(edges)
            }
        }

    def generate_workflows(
        self, num_workflows: int = 500
    ) -> List[Dict[str, Any]]:
        """Generate a collection of synthetic workflows.

        Args:
            num_workflows: Number of workflows to generate.

        Returns:
            List of workflow dictionaries.
        """
        workflows = []
        depths = list(range(1, 21))  # 1-20

        for i in range(num_workflows):
            # Distribute depths uniformly
            depth = depths[i % len(depths)]
            complexity = (i % 10) + 1  # 1-10
            workflow_id = f"wf_{i:04d}"

            workflow = self._generate_dag(depth, complexity, workflow_id)
            workflows.append(workflow)

        return workflows

    def save_workflows(
        self, workflows: List[Dict[str, Any]], output_dir: str
    ) -> None:
        """Save workflows to JSON files.

        Args:
            workflows: List of workflow dictionaries.
            output_dir: Directory to save files.
        """
        os.makedirs(output_dir, exist_ok=True)

        for workflow in workflows:
            filename = f"workflow_{workflow['id']}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                json.dump(workflow, f, indent=2)


def main() -> None:
    """Main entry point for synthetic workflow generator."""
    import argparse

    parser = argparse.ArgumentParser(description="Synthetic Workflow Generator")
    parser.add_argument("--count", type=int, default=500, help="Number of workflows")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    generator = SyntheticWorkflowGenerator(seed=args.seed)
    workflows = generator.generate_workflows(args.count)
    generator.save_workflows(workflows, args.output)

    print(f"Generated {len(workflows)} workflows to {args.output}")


if __name__ == "__main__":
    main()
