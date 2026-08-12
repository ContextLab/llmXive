from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time
from strategies.base import BaseTraversal
from graph_utils import validate_graph, get_graph_statistics

logger = logging.getLogger(__name__)

class GreedyTraversal(BaseTraversal):
    """
    Greedy traversal strategy that selects only the top-k confidence edges.
    Implements disconnected graph handling as per T044.
    """
    
    def __init__(self, top_k: int = 3, confidence_threshold: float = 0.0):
        super().__init__()
        self.top_k = top_k
        self.confidence_threshold = confidence_threshold
        self.nodes_visited = 0
        self.selection_log: List[Dict[str, Any]] = []

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
            component = nx.weakly_connected_component(graph, start_node)
            return set(component)
        except Exception as e:
            logger.warning(f"Error getting reachable component: {e}")
            return {start_node}

    def traverse(self, graph: nx.DiGraph, start_node: str, target_node: str,
                context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform greedy traversal with disconnected graph handling.
        
        Returns:
            Tuple of (success: bool, result: Dict)
        """
        self.nodes_visited = 0
        self.selection_log = []
        
        # Validate graph first
        is_valid, validation_msg = validate_graph(graph)
        if not is_valid:
            logger.warning(f"Invalid graph for greedy traversal: {validation_msg}")
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
                    "top_k": self.top_k
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

        # Normal greedy traversal logic
        visited: Set[str] = set()
        queue: List[Tuple[str, float]] = [(start_node, 1.0)]  # (node, confidence)
        path: List[str] = [start_node]
        
        iteration = 0
        found = False
        
        while queue and iteration < 1000:
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
                
                # Filter by confidence threshold
                if edge_confidence >= self.confidence_threshold:
                    neighbor_scores.append((neighbor, edge_confidence))
            
            # Sort by confidence and take top_k
            neighbor_scores.sort(key=lambda x: x[1], reverse=True)
            top_neighbors = neighbor_scores[:self.top_k]
            
            # Log selection for this step
            self.selection_log.append({
                "node": current,
                "total_neighbors": len(neighbors),
                "above_threshold": len(neighbor_scores),
                "selected": len(top_neighbors),
                "top_k": self.top_k
            })
            
            # Add top neighbors to queue
            for neighbor, conf in top_neighbors:
                if neighbor not in visited:
                    new_confidence = min(confidence * conf, 1.0)
                    queue.append((neighbor, new_confidence))
            
            # Early termination if queue is empty
            if not queue:
                break

        status = "success" if found else "unresolved"
        result = {
            "status": status,
            "nodes_visited": self.nodes_visited,
            "top_k": self.top_k,
            "confidence_threshold": self.confidence_threshold,
            "path_length": len(path) if found else 0
        }
        
        if not found:
            result["reason"] = "Target not found with greedy selection"
        
        return found, result

def run_greedy_strategy(graph: nx.DiGraph, start_node: str, target_node: str,
                       top_k: int = 3, confidence_threshold: float = 0.0) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to run greedy traversal with default settings.
    """
    traverser = GreedyTraversal(top_k=top_k, confidence_threshold=confidence_threshold)
    return traverser.traverse(graph, start_node, target_node, {})