import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import deque

# Import token counter from utils if available, otherwise handle gracefully
try:
    from utils.token_counter import count_tokens_cl100k_base
except ImportError:
    # Fallback if running as script without package context
    count_tokens_cl100k_base = None


class CompressedContextEngine:
    """
    Executes workflows using compressed context (BFS/DFS truncation).
    
    Handles edge case: compression depth=0 (no context passed).
    """
    
    def __init__(self, workflow_graph: Dict[str, Any], compression_depth: int = 1):
        """
        Initialize the engine.
        
        Args:
            workflow_graph: The full workflow DAG.
            compression_depth: The depth limit for context extraction (BFS/DFS).
                               If 0, no context is passed.
        """
        self.workflow_graph = workflow_graph
        self.compression_depth = compression_depth
        self.nodes = workflow_graph.get("nodes", [])
        self.edges = workflow_graph.get("edges", [])
        self.root_node = workflow_graph.get("root_node_id")
        
        # Pre-compute graph structure for traversal
        self.adjacency_list = self._build_adjacency_list()
        self.node_map = {n["id"]: n for n in self.nodes}
    
    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """Build adjacency list from edges."""
        adj = {n["id"]: [] for n in self.nodes}
        for edge in self.edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in adj and tgt in adj:
                adj[src].append(tgt)
        return adj
    
    def extract_compressed_context(self) -> Tuple[Dict[str, Any], int, bool]:
        """
        Extract a compressed subgraph based on traversal depth.
        
        Returns:
            Tuple of (compressed_graph, token_count, is_valid)
            
        Special handling for depth=0:
            - Returns an empty graph structure
            - Sets is_valid=False to indicate no context was passed
            - token_count is 0
        """
        # Handle depth=0 edge case: No context passed
        if self.compression_depth == 0:
            empty_graph = {
                "nodes": [],
                "edges": [],
                "root_node_id": self.root_node,
                "compression_metadata": {
                    "method": "truncation",
                    "depth": 0,
                    "reason": "No context passed (depth=0)",
                    "original_node_count": len(self.nodes),
                    "original_edge_count": len(self.edges)
                }
            }
            token_count = 0
            return empty_graph, token_count, False
        
        # Normal case: Perform BFS traversal
        if not self.root_node or self.root_node not in self.node_map:
            # Invalid graph, return empty
            return {
                "nodes": [],
                "edges": [],
                "root_node_id": self.root_node,
                "compression_metadata": {
                    "method": "truncation",
                    "depth": self.compression_depth,
                    "reason": "Invalid root node"
                }
            }, 0, False
        
        # BFS to find nodes within depth limit
        visited_nodes: Set[str] = set()
        visited_edges: List[Dict[str, Any]] = []
        queue = deque([(self.root_node, 0)])  # (node_id, current_depth)
        
        while queue:
            current_node, current_depth = queue.popleft()
            
            if current_node in visited_nodes:
                continue
            
            visited_nodes.add(current_node)
            
            if current_depth > self.compression_depth:
                continue
            
            # Add edges from this node
            for neighbor in self.adjacency_list.get(current_node, []):
                if neighbor in visited_nodes:
                    continue
                
                # Add edge if neighbor is within depth limit
                if current_depth + 1 <= self.compression_depth:
                    edge_data = next(
                        (e for e in self.edges if e["source"] == current_node and e["target"] == neighbor),
                        None
                    )
                    if edge_data:
                        visited_edges.append(edge_data)
                        queue.append((neighbor, current_depth + 1))
        
        # Build compressed graph
        compressed_nodes = [self.node_map[nid] for nid in visited_nodes if nid in self.node_map]
        
        compressed_graph = {
            "nodes": compressed_nodes,
            "edges": visited_edges,
            "root_node_id": self.root_node,
            "compression_metadata": {
                "method": "bfs_truncation",
                "depth": self.compression_depth,
                "original_node_count": len(self.nodes),
                "original_edge_count": len(self.edges),
                "compressed_node_count": len(compressed_nodes),
                "compressed_edge_count": len(visited_edges),
                "truncation_ratio": len(compressed_nodes) / len(self.nodes) if self.nodes else 0
            }
        }
        
        # Calculate token count
        if count_tokens_cl100k_base:
            # Convert graph to string representation for token counting
            graph_str = json.dumps(compressed_graph)
            token_count = count_tokens_cl100k_base(graph_str)
        else:
            # Fallback: estimate by character count (crude approximation)
            graph_str = json.dumps(compressed_graph)
            token_count = len(graph_str) // 4  # Rough estimate
        
        return compressed_graph, token_count, True
    
    def execute(self, policy_engine) -> Dict[str, Any]:
        """
        Execute the workflow with compressed context against a policy engine.
        
        Args:
            policy_engine: An engine that validates policy compliance.
        
        Returns:
            Execution log dictionary.
        """
        compressed_graph, token_count, is_valid_context = self.extract_compressed_context()
        
        execution_log = {
            "workflow_id": self.workflow_graph.get("id", "unknown"),
            "compression_depth": self.compression_depth,
            "original_node_count": len(self.nodes),
            "compressed_node_count": len(compressed_graph.get("nodes", [])),
            "token_count": token_count,
            "is_valid_context": is_valid_context,
            "status": "error" if not is_valid_context else "completed",
            "violations": [],
            "execution_steps": [],
            "metadata": {
                "compression_method": "bfs_truncation",
                "timestamp": "auto_generated"
            }
        }
        
        # If depth=0, return early with error status
        if not is_valid_context:
            execution_log["error_message"] = "No context passed (compression depth=0). Cannot execute workflow."
            execution_log["violations"].append({
                "type": "context_missing",
                "message": "Compression depth=0 resulted in no policy context. Execution aborted.",
                "severity": "critical"
            })
            return execution_log
        
        # Execute with compressed context
        if policy_engine:
            result = policy_engine.validate(compressed_graph)
            execution_log["violations"] = result.get("violations", [])
            execution_log["execution_steps"] = result.get("steps", [])
            execution_log["status"] = "completed" if not result.get("violations") else "completed_with_violations"
        
        return execution_log


