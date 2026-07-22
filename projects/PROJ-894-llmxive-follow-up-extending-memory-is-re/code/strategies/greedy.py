"""
Greedy Traversal Strategy: Selects top-k confidence edges at each step.
"""
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time

from strategies.base import BaseTraversal
from graph_utils import validate_graph, get_graph_statistics

logger = logging.getLogger(__name__)


class GreedyTraversal(BaseTraversal):
    """
    Greedy traversal heuristic that selects top-k confidence edges at each step.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.top_k = self.config.get("top_k", 3)

    def get_strategy_name(self) -> str:
        return "Greedy"

    def _validate_graph(self, graph: nx.DiGraph, start_node: str) -> bool:
        """Validate the graph structure."""
        if not validate_graph(graph):
            logger.error("Graph validation failed")
            return False

        if start_node not in graph.nodes:
            logger.error(f"Start node '{start_node}' not found in graph")
            return False

        return True

    def _get_edge_confidence(self, source: str, target: str, graph: nx.DiGraph) -> float:
        """
        Get confidence score for an edge.
        
        Args:
            source: Source node ID.
            target: Target node ID.
            graph: The graph containing the edge.
            
        Returns:
            Confidence score between 0 and 1.
        """
        edge_data = graph.edges[source, target]
        if "confidence" in edge_data:
            return edge_data["confidence"]
        # Placeholder: deterministic value based on node IDs
        return (hash((source, target)) % 100) / 100.0

    def traverse(
        self,
        graph: nx.DiGraph,
        start_node: str,
        target_node: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Traverse the graph using greedy selection of top-k edges.
        
        Args:
            graph: The memory graph to traverse.
            start_node: The starting node for traversal.
            target_node: Optional target node to reach.
            context: Optional context dictionary.
            
        Returns:
            A tuple of (success, path, stats).
        """
        start_time = self._start_timer()
        self.reset_stats()

        if not self._validate_graph(graph, start_node):
            return False, [], self.get_stats()

        visited = set()
        path = []
        current_node = start_node
        visited.add(current_node)

        logger.info(f"Starting greedy traversal from node: {start_node} (top_k={self.top_k})")

        while True:
            self._record_node_visit()
            path.append(current_node)

            # Check if we reached the target
            if target_node and current_node == target_node:
                logger.info(f"Target node {target_node} reached")
                break

            # Get all outgoing edges and their confidences
            neighbors = list(graph.successors(current_node))
            if not neighbors:
                logger.debug(f"No outgoing edges from {current_node}, stopping.")
                break

            # Score edges
            edge_scores = []
            for neighbor in neighbors:
                self._record_edge_traversal()
                confidence = self._get_edge_confidence(current_node, neighbor, graph)
                edge_scores.append((neighbor, confidence))
                self._record_inference(5.0)  # Placeholder inference time

            # Sort by confidence descending and pick top-k
            edge_scores.sort(key=lambda x: x[1], reverse=True)
            top_neighbors = [n for n, _ in edge_scores[:self.top_k]]

            # Choose the highest confidence neighbor not yet visited
            next_node = None
            for neighbor in top_neighbors:
                if neighbor not in visited:
                    next_node = neighbor
                    visited.add(neighbor)
                    break

            # If all top-k are visited, pick any unvisited neighbor
            if next_node is None:
                for neighbor in neighbors:
                    if neighbor not in visited:
                        next_node = neighbor
                        visited.add(neighbor)
                        break

            # If no unvisited neighbors, stop
            if next_node is None:
                logger.debug(f"No unvisited neighbors from {current_node}, stopping.")
                break

            current_node = next_node

        end_time = self._stop_timer(start_time)
        logger.info(
            f"Greedy traversal completed. Visited {self._stats['nodes_visited']} nodes "
            f"in {self._stats['total_execution_time_ms']:.2f}ms"
        )

        success = len(path) > 0
        return success, path, self.get_stats()

    def main():
        """Entry point for standalone execution (placeholder)."""
        logger.info("GreedyTraversal main entry point")