import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import deque

from utils.token_counter import count_tokens_cl100k_base


class CompressedContextEngine:
    """Engine for executing workflows with compressed context using BFS/DFS."""

    def __init__(self, traversal_depth: int = 2):
        """Initialize the engine with a traversal depth.

        Args:
            traversal_depth: Maximum depth for BFS/DFS traversal.
        """
        self.traversal_depth = traversal_depth

    def _traverse_bfs(
        self, graph: Dict[str, Any], start_node: str, max_depth: int
    ) -> Set[str]:
        """Perform BFS traversal up to max_depth.

        Args:
            graph: Workflow graph.
            start_node: Starting node ID.
            max_depth: Maximum traversal depth.

        Returns:
            Set of reachable node IDs.
        """
        visited = set()
        queue = deque([(start_node, 0)])

        while queue:
            node_id, depth = queue.popleft()
            if depth > max_depth:
                continue
            if node_id in visited:
                continue

            visited.add(node_id)
            node = graph.get("nodes", {}).get(node_id, {})
            edges = node.get("edges", [])

            for edge in edges:
                neighbor = edge.get("target")
                if neighbor and neighbor not in visited:
                    queue.append((neighbor, depth + 1))

        return visited

    def _traverse_dfs(
        self, graph: Dict[str, Any], start_node: str, max_depth: int
    ) -> Set[str]:
        """Perform DFS traversal up to max_depth.

        Args:
            graph: Workflow graph.
            start_node: Starting node ID.
            max_depth: Maximum traversal depth.

        Returns:
            Set of reachable node IDs.
        """
        visited = set()
        stack = [(start_node, 0)]

        while stack:
            node_id, depth = stack.pop()
            if depth > max_depth:
                continue
            if node_id in visited:
                continue

            visited.add(node_id)
            node = graph.get("nodes", {}).get(node_id, {})
            edges = node.get("edges", [])

            for edge in reversed(edges):
                neighbor = edge.get("target")
                if neighbor and neighbor not in visited:
                    stack.append((neighbor, depth + 1))

        return visited

    def execute(
        self, workflow: Dict[str, Any], traversal_method: str = "bfs"
    ) -> Dict[str, Any]:
        """Execute a workflow with compressed context.

        Args:
            workflow: The workflow to execute.
            traversal_method: 'bfs' or 'dfs'.

        Returns:
            Execution log dictionary.
        """
        nodes = workflow.get("nodes", {})
        edges = workflow.get("edges", [])
        metadata = workflow.get("metadata", {})

        # Handle edge cases
        if len(nodes) <= 1 or metadata.get("depth", 0) == 0:
            return {
                "workflow_id": workflow.get("id", "unknown"),
                "compression_depth": self.traversal_depth,
                "token_count": 0,
                "context_reduction_pct": "[deferred]",
                "is_valid": True,
                "status": "edge_case",
                "policy_violations": [],
                "violation_details": [],
            }

        # Determine start node (usually the first or root)
        start_node = list(nodes.keys())[0]

        # Perform traversal
        if traversal_method == "bfs":
            reachable_nodes = self._traverse_bfs(workflow, start_node, self.traversal_depth)
        else:
            reachable_nodes = self._traverse_dfs(workflow, start_node, self.traversal_depth)

        # Identify truncated nodes
        all_nodes = set(nodes.keys())
        truncated_nodes = all_nodes - reachable_nodes

        # Build subgraph
        subgraph_nodes = {k: v for k, v in nodes.items() if k in reachable_nodes}
        subgraph_edges = [
            e for e in edges if e.get("source") in reachable_nodes
        ]

        # Calculate token count
        subgraph_json = json.dumps({"nodes": subgraph_nodes, "edges": subgraph_edges})
        token_count = count_tokens_cl100k_base(subgraph_json)

        # Calculate context reduction percentage
        total_tokens = count_tokens_cl100k_base(json.dumps(workflow))
        if total_tokens > 0:
            reduction_pct = round((1 - token_count / total_tokens) * 100, 2)
        else:
            reduction_pct = 0.0

        # Check for policy violations due to truncation
        violations = []
        violation_details = []

        for node_id in truncated_nodes:
            node = nodes.get(node_id, {})
            rules = node.get("constraints", [])
            for rule in rules:
                rule_id = rule.get("id", "unknown")
                violations.append(f"Policy violation: {rule_id}")
                violation_details.append({
                    "node_id": node_id,
                    "rule_id": rule_id,
                    "reason": f"Node truncated at depth {self.traversal_depth}"
                })

        is_valid = len(violations) == 0

        return {
            "workflow_id": workflow.get("id", "unknown"),
            "compression_depth": self.traversal_depth,
            "token_count": token_count,
            "context_reduction_pct": reduction_pct,
            "is_valid": is_valid,
            "status": "normal" if not is_valid else "valid",
            "policy_violations": violations,
            "violation_details": violation_details,
            "depth": metadata.get("depth", 0),
            "complexity": metadata.get("complexity", 0),
        }


def main() -> None:
    """Main entry point for compressed context engine."""
    import argparse

    parser = argparse.ArgumentParser(description="Compressed Context Engine")
    parser.add_argument("--workflow", type=str, required=True, help="Workflow JSON file")
    parser.add_argument("--depth", type=int, default=2, help="Traversal depth")
    parser.add_argument("--method", type=str, default="bfs", choices=["bfs", "dfs"])
    parser.add_argument("--output", type=str, required=True, help="Output log file")

    args = parser.parse_args()

    with open(args.workflow, "r") as f:
        workflow = json.load(f)

    engine = CompressedContextEngine(traversal_depth=args.depth)
    log = engine.execute(workflow, traversal_method=args.method)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(log, f, indent=2)

    print(f"Execution log saved to {args.output}")


if __name__ == "__main__":
    main()
