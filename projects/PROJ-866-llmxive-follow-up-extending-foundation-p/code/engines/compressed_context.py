import json
import os
import sys
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import deque
from engines.oracle_policy import OraclePolicyEngine


class CompressedContextEngine:
    """Executes workflows with compressed context using BFS/DFS traversal."""

    def __init__(self, depth: int = 1, method: str = "bfs"):
        """Initialize the compressed context engine.
        
        Args:
            depth: Maximum traversal depth for context compression.
            method: Traversal method, either 'bfs' or 'dfs'.
        """
        self.depth = depth
        self.method = method
        self.oracle = OraclePolicyEngine()
        self._verify_oracle_isolation()

    def _verify_oracle_isolation(self) -> None:
        """Runtime check to ensure Oracle is used only for validation.
        
        This enforces Constitution Principle VI: The Oracle must remain the
        independent ground truth. This check verifies that no execution logic
        is implemented directly in this engine that should belong to the Oracle.
        
        Raises:
            RuntimeError: If the engine attempts to implement policy logic itself.
        """
        # Get the source code of this class
        source = inspect.getsource(self.__class__)
        
        # Define forbidden patterns that indicate policy logic implementation
        forbidden_patterns = [
            "if node_data.get('budget')",
            "if node_data.get('sovereignty')",
            "if node_data.get('latency')",
            "node_data['budget'] <",
            "node_data['sovereignty'] >=",
            "node_data['latency'] >=",
            "budget_limit =",
            "sovereignty_check =",
            "latency_threshold =",
            "self._check_budget",
            "self._check_sovereignty",
            "self._check_latency",
            "def _validate_budget",
            "def _validate_sovereignty",
            "def _validate_latency"
        ]
        
        violations = []
        for pattern in forbidden_patterns:
            if pattern in source:
                violations.append(pattern)
        
        if violations:
            raise RuntimeError(
                f"Constitution Principle VI Violation: CompressedContextEngine contains "
                f"policy logic that should be in OraclePolicyEngine. "
                f"Detected forbidden patterns: {violations}"
            )
        
        # Verify that we are using the Oracle for validation
        if "self.oracle.validate" not in source:
            raise RuntimeError(
                "Constitution Principle VI Violation: CompressedContextEngine must use "
                "OraclePolicyEngine for validation. No call to self.oracle.validate found."
            )

    def _traverse_graph(self, workflow: Dict[str, Any], start_node: str) -> Tuple[Set[str], Dict[str, Any]]:
        """Traverse the workflow graph up to the specified depth.
        
        Args:
            workflow: The workflow dictionary.
            start_node: The starting node ID.
        
        Returns:
            A tuple of (visited_nodes, subgraph_data).
        """
        nodes = workflow["nodes"]
        edges = workflow["edges"]
        
        visited = set()
        subgraph_edges = []
        
        if self.method == "bfs":
            queue = deque([(start_node, 0)])
            while queue:
                current_node, current_depth = queue.popleft()
                
                if current_node in visited or current_depth > self.depth:
                    continue
                
                visited.add(current_node)
                
                # Add edges from this node
                for edge in edges:
                    if edge["source"] == current_node:
                        subgraph_edges.append(edge)
                        target = edge["target"]
                        if target not in visited and current_depth < self.depth:
                            queue.append((target, current_depth + 1))
                    elif edge["target"] == current_node:
                        subgraph_edges.append(edge)
                        source = edge["source"]
                        if source not in visited and current_depth < self.depth:
                            queue.append((source, current_depth + 1))
        else:  # dfs
            stack = [(start_node, 0)]
            while stack:
                current_node, current_depth = stack.pop()
                
                if current_node in visited or current_depth > self.depth:
                    continue
                
                visited.add(current_node)
                
                # Add edges from this node
                for edge in edges:
                    if edge["source"] == current_node:
                        subgraph_edges.append(edge)
                        target = edge["target"]
                        if target not in visited and current_depth < self.depth:
                            stack.append((target, current_depth + 1))
                    elif edge["target"] == current_node:
                        subgraph_edges.append(edge)
                        source = edge["source"]
                        if source not in visited and current_depth < self.depth:
                            stack.append((source, current_depth + 1))
        
        # Build subgraph nodes
        subgraph_nodes = {k: v for k, v in nodes.items() if k in visited}
        
        return visited, {"nodes": subgraph_nodes, "edges": subgraph_edges}

    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with compressed context.

        Args:
            workflow: Workflow dictionary.

        Returns:
            Execution log dictionary.
        """
        workflow_id = workflow["id"]
        nodes = workflow["nodes"]
        edges = workflow["edges"]
        metadata = workflow["metadata"]

        # Check for edge cases
        if len(nodes) <= 1 or metadata.get("depth", 0) == 0:
            return {
                "workflow_id": workflow_id,
                "compression_depth": self.depth,
                "token_count": 0,
                "policy_violations": [],
                "context_reduction_pct": "[deferred]",
                "is_valid": True,
                "status": "edge_case",
                "edge_case_reason": "single_node_graph" if len(nodes) <= 1 else "depth_zero"
            }

        # Select start node (first node by key)
        start_node = list(nodes.keys())[0]
        
        # Traverse to get compressed subgraph
        visited_nodes, subgraph = self._traverse_graph(workflow, start_node)
        
        violations = []
        valid = True
        truncated_nodes = []
        
        # Validate nodes in the compressed subgraph
        for node_id, node_data in subgraph["nodes"].items():
            result = self.oracle.validate(workflow, node_data)
            if not result["compliant"]:
                violations.append({
                    "node_id": node_id,
                    "rule_id": result.get("rule_id", "unknown"),
                    "details": result.get("details", "Constraint violation")
                })
                valid = False
        
        # Identify truncated nodes (nodes not in visited but in original)
        for node_id in nodes.keys():
            if node_id not in visited_nodes:
                truncated_nodes.append(node_id)
                # Log truncation as a potential policy violation
                violations.append({
                    "node_id": node_id,
                    "rule_id": "truncation",
                    "details": f"Node truncated due to compression depth {self.depth}"
                })
                valid = False

        # Calculate token count for the subgraph
        token_count = len(str(subgraph)) * 4  # Rough estimate

        # Calculate context reduction percentage
        full_token_count = len(str(workflow)) * 4
        if full_token_count > 0:
            context_reduction_pct = (1 - (token_count / full_token_count)) * 100
        else:
            context_reduction_pct = 0.0

        return {
            "workflow_id": workflow_id,
            "compression_depth": self.depth,
            "token_count": token_count,
            "policy_violations": violations,
            "context_reduction_pct": context_reduction_pct,
            "is_valid": valid and len(violations) == 0,
            "status": "normal" if valid else "violation_detected",
            "truncated_nodes": truncated_nodes
        }


def main() -> None:
    """Main entry point for compressed context execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Compressed Context Engine")
    parser.add_argument("--workflow", type=str, required=True, help="Input workflow file")
    parser.add_argument("--output", type=str, required=True, help="Output log file")
    parser.add_argument("--depth", type=int, default=1, help="Compression depth")
    parser.add_argument("--method", type=str, default="bfs", choices=["bfs", "dfs"], help="Traversal method")

    args = parser.parse_args()

    engine = CompressedContextEngine(depth=args.depth, method=args.method)
    
    with open(args.workflow, 'r') as f:
        workflow = json.load(f)
    
    log = engine.execute(workflow)
    
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"Executed {args.workflow} (depth={args.depth}, method={args.method}) -> {args.output}")


if __name__ == "__main__":
    main()