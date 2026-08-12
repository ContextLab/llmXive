from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time
from strategies.base import BaseTraversal
from graph_utils import validate_graph, get_graph_statistics

logger = logging.getLogger(__name__)

class LazyTraversal(BaseTraversal):
    """
    Lazy traversal strategy that defers edge expansion until an evidence threshold is triggered.
    Implements disconnected graph handling as per T044.
    """
    
    def __init__(self, evidence_threshold: float = 0.7, max_iterations: int = 1000):
        super().__init__()
        self.evidence_threshold = evidence_threshold
        self.max_iterations = max_iterations
        self.nodes_visited = 0
        self.evidence_log: List[Dict[str, Any]] = []

    def _is_connected_component(self, graph: nx.DiGraph, start_node: str, target_node: str) -> bool:
        """
        Check if target_node is reachable from start_node within the same connected component.
        For directed graphs, we check weak connectivity first, then reachability.
        """
        if not graph.has_node(start_node) or not graph.has_node(target_node):
            return False
        
        # Check if they are in the same weakly connected component
        try:
            components = list(nx.weakly_connected_components(graph))
            start_comp = None
            target_comp = None
            
            for comp in components:
                if start_node in comp:
                    start_comp = comp
                if target_node in comp:
                    target_comp = comp
            
            if start_comp is None or target_comp is None:
                return False
            
            return start_comp == target_comp
        except Exception as e:
            logger.warning(f"Error checking connectivity: {e}")
            return False

    def _get_reachable_component(self, graph: nx.DiGraph, start_node: str) -> Set[str]:
        """
        Get all nodes reachable from start_node in the connected component.
        """
        if start_node not in graph:
            return set()
        
        try:
            # Use nx.weakly_connected_component to get the component
            # Then filter to only nodes reachable from start_node
            component = nx.weakly_connected_component(graph, start_node)
            return set(component)
        except Exception as e:
            logger.warning(f"Error getting reachable component: {e}")
            return {start_node}

    def traverse(self, graph: nx.DiGraph, start_node: str, target_node: str, 
                context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform lazy traversal with disconnected graph handling.
        
        Returns:
            Tuple of (success: bool, result: Dict)
        """
        self.nodes_visited = 0
        self.evidence_log = []
        
        # Validate graph first
        is_valid, validation_msg = validate_graph(graph)
        if not is_valid:
            logger.warning(f"Invalid graph for lazy traversal: {validation_msg}")
            return False, {
                "status": "degenerate",
                "nodes_visited": 0,
                "reason": validation_msg
            }
        
        # Check for degenerate cases
        if len(graph.nodes()) == 0:
            return False, {
                "status": "degenerate",
                "nodes_visited": 0,
                "reason": "Empty graph"
            }
        
        if len(graph.nodes()) == 1:
            if start_node == target_node:
                self.nodes_visited = 1
                return True, {
                    "status": "success",
                    "nodes_visited": 1,
                    "evidence_threshold": self.evidence_threshold
                }
            else:
                return False, {
                    "status": "degenerate",
                    "nodes_visited": 1,
                    "reason": "Single node graph, target not found"
                }

        # T044: Check if target is reachable from start
        if not self._is_connected_component(graph, start_node, target_node):
            logger.info(f"Target node '{target_node}' is unreachable from '{start_node}'. "
                      f"Defaulting to full traversal of connected component.")
            
            # Get the connected component containing start_node
            reachable_nodes = self._get_reachable_component(graph, start_node)
            
            # Perform full traversal of the reachable component
            visited = set()
            queue = [start_node]
            component_visited = 0
            
            while queue and component_visited < len(reachable_nodes):
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                component_visited += 1
                self.nodes_visited += 1
                
                # Add neighbors to queue
                if graph.has_node(current):
                    for neighbor in graph.successors(current):
                        if neighbor not in visited:
                            queue.append(neighbor)
                
                # Also check predecessors for undirected-like traversal in weak component
                for neighbor in graph.predecessors(current):
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            return False, {
                "status": "unresolved",
                "nodes_visited": component_visited,
                "reason": f"Target unreachable in component. Traversed {component_visited} nodes in connected component.",
                "component_size": len(reachable_nodes)
            }

        # Normal lazy traversal logic
        visited: Set[str] = set()
        queue: List[Tuple[str, float]] = [(start_node, 1.0)]  # (node, confidence)
        path: List[str] = [start_node]
        
        iteration = 0
        found = False
        
        while queue and iteration < self.max_iterations:
            iteration += 1
            current, confidence = queue.pop(0)
            
            if current in visited:
                continue
            
            visited.add(current)
            self.nodes_visited += 1
            
            # Check if we found the target
            if current == target_node:
                found = True
                break
            
            # Get neighbors and their edge weights/confidence
            neighbors = list(graph.successors(current))
            
            # Sort by confidence (edge weight) descending
            neighbor_scores = []
            for neighbor in neighbors:
                edge_data = graph.get_edge_data(current, neighbor, {})
                # Use edge weight as confidence, default to 0.5 if not present
                edge_confidence = edge_data.get('weight', edge_data.get('confidence', 0.5))
                neighbor_scores.append((neighbor, edge_confidence))
            
            # Only expand edges above threshold
            valid_neighbors = [(n, c) for n, c in neighbor_scores if c >= self.evidence_threshold]
            
            # Log evidence for this step
            self.evidence_log.append({
                "node": current,
                "neighbors_explored": len(neighbor_scores),
                "neighbors_above_threshold": len(valid_neighbors),
                "threshold": self.evidence_threshold
            })
            
            # Add valid neighbors to queue
            for neighbor, conf in sorted(valid_neighbors, key=lambda x: x[1], reverse=True):
                if neighbor not in visited:
                    new_confidence = min(confidence * conf, 1.0)
                    queue.append((neighbor, new_confidence))
            
            # Early termination if confidence drops too low
            if queue and queue[0][1] < self.evidence_threshold * 0.5:
                logger.info(f"Confidence dropped below threshold ({queue[0][1]:.2f} < {self.evidence_threshold * 0.5:.2f})")
                break

        status = "success" if found else "unresolved"
        result = {
            "status": status,
            "nodes_visited": self.nodes_visited,
            "evidence_threshold": self.evidence_threshold,
            "path_length": len(path) if found else 0
        }
        
        if not found:
            result["reason"] = "Target not found within evidence threshold constraints"
        
        return found, result

def run_sensitivity_analysis(graph: nx.DiGraph, start_node: str, target_node: str,
                            thresholds: List[float] = [0.3, 0.5, 0.7, 0.9]) -> Dict[float, Dict[str, Any]]:
    """
    Run lazy traversal with multiple evidence thresholds for sensitivity analysis.
    
    Args:
        graph: The memory graph to traverse
        start_node: Starting node
        target_node: Target node to reach
        thresholds: List of evidence thresholds to test
        
    Returns:
        Dictionary mapping threshold to results
    """
    results = {}
    
    for threshold in thresholds:
        traverser = LazyTraversal(evidence_threshold=threshold)
        success, result = traverser.traverse(graph, start_node, target_node, {})
        
        results[threshold] = {
            "success": success,
            "nodes_visited": result.get("nodes_visited", 0),
            "status": result.get("status", "unknown"),
            "reason": result.get("reason", "")
        }
        
        logger.info(f"Threshold {threshold}: {result.get('status', 'unknown')}, "
                   f"visited {result.get('nodes_visited', 0)} nodes")
    
    return results

def run_lazy_strategy(graph: nx.DiGraph, start_node: str, target_node: str,
                     evidence_threshold: float = 0.7) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to run lazy traversal with default settings.
    """
    traverser = LazyTraversal(evidence_threshold=evidence_threshold)
    return traverser.traverse(graph, start_node, target_node, {})