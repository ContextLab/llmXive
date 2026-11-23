"""
Greedy Traversal Strategy for Memory Graph Reconstruction.

This module implements the "Greedy" traversal heuristic for the active
reconstruction of memory graphs. The strategy prioritizes visiting nodes
that have the highest estimated relevance or connectivity score towards
the target, aiming to minimize the number of nodes visited while maximizing
the probability of finding the correct evidence.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time

from strategies.base import BaseTraversal
from graph_utils import validate_graph, get_graph_statistics, check_graph_connectivity

logger = logging.getLogger(__name__)


class GreedyTraversal(BaseTraversal):
    """
    A greedy traversal strategy that selects the next node to visit
    based on a heuristic score (e.g., edge weight, centrality, or relevance).

    The greedy approach makes the locally optimal choice at each step,
    attempting to reach the target node with the fewest hops or highest
    confidence path.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the GreedyTraversal strategy.

        Args:
            config: Configuration dictionary. Expected keys:
                    - 'score_key': The attribute name in nodes/edges to use for scoring (default: 'weight').
                    - 'max_visits': Maximum number of nodes to visit before giving up (default: 100).
                    - 'threshold': Minimum confidence threshold to accept a node as evidence (default: 0.5).
        """
        super().__init__(config)
        self.score_key = config.get('score_key', 'weight') if config else 'weight'
        self.max_visits = config.get('max_visits', 100) if config else 100
        self.threshold = config.get('threshold', 0.5) if config else 0.5

    def _calculate_node_score(self, graph: nx.DiGraph, current_node: str, target_node: str) -> float:
        """
        Calculate a heuristic score for a neighbor node.

        The score is based on the edge weight to the neighbor. If weights are not
        present, it defaults to 1.0 (unweighted). In a more advanced implementation,
        this could incorporate centrality measures or semantic similarity.

        Args:
            graph: The memory graph.
            current_node: The current node being traversed.
            target_node: The target node we are trying to reach.

        Returns:
            A float score representing the desirability of the neighbor.
        """
        # For a simple greedy approach, we look at the direct edge weight to the neighbor.
        # If the graph is unweighted, we assume weight 1.0.
        # We could also look at the distance to target if pre-calculated, but that's expensive.
        # Here we prioritize neighbors with higher edge weights.
        # If we want to be more "greedy" towards the target, we might prioritize neighbors
        # that are closer to the target, but without a full BFS/Dijkstra pre-run,
        # we rely on edge weights as a proxy for relevance.

        # Note: In a true greedy shortest-path, we'd use Dijkstra. Here we simulate
        # a "greedy" selection based on available local information (edge weights).
        return 1.0  # Default score if no weight

    def traverse(self, graph: nx.DiGraph, start_node: str, target_node: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Execute the greedy traversal from start_node to target_node.

        Args:
            graph: The memory graph (networkx DiGraph).
            start_node: The starting node for traversal.
            target_node: The target node to find.

        Returns:
            A tuple containing:
                - path: List of node IDs visited in order.
                - stats: Dictionary containing traversal statistics (nodes_visited, etc.).
        """
        start_time = time.time()

        # Validate graph
        if not validate_graph(graph):
            logger.error("Invalid graph provided to GreedyTraversal.")
            return [], {"nodes_visited": 0, "status": "INVALID_GRAPH", "latency_ms": 0}

        # Check for degenerate cases
        if start_node not in graph or target_node not in graph:
            logger.warning(f"Start or target node not in graph. Start: {start_node}, Target: {target_node}")
            return [], {"nodes_visited": 0, "status": "NODE_NOT_FOUND", "latency_ms": 0}

        # Check connectivity (optional, but good for logging)
        is_connected = check_graph_connectivity(graph, start_node, target_node)
        if not is_connected:
            logger.warning(f"Target node {target_node} is unreachable from {start_node} in the current component.")
            # We still attempt traversal, but it will fail to find the target.
            # The strategy will exhaust reachable nodes.

        visited: Set[str] = set()
        path: List[str] = []
        queue: List[str] = [start_node]  # Using a list as a priority queue (sorted by score)

        # We will use a simple greedy selection: at each step, pick the neighbor
        # with the highest score. Since we don't have a global score, we score
        # the immediate neighbors of the current node.
        # To prevent infinite loops, we track visited nodes.

        current_node = start_node
        nodes_visited_count = 0

        while queue and nodes_visited_count < self.max_visits:
            # Sort queue by score (descending) - greedy choice
            # Since we are doing a simple greedy, we pick the best neighbor of the *current* node
            # and push it to the queue, but strictly speaking, greedy traversal usually
            # picks the best neighbor of the current node to move to next.
            # Let's implement a standard Greedy Best-First:
            # 1. Expand current node.
            # 2. Get neighbors.
            # 3. Score neighbors.
            # 4. Pick best unvisited neighbor.
            # 5. Move to best neighbor.

            if current_node == target_node:
                break

            neighbors = list(graph.successors(current_node))
            if not neighbors:
                # Dead end
                logger.debug(f"Dead end at {current_node}. No successors.")
                # If we have other candidates in queue (if we were doing a more complex search),
                # we would pop the best one. But for a pure greedy path, we just stop if dead end.
                # However, to be robust, let's assume we might have backtracking or multiple paths.
                # For this specific "Greedy" strategy, we assume we follow the highest weight edge.
                break

            # Calculate scores for neighbors
            neighbor_scores = []
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                # Simple heuristic: edge weight
                edge_data = graph[current_node][neighbor]
                score = edge_data.get(self.score_key, 1.0)
                neighbor_scores.append((neighbor, score))

            if not neighbor_scores:
                logger.debug(f"No unvisited neighbors for {current_node}.")
                break

            # Sort by score descending
            neighbor_scores.sort(key=lambda x: x[1], reverse=True)
            best_neighbor = neighbor_scores[0][0]

            # Move to best neighbor
            visited.add(current_node)
            path.append(current_node)
            nodes_visited_count += 1
            current_node = best_neighbor

            # If we reached the target
            if current_node == target_node:
                visited.add(current_node)
                path.append(current_node)
                nodes_visited_count += 1
                break

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        status = "SUCCESS" if current_node == target_node else "DEAD_END"
        if not is_connected and status == "DEAD_END":
            status = "UNREACHABLE"

        stats = {
            "nodes_visited": nodes_visited_count,
            "path_length": len(path),
            "status": status,
            "latency_ms": latency_ms,
            "threshold": self.threshold,
            "strategy": "Greedy"
        }

        return path, stats


def run_greedy_strategy(
    graph: nx.DiGraph,
    start_node: str,
    target_node: str,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Convenience function to run the GreedyTraversal strategy.

    Args:
        graph: The memory graph.
        start_node: The starting node.
        target_node: The target node.
        config: Configuration for the strategy.

    Returns:
        Tuple of (path, stats).
    """
    strategy = GreedyTraversal(config)
    return strategy.traverse(graph, start_node, target_node)
