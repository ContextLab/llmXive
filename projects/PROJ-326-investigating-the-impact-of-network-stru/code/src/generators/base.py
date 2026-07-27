"""
Base Generator Class.

Provides common functionality for all graph generators, including
connectivity checks and retry logic.
"""

import logging
import time
import signal
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, TypeVar, Generic, List
import networkx as nx

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """
    Abstract base class for graph generators.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_retries = config.get('simulation_params', {}).get('max_retries', 10)
    
    @abstractmethod
    def generate(self, seed: Optional[int] = None) -> Tuple[nx.Graph, Dict[str, Any]]:
        """
        Generate a graph.
        
        Args:
            seed: Random seed.
        
        Returns:
            Tuple of (graph, metadata).
        """
        pass
    
    def _check_connectivity(self, graph: nx.Graph) -> bool:
        """Check if the graph is connected."""
        return nx.is_connected(graph)
    
    def _log_retry(self, attempt: int, max_attempts: int, reason: str):
        logger.warning(f"Retry attempt {attempt}/{max_attempts}: {reason}")
