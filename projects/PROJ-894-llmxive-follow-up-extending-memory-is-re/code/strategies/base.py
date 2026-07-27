"""
Base class for traversal strategies.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx
import logging
import time

logger = logging.getLogger(__name__)

class BaseTraversal(ABC):
    """
    Abstract base class for graph traversal strategies.
    """
    
    def __init__(self):
        pass

    @abstractmethod
    def run(self, G: nx.Graph, question: str) -> Dict[str, Any]:
        """
        Execute the traversal strategy.
        
        Args:
            G: The memory graph.
            question: The user question.
        
        Returns:
            Dictionary containing 'answer', 'nodes_visited', 'path', 'status'.
        """
        pass

    def _log_step(self, step: int, current_nodes: List[Any], visited_count: int):
        """Helper to log traversal steps."""
        logger.debug(f"Step {step}: Visited {visited_count} nodes. Current frontier: {len(current_nodes)} nodes.")
