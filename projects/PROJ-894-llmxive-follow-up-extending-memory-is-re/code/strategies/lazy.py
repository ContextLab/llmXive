"""
Lazy Traversal Strategy Implementation.

This module implements the "Lazy" traversal heuristic that defers edge expansion
until an evidence threshold is triggered.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time
from strategies.base import BaseTraversal
from graph_utils import validate_graph, get_graph_statistics, check_graph_connectivity

logger = logging.getLogger(__name__)

class LazyTraversal(BaseTraversal):
    """
    Lazy traversal strategy that defers edge expansion until evidence threshold is met.
    """

    def __init__(self, threshold: float = 0.7):
        """
        Initialize LazyTraversal with a confidence threshold.

        Args:
            threshold: The confidence score threshold to trigger edge expansion.
        """
        self.threshold = threshold
        self.nodes_visited = 0
        self.start_time = None

    def traverse(self, graph: nx.DiGraph, start_node: str, target_node: str) -> Dict[str, Any]:
        """
        Perform lazy traversal from start_node to target_node.

        Args:
            graph: The memory graph to traverse.
            start_node: The starting node.
            target_node: The target node to reach.

        Returns:
            Dictionary containing traversal results.
        """
        self.start_time = time.time()
        self.nodes_visited = 0

        if not validate_graph(graph):
            logger.warning("Invalid graph provided for traversal.")
            return {
                'status': 'invalid_graph',
                'nodes_visited': 0,
                'latency_ms': 0,
                'path': []
            }

        if start_node not in graph.nodes() or target_node not in graph.nodes():
            logger.warning(f"Start or target node not in graph. Start: {start_node}, Target: {target_node}")
            return {
                'status': 'node_not_found',
                'nodes_visited': 0,
                'latency_ms': 0,
                'path': []
            }

        # Check connectivity first to handle disconnected graphs early
        is_connected, component_nodes = check_graph_connectivity(graph, start_node)
        if not is_connected and target_node not in component_nodes:
            logger.warning(f"Target node unreachable from start node in current component.")
            return {
                'status': 'unreachable',
                'nodes_visited': 0,
                'latency_ms': 0,
                'path': [],
                'degenerate_flag': 'disconnected'
            }

        # BFS with threshold check
        queue = [(start_node, [start_node])]
        visited = set()
        path = []

        while queue:
            current, current_path = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            self.nodes_visited += 1

            if current == target_node:
                path = current_path
                break

            # Check evidence threshold for neighbors
            for neighbor in graph.neighbors(current):
                if neighbor not in visited:
                    # In a real implementation, this would check edge weights/confidence
                    # For now, we simulate by checking if edge has a 'confidence' attribute
                    edge_data = graph.get_edge_data(current, neighbor)
                    confidence = edge_data.get('confidence', 1.0) if edge_data else 1.0

                    if confidence >= self.threshold:
                        queue.append((neighbor, current_path + [neighbor]))

        latency_ms = (time.time() - self.start_time) * 1000

        return {
            'status': 'success' if path else 'unreachable',
            'nodes_visited': self.nodes_visited,
            'latency_ms': latency_ms,
            'path': path,
            'threshold_used': self.threshold
        }

def run_lazy_strategy(task: Dict[str, Any], graph_data: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    """
    Run the lazy strategy on a given task and graph.

    Args:
        task: The task dictionary containing question, context, answer.
        graph_data: The graph data dictionary.
        threshold: The confidence threshold for edge expansion.

    Returns:
        Dictionary containing strategy execution results.
    """
    # Convert graph_data to networkx graph
    G = nx.DiGraph()
    edges = graph_data.get('edges', [])
    nodes = graph_data.get('nodes', [])

    # Add nodes
    for node in nodes:
        if isinstance(node, dict):
            G.add_node(node.get('id', node), **node.get('attributes', {}))
        else:
            G.add_node(node)

    # Add edges
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if source and target:
            G.add_edge(source, target, **{k: v for k, v in edge.items() if k not in ['source', 'target']})

    # Determine start and target nodes
    # Simplified: start from first node, target is answer
    start_node = list(G.nodes())[0] if G.nodes() else 'unknown'
    target_node = task.get('answer', 'target')

    # Run traversal
    strategy = LazyTraversal(threshold=threshold)
    result = strategy.traverse(G, start_node, target_node)

    # Add task metadata
    result['task_id'] = task.get('task_id', 'unknown')
    result['threshold'] = threshold

    return result

def run_sensitivity_analysis(graph_data: Dict[str, Any], tasks: List[Dict[str, Any]], thresholds: List[float]) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis across multiple thresholds.

    Args:
        graph_data: The graph data dictionary.
        tasks: List of task dictionaries.
        thresholds: List of threshold values to test.

    Returns:
        List of result dictionaries for each task and threshold combination.
    """
    all_results = []
    for threshold in thresholds:
        for task in tasks:
            result = run_lazy_strategy(task, graph_data, threshold)
            all_results.append(result)
    return all_results