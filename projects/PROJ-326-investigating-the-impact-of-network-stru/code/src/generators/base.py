import logging
import time
import signal
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, TypeVar, Generic, List
import networkx as nx

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseGenerator(ABC, Generic[T]):
    """
    Base class for all graph generators.
    Implements shared logic for connectivity checks, retry logic, and logging.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_retries = config.get("thresholds", {}).get("max_retries", 10)
        self.seed = config.get("global_seed", 42)

    @abstractmethod
    def _generate_graph(self) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Abstract method to generate a graph.
        Returns (graph, metadata) or (None, None) if generation fails.
        """
        pass

    def generate(self) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Generate a connected graph with retry logic.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                graph, metadata = self._generate_graph()
                if graph is None:
                    continue

                # Check connectivity
                if nx.is_connected(graph):
                    logger.debug(f"Generated connected graph on attempt {attempt}")
                    return graph, metadata
                else:
                    logger.warning(f"Graph disconnected on attempt {attempt}, retrying...")
            except Exception as e:
                logger.error(f"Generation failed on attempt {attempt}: {e}")
                continue

        logger.error(f"Failed to generate connected graph after {self.max_retries} attempts")
        return None, None
