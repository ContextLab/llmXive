"""
Base generator logic for network topology generation.
Implements shared connectivity checks, retry logic, and timeout handling.
"""
import logging
import time
import signal
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, TypeVar, Generic, List
import networkx as nx
import numpy as np

from code.src.generators.timeout import TimeoutHandler, TimeoutError
from code.src.utils.logging import log_run

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseGenerator(ABC, Generic[T]):
    """
    Abstract base class for network graph generators.
    Enforces connectivity verification and retry logic.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout_handler = TimeoutHandler(config)
        self.max_retries = config.get('max_retries', 10)
        self.retry_delay = config.get('retry_delay', 0.1)
        self.seed = config.get('seed', 42)
        np.random.seed(self.seed)

    def _log_event(self, event_type: str, details: Optional[Dict] = None):
        """Helper to log events to run_log.json"""
        log_run(event_type, details=details)

    def _generate_candidate(self) -> Optional[nx.Graph]:
        """
        Generate a single candidate graph.
        Must be implemented by subclasses.
        Returns None if generation fails immediately.
        """
        raise NotImplementedError

    def _verify_connectivity(self, graph: nx.Graph) -> bool:
        """
        Verify if the graph is connected.
        Returns True if connected, False otherwise.
        """
        if graph.number_of_nodes() == 0:
            return False
        if graph.number_of_nodes() == 1:
            return True
        return nx.is_connected(graph)

    def generate(self) -> Optional[Tuple[nx.Graph, Dict[str, Any]]]:
        """
        Generate a connected graph with retry logic.
        Returns (graph, metrics) tuple if successful, None if all retries exhausted.
        """
        start_time = time.time()
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                # Apply timeout if configured
                with self.timeout_handler.timeout_context():
                    candidate = self._generate_candidate()

                    if candidate is None:
                        logger.warning(f"Attempt {attempt}: Graph generation returned None")
                        last_error = "Generation returned None"
                        continue

                    # Verify connectivity
                    if not self._verify_connectivity(candidate):
                        logger.debug(f"Attempt {attempt}: Graph disconnected, retrying...")
                        last_error = "Disconnected graph"
                        continue

                    # Success
                    duration = time.time() - start_time
                    metrics = {
                        'attempt': attempt,
                        'duration_seconds': duration,
                        'nodes': candidate.number_of_nodes(),
                        'edges': candidate.number_of_edges(),
                        'is_connected': True
                    }
                    self._log_event('graph_generated', {
                        'status': 'success',
                        'attempt': attempt,
                        'metrics': metrics
                    })
                    return candidate, metrics

            except TimeoutError as te:
                logger.warning(f"Attempt {attempt}: Timeout occurred - {te}")
                last_error = str(te)
                continue
            except Exception as e:
                logger.warning(f"Attempt {attempt}: Generation failed - {e}")
                last_error = str(e)
                continue

            # Brief delay before retry
            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        # All retries exhausted
        duration = time.time() - start_time
        logger.warning(
            f"Max retries ({self.max_retries}) exceeded. "
            f"Last error: {last_error}. Proceeding to next graph."
        )
        self._log_event('divergence_detected', {
            'status': 'failed',
            'max_retries': self.max_retries,
            'total_duration_seconds': duration,
            'last_error': last_error,
            'reason': 'DISCONNECTED_NETWORK_FAILURE'
        })
        return None

    @abstractmethod
    def get_generator_name(self) -> str:
        """Return the name of the generator algorithm."""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return the parameters used for this generation."""
        pass
