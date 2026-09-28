import json
import os
import sys
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from engines.oracle_policy import OraclePolicyEngine

class CompressedContextEngine:
    """
    Executes workflows with compressed context using BFS/DFS truncation.
    """
    
    def __init__(self):
        self.oracle = OraclePolicyEngine()
    
    def _extract_subgraph(self, workflow: Dict[str, Any], depth: int, method: str = "bfs") -> Tuple[List[Dict], List[Dict]]:
        """
        Extract a minimal policy subgraph using BFS or DFS.
        
        Args:
            workflow: The full workflow
            depth: Maximum depth to traverse
            method: "bfs" or "dfs"
        
        Returns:
            Tuple of (nodes, edges) in the subgraph
        """
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        if depth == 0 or len(nodes) <= 1:
            return nodes[:1], []  # Edge case: single node

        # Build adjacency list
        adj = {}
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src not in adj:
                adj[src] = []
            adj[src].append(tgt)
    
        # BFS/DFS traversal
        visited = set()
        subgraph_nodes = []
        subgraph_edges = []

        if method == "bfs":
            # BFS
            queue = [nodes[0]["id"]]  # Start with first node
            while queue and len(visited) < len(nodes):
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                
                # Find node
                node_data = next((n for n in nodes if n["id"] == current), None)
                if node_data:
                    subgraph_nodes.append(node_data)
                
                # Add neighbors
                for neighbor in adj.get(current, []):
                    if neighbor not in visited:
                        queue.append(neighbor)

        else:
            # DFS
            stack = [nodes[0]["id"]]
            while stack and len(visited) < len(nodes):
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                
                node_data = next((n for n in nodes if n["id"] == current), None)
                if node_data:
                    subgraph_nodes.append(node_data)

                for neighbor in adj.get(current, []):
                    if neighbor not in visited:
                        stack.append(neighbor)

        # Filter edges to only include those within subgraph
        subgraph_edge_set = set()
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in visited and tgt in visited:
                subgraph_edges.append(edge)
                subgraph_edge_set.add((src, tgt))

        return subgraph_nodes, subgraph_edges

def execute(self, workflow: Dict[str, Any], depth: int, method: str = "bfs") -> Dict[str, Any]:
    """
    Execute a workflow with compressed context.
    
    Args:
        workflow: The workflow to execute
        depth: Compression depth
        method: "bfs" or "dfs"
    
    Returns:
        Execution log with validation results
    """
    workflow_id = workflow.get("id", "unknown")
    original_depth = workflow.get("depth", 0)
    nodes = workflow.get("nodes", [])
    metadata = workflow.get("metadata", {})
    
    # Check if workflow is marked as invalid
    is_valid = metadata.get("is_valid", True)
    
    # Handle edge cases
    if depth == 0 or len(nodes) <= 1:
        return {
            "workflow_id": workflow_id,
            "compression_depth": depth,
            "token_count": 0,
            "policy_violations": [],
            "context_reduction_pct": "[deferred]",
            "is_valid": is_valid,
            "status": "edge_case",
            "violation_details": [],
            "edge_case_reason": "single_node_graph" if len(nodes) <= 1 else "depth_zero"
        }
    
    # Extract subgraph
    subgraph_nodes, subgraph_edges = self._extract_subgraph(workflow, depth, method)
    
    # Log edge cases
    edge_case_log = {
        "workflow_id": workflow_id,
        "compression_depth": depth,
        "reason": "single_node_graph" if len(nodes) <= 1 else "depth_zero" if depth == 0 else "truncation",
        "subgraph_nodes": len(subgraph_nodes),
        "original_nodes": len(nodes)
    }

    # Validate subgraph nodes
    violations = []
    violation_details = []
    
    for node in subgraph_nodes:
        node_id = node.get("id")
        is_node_valid, violation = self.oracle.validate(workflow, node)

        if not is_node_valid:
            violations.append(violation)
            if node_id and violation:
                violation_details.append({
                    "node_id": node_id,
                    "rule_id": violation.get("rule_id", "unknown"),
                    "truncated": node_id not in [n["id"] for n in nodes]  # Should always be False, but for completeness
                })

    # Calculate token count (simplified)
    full_token_count = len(str(workflow)) // 4
    compressed_token_count = len(str({"nodes": subgraph_nodes, "edges": subgraph_edges})) // 4

    # Calculate context reduction percentage
    if full_token_count > 0:
        reduction_pct = (1 - (compressed_token_count / full_token_count)) * 100
    else:
        reduction_pct = 0.0

    return {
        "workflow_id": workflow_id,
        "compression_depth": depth,
        "token_count": compressed_token_count,
        "policy_violations": violations,
        "context_reduction_pct": reduction_pct,
        "is_valid": is_valid and len(violations) == 0,
        "status": "normal" if len(violations) == 0 else "edge_case",
        "violation_details": violation_details,
        "original_token_count": full_token_count,
        "subgraph_size": len(subgraph_nodes)
    }

def main():
    """
    CLI entry point for compressed context execution.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute workflows with compressed context")
    parser.add_argument("--workflow", type=str, required=True, help="Input workflow file path")
    parser.add_argument("--depths", type=int, nargs="+", default=[1, 2, 4, 6, 8, 10], help="Compression depths to test")
    parser.add_argument("--method", type=str, default="bfs", choices=["bfs", "dfs"], help="Traversal method")
    parser.add_argument("--output", type=str, required=True, help="Output file path for execution logs")
    
    args = parser.parse_args()
    
    # Load workflows
    workflow_file = Path(args.workflow)
    if not workflow_file.exists():
        print(f"Error: Workflow file not found: {args.workflow}", file=sys.stderr)
        sys.exit(1)
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    if not isinstance(workflows, list):
        workflows = [workflows]
    
    # Execute each workflow for each depth
    engine = CompressedContextEngine()
    all_logs = []
    
    for workflow in workflows:
        for depth in args.depths:
            log = engine.execute(workflow, depth, args.method)
            all_logs.append(log)
    
    # Save logs
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_logs, f, indent=2)
    
    print(f"Executed {len(workflows)} workflows across {len(args.depths)} depths")
    print(f"Total logs: {len(all_logs)}")
    print(f"Saved logs to {args.output}")

if __name__ == "__main__":
    main()
