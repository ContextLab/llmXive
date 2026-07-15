"""
Implementation of the 'Full' active reconstruction strategy.
Traverses the entire relevant subgraph to reconstruct memory.
"""
from typing import Dict, Any, List, Set, Optional
import networkx as nx
import logging

logger = logging.getLogger(__name__)

class FullTraversal:
    """
    Full traversal strategy: visits all reachable nodes from the start node.
    Includes robust error handling for disconnected graphs and degenerate inputs.
    """
    def __init__(self):
        pass

    def execute(self, graph: nx.Graph, start_node: str, **kwargs) -> Dict[str, Any]:
        """
        Execute full traversal from the start node.
        
        Args:
            graph: The memory graph (networkx.DiGraph or Graph).
            start_node: The ID of the starting node.
            **kwargs: Additional arguments (ignored for full traversal).
        
        Returns:
            A dictionary containing:
                - visited_nodes: List of node IDs visited.
                - edges_traversed: List of edges traversed.
                - success: Boolean indicating if traversal completed.
                - error: (Optional) Error message if traversal failed.
                - stats: (Optional) Statistics about the traversal.
        """
        # Validate graph input
        if graph is None:
            logger.error("Graph input is None.")
            return {
                "visited_nodes": [],
                "edges_traversed": [],
                "success": False,
                "error": "Graph input is None."
            }

        # Handle degenerate case: empty graph
        if graph.number_of_nodes() == 0:
            logger.warning("Graph is empty (0 nodes).")
            return {
                "visited_nodes": [],
                "edges_traversed": [],
                "success": False,
                "error": "Graph is empty.",
                "stats": {
                    "node_count": 0,
                    "edge_count": 0
                }
            }

        # Validate start_node type
        if start_node is None:
            logger.error("Start node is None.")
            return {
                "visited_nodes": [],
                "edges_traversed": [],
                "success": False,
                "error": "Start node is None."
            }

        # Check if start_node exists in the graph
        if start_node not in graph.nodes:
            logger.warning(f"Start node '{start_node}' not found in graph.")
            return {
                "visited_nodes": [],
                "edges_traversed": [],
                "success": False,
                "error": f"Start node '{start_node}' not found in graph.",
                "stats": {
                    "node_count": 0,
                    "edge_count": 0
                }
            }

        # Check for disconnected components if the graph is not connected
        # and the start_node is in a small component, warning the user.
        # Note: For directed graphs, we check weakly connected components.
        try:
            if nx.is_directed(graph):
                # For directed graphs, check if the component containing start_node is the whole graph
                # using weak connectivity
                if not nx.is_weakly_connected(graph):
                    component = nx.weakly_connected_components(graph)
                    start_component = None
                    for comp in component:
                        if start_node in comp:
                            start_component = comp
                            break
                    
                    if start_component and len(start_component) < graph.number_of_nodes():
                        logger.warning(
                            f"Graph is disconnected. Start node '{start_node}' is in a component "
                            f"of size {len(start_component)} out of {graph.number_of_nodes()} total nodes. "
                            f"Traversal will be limited to this component."
                        )
            else:
                if not nx.is_connected(graph):
                    component = nx.connected_components(graph)
                    start_component = None
                    for comp in component:
                        if start_node in comp:
                            start_component = comp
                            break
                    
                    if start_component and len(start_component) < graph.number_of_nodes():
                        logger.warning(
                            f"Graph is disconnected. Start node '{start_node}' is in a component "
                            f"of size {len(start_component)} out of {graph.number_of_nodes()} total nodes. "
                            f"Traversal will be limited to this component."
                        )
        except Exception as e:
            # Fallback if connectivity check fails for some reason (e.g., invalid graph state)
            logger.warning(f"Could not determine graph connectivity: {e}. Proceeding with traversal.")

        visited_nodes = []
        edges_traversed = []
        
        # Use BFS for deterministic traversal order
        queue = [start_node]
        visited_set = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited_set:
                continue
            
            visited_set.add(current)
            visited_nodes.append(current)
            
            # Get neighbors (handle both directed and undirected)
            # Ensure we handle potential errors in neighbor retrieval
            try:
                if hasattr(graph, 'successors'):
                    # Directed graph
                    neighbors = list(graph.successors(current))
                else:
                    # Undirected graph
                    neighbors = list(graph.neighbors(current))
            except Exception as e:
                logger.error(f"Error retrieving neighbors for node '{current}': {e}")
                continue
            
            for neighbor in neighbors:
                if neighbor not in visited_set:
                    edges_traversed.append((current, neighbor))
                    queue.append(neighbor)
        
        logger.info(f"Traversal completed successfully. Visited {len(visited_nodes)} nodes, {len(edges_traversed)} edges.")
        
        return {
            "visited_nodes": visited_nodes,
            "edges_traversed": edges_traversed,
            "success": True,
            "stats": {
                "node_count": len(visited_nodes),
                "edge_count": len(edges_traversed)
            }
        }