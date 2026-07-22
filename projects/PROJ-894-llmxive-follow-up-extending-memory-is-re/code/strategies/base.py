"""
Base class for all graph traversal strategies.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time

logger = logging.getLogger(__name__)


class BaseTraversal(ABC):
    """
    Abstract base class defining the interface for memory graph traversal strategies.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the traversal strategy.

        Args:
            config: Optional dictionary of configuration parameters.
        """
        self.config = config or {}
        self._stats = {
            "nodes_visited": 0,
            "edges_traversed": 0,
            "inference_calls": 0,
            "total_inference_time_ms": 0.0,
            "total_execution_time_ms": 0.0,
        }

    @abstractmethod
    def traverse(
        self,
        graph: nx.DiGraph,
        start_node: str,
        target_node: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Execute the traversal strategy on the given graph.

        Args:
            graph: The memory graph to traverse.
            start_node: The starting node for traversal.
            target_node: Optional target node to reach.
            context: Optional context dictionary containing task info.

        Returns:
            A tuple of (success, path, stats).
            - success: Boolean indicating if the traversal succeeded.
            - path: List of node IDs visited in order.
            - stats: Dictionary of traversal statistics.
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Returns the name of this strategy.

        Returns:
            String name of the strategy.
        """
        pass

    def reset_stats(self) -> None:
        """Reset internal statistics counters."""
        self._stats = {
            "nodes_visited": 0,
            "edges_traversed": 0,
            "inference_calls": 0,
            "total_inference_time_ms": 0.0,
            "total_execution_time_ms": 0.0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns a copy of the current statistics.

        Returns:
            Dictionary of traversal statistics.
        """
        return self._stats.copy()

    def _record_inference(self, duration_ms: float) -> None:
        """
        Helper to record an inference call.

        Args:
            duration_ms: Duration of the inference call in milliseconds.
        """
        self._stats["inference_calls"] += 1
        self._stats["total_inference_time_ms"] += duration_ms

    def _record_node_visit(self) -> None:
        """Record that a node was visited."""
        self._stats["nodes_visited"] += 1

    def _record_edge_traversal(self) -> None:
        """Record that an edge was traversed."""
        self._stats["edges_traversed"] += 1

    def _start_timer(self) -> float:
        """Start the execution timer."""
        return time.time()

    def _stop_timer(self, start_time: float) -> float:
        """
        Stop the execution timer and return duration in ms.

        Args:
            start_time: The start time from _start_timer.

        Returns:
            Duration in milliseconds.
        """
        duration = time.time() - start_time
        self._stats["total_execution_time_ms"] += duration * 1000
        return duration * 1000
