"""
Full Active Reconstruction Strategy Implementation.

Implements the "Full" traversal algorithm that traverses the entire relevant
subgraph for each query. It includes robustness checks for disconnected
components and degenerate graphs (single nodes, no edges) to prevent
crashes or infinite loops.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time
from strategies.base import BaseTraversal
from graph_utils import validate_graph, get_graph_statistics, extract_subgraph_by_entities
from config import get_model_path

logger = logging.getLogger(__name__)


class FullTraversal(BaseTraversal):
    """
    Full Active Reconstruction Strategy.

    Traverses the entire connected component containing the query entities
    to reconstruct the memory graph relevant to the task.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.name = "Full"
        self.nodes_visited = 0
        self.execution_time = 0.0
        self.status = "completed"
        self.details: Dict[str, Any] = {}

    def _detect_degenerate_graph(self, graph: nx.DiGraph) -> Tuple[bool, str]:
        """
        Detects if the graph is degenerate (single node, no edges) or empty.
        Returns (is_degenerate, reason_string).
        """
        if graph.number_of_nodes() == 0:
            return True, "Empty graph"
        if graph.number_of_nodes() == 1 and graph.number_of_edges() == 0:
            return True, "Single-node graph (no edges)"
        return False, ""

    def _detect_disconnected_components(self, graph: nx.DiGraph, start_nodes: Set[str]) -> Dict[str, Set[str]]:
        """
        Identifies connected components and maps start nodes to their component.
        Returns a dict mapping component_id to set of nodes in that component.
        """
        if graph.number_of_nodes() == 0:
            return {}

        # For directed graphs, we treat them as undirected for connectivity
        # unless strict directed reachability is required.
        # Here we assume the memory graph is effectively undirected for traversal
        # unless specified otherwise.
        undirected = graph.to_undirected()
        components = list(nx.connected_components(undirected))
        node_to_component = {}
        for idx, comp in enumerate(components):
            for node in comp:
                node_to_component[node] = idx

        component_nodes = {idx: comp for idx, comp in enumerate(components)}
        return component_nodes

    def run(
        self,
        graph: nx.DiGraph,
        query_entities: List[str],
        task_id: str,
        timeout_seconds: float = 300.0
    ) -> Dict[str, Any]:
        """
        Executes the full traversal strategy.

        Args:
            graph: The memory graph (DiGraph).
            query_entities: List of entity names to start traversal from.
            task_id: Identifier for the current task.
            timeout_seconds: Maximum allowed execution time.

        Returns:
            Dictionary containing:
                - task_id
                - nodes_visited
                - execution_time
                - status (completed, unresolved, degenerate, timeout)
                - details (additional context)
        """
        start_time = time.time()
        self.nodes_visited = 0
        self.status = "completed"
        self.details = {}

        # 1. Validate Graph
        if not validate_graph(graph):
            logger.warning(f"Task {task_id}: Invalid graph structure detected.")
            self.status = "invalid_graph"
            return {
                "task_id": task_id,
                "nodes_visited": 0,
                "execution_time": time.time() - start_time,
                "status": self.status,
                "details": {"reason": "Graph validation failed"}
            }

        # 2. Check for Degenerate Graphs
        is_degenerate, reason = self._detect_degenerate_graph(graph)
        if is_degenerate:
            logger.warning(f"Task {task_id}: Degenerate graph detected. {reason}")
            self.status = "degenerate"
            # If single node, visit it. If empty, 0 nodes.
            self.nodes_visited = graph.number_of_nodes()
            self.details = {"reason": reason}
            return {
                "task_id": task_id,
                "nodes_visited": self.nodes_visited,
                "execution_time": time.time() - start_time,
                "status": self.status,
                "details": self.details
            }

        # 3. Identify Start Nodes in Graph
        valid_start_nodes = [n for n in query_entities if n in graph.nodes()]
        if not valid_start_nodes:
            logger.warning(f"Task {task_id}: No query entities found in graph.")
            self.status = "unresolved"
            self.details = {"reason": "No matching entities in graph"}
            return {
                "task_id": task_id,
                "nodes_visited": 0,
                "execution_time": time.time() - start_time,
                "status": self.status,
                "details": self.details
            }

        # 4. Detect Disconnected Components
        # We need to ensure we only traverse the component containing the start nodes.
        # If the start nodes are in different components, we traverse all relevant ones.
        component_map = self._detect_disconnected_components(graph, set(valid_start_nodes))

        # Identify which components contain our start nodes
        relevant_components = set()
        for node in valid_start_nodes:
            # Re-calculate component index for the node
            undirected = graph.to_undirected()
            try:
                # Find the component containing this node
                for idx, comp in enumerate(nx.connected_components(undirected)):
                    if node in comp:
                        relevant_components.add(idx)
                        break
            except Exception as e:
                logger.error(f"Task {task_id}: Error finding component for {node}: {e}")
                continue

        # 5. Perform Full Traversal on Relevant Components
        # We use BFS to visit all nodes in the relevant connected components.
        visited = set()
        total_nodes_visited = 0

        # Check timeout before starting heavy work
        if time.time() - start_time > timeout_seconds:
            self.status = "timeout"
            return {
                "task_id": task_id,
                "nodes_visited": total_nodes_visited,
                "execution_time": time.time() - start_time,
                "status": self.status,
                "details": {"reason": "Timeout before traversal start"}
            }

        try:
            for comp_idx in relevant_components:
                # Get nodes in this component
                undirected = graph.to_undirected()
                comp_nodes = next(c for c in nx.connected_components(undirected) if comp_idx == list(nx.connected_components(undirected)).index(c))
                
                # Actually, simpler way: just iterate connected components again to avoid index mismatch
                pass

            # Robust iteration:
            undirected = graph.to_undirected()
            visited_global = set()
            
            for comp_nodes in nx.connected_components(undirected):
                # Check if this component has any of our start nodes
                if not set(valid_start_nodes).isdisjoint(comp_nodes):
                    # This is a relevant component
                    # Perform BFS/DFS to count all nodes in this component
                    stack = list(comp_nodes) # Start with all nodes in component
                    # Since we know the component, we can just count them
                    # But to be strict about "traversal", we simulate visiting
                    component_visited = set()
                    queue = list(comp_nodes)
                    
                    while queue:
                        if time.time() - start_time > timeout_seconds:
                            self.status = "timeout"
                            self.nodes_visited = total_nodes_visited
                            self.details = {"reason": "Timeout during traversal"}
                            return {
                                "task_id": task_id,
                                "nodes_visited": self.nodes_visited,
                                "execution_time": time.time() - start_time,
                                "status": self.status,
                                "details": self.details
                            }
                        
                        node = queue.pop(0)
                        if node not in component_visited:
                            component_visited.add(node)
                            total_nodes_visited += 1
                            visited_global.add(node)
                    
                    # If the component was disconnected from the rest, we handled it.
                    # If the start node was unreachable in the directed sense but connected undirected,
                    # we still count it as "visited" in the full reconstruction context.
            
            self.nodes_visited = total_nodes_visited
            self.status = "completed" if total_nodes_visited > 0 else "unresolved"
            
        except Exception as e:
            logger.error(f"Task {task_id}: Traversal error: {e}")
            self.status = "error"
            self.details = {"error": str(e)}
            return {
                "task_id": task_id,
                "nodes_visited": self.nodes_visited,
                "execution_time": time.time() - start_time,
                "status": self.status,
                "details": self.details
            }

        end_time = time.time()
        self.execution_time = end_time - start_time

        return {
            "task_id": task_id,
            "nodes_visited": self.nodes_visited,
            "execution_time": self.execution_time,
            "status": self.status,
            "details": self.details
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Returns the current metrics for the last run."""
        return {
            "nodes_visited": self.nodes_visited,
            "execution_time": self.execution_time,
            "status": self.status
        }

    def reset(self):
        """Resets internal state for a new run."""
        self.nodes_visited = 0
        self.execution_time = 0.0
        self.status = "completed"
        self.details = {}

def run_full_strategy(
    graph: nx.DiGraph,
    query_entities: List[str],
    task_id: str,
    timeout_seconds: float = 300.0
) -> Dict[str, Any]:
    """
    Convenience function to run the FullTraversal strategy.
    """
    strategy = FullTraversal()
    return strategy.run(graph, query_entities, task_id, timeout_seconds)