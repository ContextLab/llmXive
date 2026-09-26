import logging
from typing import List, Optional
import networkx as nx
from environment.state_graph import StateGraph

logger = logging.getLogger(__name__)

def validate_graph(graph: StateGraph) -> bool:
    """
    Validate that a path exists from the start node to the goal node in the given StateGraph.

    This function constructs a directed NetworkX graph from the StateGraph's nodes and edges,
    then checks for the existence of a path from the start node to the goal node using
    networkx.has_path.

    Args:
        graph (StateGraph): The state graph to validate.

    Returns:
        bool: True if a path exists from start to goal.

    Raises:
        RuntimeError: If no path exists from start to goal.
        ValueError: If the graph is None or invalid structure.
    """
    if graph is None:
        logger.error("Validation failed: Input graph is None")
        raise ValueError("Input graph cannot be None")

    # Convert StateGraph to NetworkX DiGraph
    G = nx.DiGraph()

    # Add nodes
    for node in graph.nodes:
        G.add_node(node.id, tier=graph.tier, is_start=(node.id == graph.start), is_goal=(node.id == graph.goal))

    # Add edges with transition probabilities
    for edge in graph.edges:
        G.add_edge(edge.source_id, edge.target_id, probability=edge.probability)

    # Check if start and goal nodes exist in the graph
    if graph.start not in G:
        error_msg = f"Validation failed: Start node {graph.start} not found in graph"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    if graph.goal not in G:
        error_msg = f"Validation failed: Goal node {graph.goal} not found in graph"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Check for path existence using networkx.has_path
    if not nx.has_path(G, graph.start, graph.goal):
        error_msg = f"Validation failed: No path exists from start node {graph.start} to goal node {graph.goal}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Validation successful: Path exists from {graph.start} to {graph.goal} in tier {graph.tier}")
    return True