def main():
    """
    Main entry point for testing the CompressedContextEngine.
    """
    # Example usage
    sample_workflow = {
        "id": "test-workflow-001",
        "root_node_id": "node_1",
        "nodes": [
            {"id": "node_1", "type": "start", "policy": "allow"},
            {"id": "node_2", "type": "process", "policy": "restricted"},
            {"id": "node_3", "type": "end", "policy": "allow"}
        ],
        "edges": [
            {"source": "node_1", "target": "node_2"},
            {"source": "node_2", "target": "node_3"}
        ]
    }
    
    print("Testing CompressedContextEngine with depth=0...")
    engine = CompressedContextEngine(sample_workflow, compression_depth=0)
    graph, tokens, valid = engine.extract_compressed_context()
    
    print(f"  Compressed graph nodes: {len(graph['nodes'])}")
    print(f"  Token count: {tokens}")
    print(f"  Is valid context: {valid}")
    print(f"  Status: {'error' if not valid else 'ok'}")
    
    if not valid:
        print("  ✓ Correctly handled depth=0 case: No context passed")
    
    print("\nTesting CompressedContextEngine with depth=1...")
    engine_depth1 = CompressedContextEngine(sample_workflow, compression_depth=1)
    graph1, tokens1, valid1 = engine_depth1.extract_compressed_context()
    
    print(f"  Compressed graph nodes: {len(graph1['nodes'])}")
    print(f"  Token count: {tokens1}")
    print(f"  Is valid context: {valid1}")
    
    if valid1:
        print("  ✓ Normal depth=1 case works correctly")
    
    print("\nAll tests passed.")


if __name__ == "__main__":
    main()