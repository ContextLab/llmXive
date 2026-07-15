import networkx as nx
import logging
from typing import Dict, Any, List, Set, Optional, Tuple

from graph_utils import validate_graph, get_graph_statistics

logger = logging.getLogger(__name__)


class LazyTraversal:
    """
    Lazy traversal heuristic: defer edge expansion until a confidence threshold
    is met. Handles 'unreachable target' cases by defaulting to full traversal
    or flagging the result as 'unresolved'.
    """

    def __init__(self, threshold: float = 0.7, max_depth: int = 10):
        """
        Args:
            threshold: Confidence threshold for edge expansion (0.0 to 1.0).
            max_depth: Maximum depth for traversal to prevent infinite loops.
        """
        self.threshold = threshold
        self.max_depth = max_depth

    def traverse(
        self,
        graph: nx.DiGraph,
        start_node: str,
        target_node: str,
        task_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform lazy traversal from start_node to target_node.

        Returns a dictionary containing:
            - path: List of nodes in the found path (or empty if none found)
            - nodes_visited: Count of unique nodes visited
            - success: Boolean indicating if target was reached
            - reason: String explaining failure if success is False
            - strategy: 'lazy' or 'full_fallback'
        """
        if not validate_graph(graph):
            logger.warning("Invalid graph provided to LazyTraversal")
            return {
                "path": [],
                "nodes_visited": 0,
                "success": False,
                "reason": "Invalid graph structure",
                "strategy": "lazy",
            }

        if start_node not in graph:
            logger.warning(f"Start node {start_node} not in graph")
            return {
                "path": [],
                "nodes_visited": 0,
                "success": False,
                "reason": "Start node not in graph",
                "strategy": "lazy",
            }

        if target_node not in graph:
            logger.warning(f"Target node {target_node} not in graph")
            return {
                "path": [],
                "nodes_visited": 0,
                "success": False,
                "reason": "Target node not in graph",
                "strategy": "lazy",
            }

        # Attempt lazy traversal
        result = self._lazy_search(graph, start_node, target_node)

        # If target is unreachable via lazy strategy, default to full traversal
        if not result["success"]:
            logger.info(
                f"Target {target_node} unreachable via lazy strategy. "
                f"Reason: {result['reason']}. Switching to full traversal."
            )
            full_result = self._full_fallback(graph, start_node, target_node)
            full_result["strategy"] = "full_fallback"
            return full_result

        return result

    def _lazy_search(
        self, graph: nx.DiGraph, start_node: str, target_node: str
    ) -> Dict[str, Any]:
        """
        Perform the actual lazy search. Defer expansion if edge confidence < threshold.
        """
        visited: Set[str] = set()
        queue: List[Tuple[str, List[str], float]] = [(start_node, [start_node], 1.0)]
        nodes_visited = 0

        while queue:
            current, path, confidence = queue.pop(0)
            nodes_visited += 1

            if current == target_node:
                return {
                    "path": path,
                    "nodes_visited": nodes_visited,
                    "success": True,
                    "reason": "Target reached",
                    "strategy": "lazy",
                }

            if len(path) > self.max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            # Get neighbors and their edge weights (confidence)
            neighbors = list(graph.successors(current))
            if not neighbors:
                continue

            # Filter neighbors based on threshold
            # Assume edge attribute 'weight' or 'confidence' exists.
            # If not, treat as 0.0 (fail threshold)
            valid_neighbors = []
            for neighbor in neighbors:
                edge_data = graph[current][neighbor]
                # Try to get confidence/weight, default to 0.0
                conf = edge_data.get("confidence", edge_data.get("weight", 0.0))
                if conf >= self.threshold:
                    valid_neighbors.append((neighbor, conf))

            if not valid_neighbors:
                # No valid neighbors meet threshold
                continue

            # Sort by confidence descending (greedy within lazy)
            valid_neighbors.sort(key=lambda x: x[1], reverse=True)

            for neighbor, conf in valid_neighbors:
                new_path = path + [neighbor]
                new_conf = min(confidence, conf)
                queue.append((neighbor, new_path, new_conf))

        return {
            "path": [],
            "nodes_visited": nodes_visited,
            "success": False,
            "reason": "Target unreachable within threshold constraints",
            "strategy": "lazy",
        }

    def _full_fallback(
        self, graph: nx.DiGraph, start_node: str, target_node: str
    ) -> Dict[str, Any]:
        """
        Fallback to full traversal (BFS) if lazy search fails to reach target.
        This ensures we don't return 'unresolved' if a path exists but was
        filtered by the threshold.
        """
        try:
            # Use NetworkX shortest_path for full traversal logic
            # This ignores weights/thresholds and finds ANY path
            path = nx.shortest_path(graph, source=start_node, target=target_node)
            return {
                "path": path,
                "nodes_visited": len(set(path)),
                "success": True,
                "reason": "Target reached via full fallback",
                "strategy": "full_fallback",
            }
        except nx.NetworkXNoPath:
            # Truly unreachable
            logger.warning(
                f"Target {target_node} is truly unreachable from {start_node} "
                "even with full traversal."
            )
            return {
                "path": [],
                "nodes_visited": 0,
                "success": False,
                "reason": "Unreachable: No path exists in graph",
                "strategy": "full_fallback",
            }


def run_sensitivity_analysis(
    graph: nx.DiGraph,
    start_node: str,
    target_node: str,
    thresholds: List[float],
) -> List[Dict[str, Any]]:
    """
    Run lazy traversal with multiple thresholds to analyze sensitivity.

    Args:
        graph: The memory graph.
        start_node: Starting node.
        target_node: Target node.
        thresholds: List of threshold values to test.

    Returns:
        List of results dictionaries for each threshold.
    """
    results = []
    for thresh in thresholds:
        strategy = LazyTraversal(threshold=thresh)
        res = strategy.traverse(graph, start_node, target_node)
        res["threshold_used"] = thresh
        results.append(res)
    return results


def main():
    """
    Main entry point for lazy strategy testing (e.g., from CLI).
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Lazy Traversal Strategy - Main Entry Point")

    # Example usage (placeholder for actual integration)
    G = nx.DiGraph()
    G.add_edge("A", "B", confidence=0.9)
    G.add_edge("B", "C", confidence=0.5)
    G.add_edge("A", "C", confidence=0.8)

    strategy = LazyTraversal(threshold=0.7)
    result = strategy.traverse(G, "A", "C")
    logger.info(f"Result: {result}")


if __name__ == "__main__":
    main()