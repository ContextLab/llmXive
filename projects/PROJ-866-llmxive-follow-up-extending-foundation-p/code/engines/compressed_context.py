import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import deque
from engines.oracle_policy import OraclePolicyEngine


class CompressedContextEngine:
    """Executes workflows with compressed context (truncation)."""

    def __init__(self, method: str = "bfs"):
        self.method = method
        self.oracle = OraclePolicyEngine()

    def _traverse(self, workflow: Dict[str, Any], depth: int) -> Set[str]:
        """Traverse workflow graph to get included nodes.

        Args:
            workflow: Workflow dictionary.
            depth: Traversal depth limit.

        Returns:
            Set of included node IDs.
        """
        nodes = workflow["nodes"]
        edges = workflow["edges"]
        
        # Find start nodes (nodes with no incoming edges)
        incoming = {n: 0 for n in nodes}
        for edge in edges:
            if edge["target"] in incoming:
                incoming[edge["target"]] += 1
        
        start_nodes = [n for n, count in incoming.items() if count == 0]
        if not start_nodes:
            start_nodes = list(nodes.keys())[:1]

        included = set()
        queue = deque([(start_nodes[0], 0)])
        
        while queue:
            current, current_depth = queue.popleft()
            if current_depth > depth:
                continue
            
            if current in included:
                continue
            
            included.add(current)
            
            # Find children
            for edge in edges:
                if edge["source"] == current:
                    queue.append((edge["target"], current_depth + 1))
        
        return included

    def execute(self, workflow: Dict[str, Any], depth: int = 1) -> Dict[str, Any]:
        """Execute workflow with compressed context.

        Args:
            workflow: Workflow dictionary.
            depth: Compression depth.

        Returns:
            Execution log dictionary.
        """
        workflow_id = workflow["id"]
        nodes = workflow["nodes"]
        metadata = workflow["metadata"]

        # Edge cases
        if len(nodes) <= 1 or metadata.get("depth", 0) == 0 or depth == 0:
            return {
                "workflow_id": workflow_id,
                "compression_depth": depth,
                "token_count": 0,
                "policy_violations": [],
                "context_reduction_pct": "[deferred]",
                "is_valid": True,
                "status": "edge_case"
            }

        # Determine included nodes
        included_nodes = self._traverse(workflow, depth)
        excluded_nodes = set(nodes.keys()) - included_nodes

        # Check for policy violations due to truncation
        violations = []
        for excluded_id in excluded_nodes:
            # If excluded node had critical constraints, record violation
            excluded_node = nodes[excluded_id]
            for constraint in excluded_node.get("constraints", []):
                if not constraint.get("compliant", True):
                    violations.append({
                        "node_id": excluded_id,
                        "rule_id": constraint.get("type", "unknown"),
                        "details": f"Node truncated at depth {depth}"
                    })

        # Calculate token count (mock, replaced by T022)
        # Count only included nodes
        included_workflow = {
            "id": workflow_id,
            "nodes": {k: v for k, v in nodes.items() if k in included_nodes},
            "edges": workflow["edges"]
        }
        token_count = len(str(included_workflow)) * 4
        
        # Calculate reduction percentage
        full_token_count = len(str(workflow)) * 4
        if full_token_count > 0:
            reduction_pct = (1 - (token_count / full_token_count)) * 100
        else:
            reduction_pct = 0.0

        return {
            "workflow_id": workflow_id,
            "compression_depth": depth,
            "token_count": token_count,
            "policy_violations": violations,
            "context_reduction_pct": reduction_pct,
            "is_valid": len(violations) == 0,
            "status": "normal" if len(violations) == 0 else "violation_detected"
        }


def main() -> None:
    """Main entry point for compressed context execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Compressed Context Engine")
    parser.add_argument("--workflow", type=str, required=True, help="Input workflow file")
    parser.add_argument("--depth", type=int, default=1, help="Compression depth")
    parser.add_argument("--method", type=str, default="bfs", choices=["bfs", "dfs"])
    parser.add_argument("--output", type=str, required=True, help="Output log file")

    args = parser.parse_args()

    engine = CompressedContextEngine(method=args.method)
    
    with open(args.workflow, 'r') as f:
        workflow = json.load(f)
    
    log = engine.execute(workflow, depth=args.depth)
    
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"Executed {args.workflow} (depth={args.depth}) -> {args.output}")


if __name__ == "__main__":
    main()
