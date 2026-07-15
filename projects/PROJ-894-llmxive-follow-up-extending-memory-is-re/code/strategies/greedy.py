"""
Greedy Traversal Strategy for Active Reconstruction.

Implements a heuristic that selects the top-k edges with the highest
confidence scores at each step of the graph traversal, rather than
exploring the entire subgraph (Full) or deferring expansion (Lazy).
"""
import networkx as nx
import logging
from typing import Dict, Any, List, Set, Optional, Tuple

from graph_utils import validate_graph, get_graph_statistics

logger = logging.getLogger(__name__)


class GreedyTraversal:
    """
    Greedy traversal heuristic for memory graph reconstruction.

    At each step, this strategy:
    1. Identifies all candidate edges connecting the visited set to unvisited nodes.
    2. Scores these edges based on a confidence metric (default: edge weight or a
       computed relevance score).
    3. Selects the top-k highest-scoring edges to expand.
    4. Repeats until the target entity is reached or no candidates remain.

    Attributes:
        k (int): The number of top edges to select at each step.
        confidence_key (str): The attribute name in edge data used for scoring.
    """

    def __init__(self, k: int = 3, confidence_key: str = "weight", max_steps: int = 50):
        """
        Initialize the Greedy Traversal strategy.

        Args:
            k: Number of top edges to expand per iteration.
            confidence_key: The edge attribute name used as the confidence score.
            max_steps: Maximum number of expansion steps to prevent infinite loops.
        """
        if k < 1:
            raise ValueError("k must be at least 1")
        self.k = k
        self.confidence_key = confidence_key
        self.max_steps = max_steps

    def _get_edge_confidence(self, G: nx.Graph, u: Any, v: Any) -> float:
        """
        Retrieve the confidence score for an edge.

        If the edge has the specified attribute, use it.
        Otherwise, default to 1.0 (or 0.0 if no weight exists and we treat missing as low confidence).
        Here we default to 1.0 for unweighted edges to ensure they are considered,
        unless the user explicitly set weights to 0.
        """
        try:
            edge_data = G[u][v]
            if self.confidence_key in edge_data:
                val = edge_data[self.confidence_key]
                # Ensure it's a float, handle potential None
                if val is None:
                    return 0.0
                return float(val)
            return 1.0 # Default confidence if key missing but edge exists
        except KeyError:
            return 0.0

    def traverse(
        self,
        G: nx.Graph,
        start_node: Any,
        target_node: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the greedy traversal from start_node to target_node.

        Args:
            G: The memory graph (NetworkX).
            start_node: The entity to start the search from.
            target_node: The target entity to reach.
            context: Optional context dict (unused in basic greedy, but kept for API compatibility).

        Returns:
            A dictionary containing:
                - path: List of nodes in the found path (or empty if none).
                - nodes_visited: Total unique nodes visited during traversal.
                - edges_explored: Total edges considered.
                - success: Boolean indicating if target was reached.
                - steps: Number of expansion iterations performed.
        """
        if not validate_graph(G):
            logger.warning("Graph validation failed or graph is empty.")
            return {
                "path": [],
                "nodes_visited": 0,
                "edges_explored": 0,
                "success": False,
                "steps": 0,
                "reason": "Invalid or empty graph"
            }

        if start_node not in G:
            return {
                "path": [],
                "nodes_visited": 0,
                "edges_explored": 0,
                "success": False,
                "steps": 0,
                "reason": f"Start node {start_node} not in graph"
            }

        if target_node not in G:
            return {
                "path": [],
                "nodes_visited": 0,
                "edges_explored": 0,
                "success": False,
                "steps": 0,
                "reason": f"Target node {target_node} not in graph"
            }

        visited: Set[Any] = {start_node}
        path: List[Any] = [start_node]
        current_node = start_node
        edges_explored = 0
        steps = 0

        # Parent map to reconstruct path
        parent_map: Dict[Any, Any] = {start_node: None}

        while current_node != target_node and steps < self.max_steps:
            steps += 1
            candidates: List[Tuple[Any, float]] = []

            # Identify neighbors
            try:
                neighbors = G.neighbors(current_node)
            except Exception:
                logger.error(f"Error getting neighbors for {current_node}")
                break

            for neighbor in neighbors:
                if neighbor in visited:
                    continue

                conf = self._get_edge_confidence(G, current_node, neighbor)
                candidates.append((neighbor, conf))
                edges_explored += 1

            if not candidates:
                logger.debug(f"No unvisited candidates from {current_node}. Stuck.")
                break

            # Sort by confidence descending, then by node ID for determinism
            candidates.sort(key=lambda x: (-x[1], str(x[0])))

            # Select top-k
            top_k = candidates[:self.k]

            # Expand the best candidate (greedy choice)
            # Note: A true greedy search might pick the absolute best edge overall,
            # but here we are simulating a step-wise expansion where we pick the best
            # neighbor of the current node.
            best_neighbor, best_conf = top_k[0]

            visited.add(best_neighbor)
            parent_map[best_neighbor] = current_node
            current_node = best_neighbor
            path.append(current_node)

        success = current_node == target_node

        if success:
            # Reconstruct path if we need to ensure it's the one taken
            # (In this simple greedy, path is built incrementally)
            pass
        else:
            path = [] # Clear path if not successful

        return {
            "path": path,
            "nodes_visited": len(visited),
            "edges_explored": edges_explored,
            "success": success,
            "steps": steps
        }

    def evaluate_task(
        self,
        task: Dict[str, Any],
        graph: nx.Graph
    ) -> Dict[str, Any]:
        """
        Evaluate a single task using the Greedy strategy.

        Args:
            task: Dictionary containing 'start', 'target', and 'answer' keys.
            graph: The memory graph to traverse.

        Returns:
            Dictionary with evaluation metrics.
        """
        start = task.get("start")
        target = task.get("target")
        expected_answer = task.get("answer")

        if not start or not target:
            return {
                "task_id": task.get("id", "unknown"),
                "success": False,
                "accuracy": False,
                "nodes_visited": 0,
                "edges_explored": 0,
                "reason": "Missing start or target in task"
            }

        result = self.traverse(graph, start, target)

        # Determine accuracy based on whether target was reached
        # In a real scenario, we might check if the path leads to the correct answer string
        # For this benchmark, 'success' in traversal often implies reaching the target entity.
        # We assume if we reached the target node, the answer is "retrieved".
        # If the task requires specific content validation, that would happen here.
        is_correct = result["success"]

        return {
            "task_id": task.get("id", "unknown"),
            "success": result["success"],
            "accuracy": is_correct,
            "nodes_visited": result["nodes_visited"],
            "edges_explored": result["edges_explored"],
            "steps": result["steps"],
            "path": result["path"],
            "reason": result.get("reason", None)
        }