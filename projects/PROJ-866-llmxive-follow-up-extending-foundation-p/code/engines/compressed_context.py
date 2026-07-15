"""
Compressed Context Execution Engine.

Executes workflows using compressed context (BFS/DFS truncation) and measures
token counts and policy violations.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import deque

# Import the token counter utility
from utils.token_counter import count_tokens_cl100k_base

class CompressedContextEngine:
    """
    Executes workflows with compressed context using BFS/DFS truncation.
    
    This engine extracts minimal policy subgraphs based on a configurable
    traversal depth and counts actual tokens used.
    """
    
    def __init__(self, max_depth: int = 2, traversal_mode: str = "bfs"):
        """
        Initialize the compressed context engine.
        
        Args:
            max_depth: Maximum depth for BFS/DFS traversal (0 = no context).
            traversal_mode: 'bfs' for Breadth-First Search, 'dfs' for Depth-First Search.
        """
        if traversal_mode not in ("bfs", "dfs"):
            raise ValueError(f"traversal_mode must be 'bfs' or 'dfs', got '{traversal_mode}'")
        
        self.max_depth = max_depth
        self.traversal_mode = traversal_mode
    
    def _traverse_bfs(self, workflow: Dict[str, Any], start_node_id: str) -> Set[str]:
        """
        Perform BFS traversal to collect nodes within max_depth.
        
        Args:
            workflow: The workflow dictionary with 'nodes' and 'edges'.
            start_node_id: The ID of the starting node.
            
        Returns:
            A set of node IDs included in the compressed context.
        """
        if not workflow.get("nodes"):
            return set()
        
        included_nodes = set()
        queue = deque([(start_node_id, 0)])
        visited = set()
        
        while queue:
            node_id, depth = queue.popleft()
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            
            if depth > self.max_depth:
                continue
            
            included_nodes.add(node_id)
            
            # Find children (nodes this node points to)
            for edge in workflow.get("edges", []):
                if edge.get("source") == node_id:
                    target = edge.get("target")
                    if target not in visited:
                        queue.append((target, depth + 1))
        
        return included_nodes
    
    def _traverse_dfs(self, workflow: Dict[str, Any], start_node_id: str) -> Set[str]:
        """
        Perform DFS traversal to collect nodes within max_depth.
        
        Args:
            workflow: The workflow dictionary with 'nodes' and 'edges'.
            start_node_id: The ID of the starting node.
            
        Returns:
            A set of node IDs included in the compressed context.
        """
        if not workflow.get("nodes"):
            return set()
        
        included_nodes = set()
        stack = [(start_node_id, 0)]
        visited = set()
        
        while stack:
            node_id, depth = stack.pop()
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            
            if depth > self.max_depth:
                continue
            
            included_nodes.add(node_id)
            
            # Find children (nodes this node points to)
            # Using reversed order to maintain consistent traversal order
            children = []
            for edge in workflow.get("edges", []):
                if edge.get("source") == node_id:
                    target = edge.get("target")
                    if target not in visited:
                        children.append(target)
            
            for target in reversed(children):
                stack.append((target, depth + 1))
        
        return included_nodes
    
    def _build_context_string(self, workflow: Dict[str, Any], included_node_ids: Set[str]) -> str:
        """
        Build a string representation of the compressed context.
        
        Args:
            workflow: The full workflow dictionary.
            included_node_ids: Set of node IDs to include in context.
            
        Returns:
            A string representation of the compressed context.
        """
        context_parts = []
        
        # Include nodes
        context_parts.append("=== COMPRESSED CONTEXT ===")
        context_parts.append("NODES:")
        for node in workflow.get("nodes", []):
            if node.get("id") in included_node_ids:
                node_info = f"  - ID: {node.get('id')}, Type: {node.get('type')}, Policy: {node.get('policy', 'none')}"
                context_parts.append(node_info)
        
        # Include relevant edges
        context_parts.append("EDGES:")
        for edge in workflow.get("edges", []):
            if edge.get("source") in included_node_ids and edge.get("target") in included_node_ids:
                edge_info = f"  - {edge.get('source')} -> {edge.get('target')}"
                context_parts.append(edge_info)
        
        context_parts.append("=== END CONTEXT ===")
        return "\n".join(context_parts)
    
    def _detect_violations(self, workflow: Dict[str, Any], included_node_ids: Set[str]) -> List[Dict[str, Any]]:
        """
        Detect policy violations caused by context truncation.
        
        Args:
            workflow: The full workflow dictionary.
            included_node_ids: Set of node IDs included in the compressed context.
            
        Returns:
            A list of violation dictionaries.
        """
        violations = []
        
        # Check for edges that cross the boundary (source in context, target outside)
        for edge in workflow.get("edges", []):
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            if source_id in included_node_ids and target_id not in included_node_ids:
                # Check if the target node has a policy that might be violated
                target_node = None
                for node in workflow.get("nodes", []):
                    if node.get("id") == target_id:
                        target_node = node
                        break
                
                if target_node and target_node.get("policy"):
                    violations.append({
                        "type": "policy_violation",
                        "reason": f"Truncation cut off required node '{target_id}' with policy '{target_node.get('policy')}'",
                        "source_node": source_id,
                        "target_node": target_id,
                        "policy": target_node.get("policy")
                    })
        
        return violations
    
    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow with compressed context.
        
        Args:
            workflow: The workflow dictionary to execute.
            
        Returns:
            An execution log dictionary with token counts and violations.
        """
        # Handle edge cases
        if not workflow.get("nodes"):
            return {
                "status": "edge_case",
                "context_reduction_pct": "[deferred]",
                "token_count": 0,
                "violations": [],
                "included_nodes": [],
                "message": "Workflow has no nodes"
            }
        
        # Determine start node (first node or node with no incoming edges)
        start_node_id = workflow["nodes"][0]["id"]
        for node in workflow.get("nodes", []):
            has_incoming = False
            for edge in workflow.get("edges", []):
                if edge.get("target") == node.get("id"):
                    has_incoming = True
                    break
            if not has_incoming:
                start_node_id = node.get("id")
                break
        
        # Traverse to get included nodes
        if self.traversal_mode == "bfs":
            included_node_ids = self._traverse_bfs(workflow, start_node_id)
        else:
            included_node_ids = self._traverse_dfs(workflow, start_node_id)
        
        # Build context string
        context_string = self._build_context_string(workflow, included_node_ids)
        
        # Count actual tokens using tiktoken
        token_count = count_tokens_cl100k_base(context_string)
        
        # Calculate context reduction percentage
        full_context_string = json.dumps(workflow, separators=(',', ':'))
        full_token_count = count_tokens_cl100k_base(full_context_string)
        
        if full_token_count > 0:
            context_reduction_pct = round(100 * (1 - token_count / full_token_count), 2)
        else:
            context_reduction_pct = 0.0
        
        # Detect violations
        violations = self._detect_violations(workflow, included_node_ids)
        
        # Build execution log
        execution_log = {
            "status": "completed",
            "context_reduction_pct": context_reduction_pct,
            "token_count": token_count,
            "full_token_count": full_token_count,
            "violations": violations,
            "included_nodes": sorted(list(included_node_ids)),
            "traversal_mode": self.traversal_mode,
            "max_depth": self.max_depth,
            "workflow_id": workflow.get("id", "unknown")
        }
        
        return execution_log
    
    def execute_batch(self, workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple workflows with compressed context.
        
        Args:
            workflows: A list of workflow dictionaries.
            
        Returns:
            A list of execution log dictionaries.
        """
        return [self.execute(workflow) for workflow in workflows]


def main():
    """
    Main entry point for testing the compressed context engine.
    
    Reads workflows from a JSON file, executes them with compressed context,
    and outputs the results.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute workflows with compressed context")
    parser.add_argument("--input", type=str, required=True, help="Path to input workflows JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to output execution logs JSON file")
    parser.add_argument("--depth", type=int, default=2, help="Maximum traversal depth")
    parser.add_argument("--mode", type=str, default="bfs", choices=["bfs", "dfs"], help="Traversal mode")
    
    args = parser.parse_args()
    
    # Load workflows
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r') as f:
        workflows = json.load(f)
    
    # Handle both list and dict with 'workflows' key
    if isinstance(workflows, dict) and "workflows" in workflows:
        workflows = workflows["workflows"]
    elif isinstance(workflows, dict):
        workflows = [workflows]
    
    print(f"Loaded {len(workflows)} workflows")
    
    # Initialize engine
    engine = CompressedContextEngine(max_depth=args.depth, traversal_mode=args.mode)
    
    # Execute workflows
    execution_logs = engine.execute_batch(workflows)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(execution_logs, f, indent=2)
    
    print(f"Saved {len(execution_logs)} execution logs to {output_path}")
    
    # Print summary
    total_tokens = sum(log.get("token_count", 0) for log in execution_logs)
    total_violations = sum(len(log.get("violations", [])) for log in execution_logs)
    avg_reduction = sum(log.get("context_reduction_pct", 0) for log in execution_logs) / len(execution_logs) if execution_logs else 0
    
    print(f"\nSummary:")
    print(f"  Total workflows: {len(execution_logs)}")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Total violations: {total_violations}")
    print(f"  Average context reduction: {avg_reduction:.2f}%")


if __name__ == "__main__":
    main()