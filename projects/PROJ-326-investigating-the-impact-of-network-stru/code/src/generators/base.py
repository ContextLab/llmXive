"""
Base generator logic for synthetic spin network datasets.

This module provides the abstract base class and shared utilities for all
topology generators (Erdős-Rényi, Watts-Strogatz, Barabási-Albert).
It handles connectivity verification, retry limits, and timeout enforcement.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, TypeVar, Generic, List

import networkx as nx
import numpy as np

from code.src.generators.timeout import timeout, TimeoutError
from code.src.utils.logging import log_metric
from code.src.utils.config import get_config_value

logger = logging.getLogger(__name__)

# Type variable for graph types
GraphT = TypeVar('GraphT', bound=nx.Graph)


class BaseGenerator(ABC, Generic[GraphT]):
    """
    Abstract base class for network topology generators.

    Provides shared logic for:
    - Connectivity verification
    - Retry limits for generation failures
    - Timeout enforcement
    - Metric tracking and logging
    """

    def __init__(
        self,
        topology_class: str,
        config: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None
    ):
        """
        Initialize the base generator.

        Args:
            topology_class: Name of the topology class (e.g., 'ErdosRenyi')
            config: Configuration dictionary (optional, loads defaults if None)
            max_retries: Maximum number of retry attempts for failed generation.
                        If None, uses value from config or default (10).
            timeout_seconds: Timeout in seconds for single generation attempt.
                            If None, uses value from config or default (30.0).
        """
        self.topology_class = topology_class
        self.config = config or {}

        # Load retry limit from config or use default
        if max_retries is not None:
            self.max_retries = max_retries
        else:
            self.max_retries = get_config_value(
                self.config,
                'generators.max_retries',
                default=10
            )

        # Load timeout from config or use default
        if timeout_seconds is not None:
            self.timeout_seconds = timeout_seconds
        else:
            self.timeout_seconds = get_config_value(
                self.config,
                'generators.timeout_seconds',
                default=30.0
            )

        logger.info(f"Initialized {topology_class} generator with "
                   f"max_retries={self.max_retries}, timeout={self.timeout_seconds}s")

    @abstractmethod
    def _generate_single(self, **kwargs) -> GraphT:
        """
        Abstract method to generate a single graph.
        Must be implemented by subclasses.

        Args:
            **kwargs: Generator-specific parameters (n, p, k, etc.)

        Returns:
            A networkx Graph instance
        """
        pass

    @abstractmethod
    def _validate_params(self, **kwargs) -> None:
        """
        Abstract method to validate generator-specific parameters.
        Must be implemented by subclasses.
        """
        pass

    def _check_connectivity(self, graph: GraphT) -> bool:
        """
        Check if the graph is connected.

        Args:
            graph: Networkx graph to check

        Returns:
            True if connected, False otherwise
        """
        if graph.number_of_nodes() == 0:
            return False
        if graph.number_of_nodes() == 1:
            return True
        return nx.is_connected(graph)

    def _log_failure(self, attempt: int, error: str) -> None:
        """
        Log a generation failure attempt.

        Args:
            attempt: Current attempt number
            error: Description of the error
        """
        logger.warning(
            f"Generation attempt {attempt}/{self.max_retries} failed for "
            f"{self.topology_class}: {error}"
        )
        log_metric(
            "generation_failure",
            {
                "topology_class": self.topology_class,
                "attempt": attempt,
                "max_retries": self.max_retries,
                "error": error
            }
        )

    def generate(self, **kwargs) -> Tuple[GraphT, Dict[str, Any]]:
        """
        Generate a connected graph with retry logic and timeout enforcement.

        This method:
        1. Validates input parameters
        2. Attempts generation with timeout enforcement
        3. Checks connectivity
        4. Retries up to max_retries on failure
        5. Logs all attempts and final result

        Args:
            **kwargs: Generator-specific parameters

        Returns:
            Tuple of (generated_graph, metadata_dict)

        Raises:
            RuntimeError: If generation fails after all retries
            ValueError: If parameters are invalid
        """
        self._validate_params(**kwargs)

        last_error = None
        start_time = time.time()

        for attempt in range(1, self.max_retries + 1):
            try:
                # Enforce timeout on generation attempt
                graph = timeout(
                    self._generate_single,
                    timeout_seconds=self.timeout_seconds
                )(**kwargs)

                # Verify connectivity
                if not self._check_connectivity(graph):
                    raise RuntimeError(
                        f"Generated graph is not connected (nodes={graph.number_of_nodes()}, "
                        f"edges={graph.number_of_edges()})"
                    )

                # Success!
                elapsed = time.time() - start_time
                metadata = {
                    "topology_class": self.topology_class,
                    "nodes": graph.number_of_nodes(),
                    "edges": graph.number_of_edges(),
                    "is_connected": True,
                    "attempt_count": attempt,
                    "elapsed_time_seconds": elapsed,
                    "parameters": kwargs.copy()
                }

                logger.info(
                    f"Successfully generated {self.topology_class} graph "
                    f"on attempt {attempt} in {elapsed:.2f}s"
                )
                log_metric("generation_success", metadata)

                return graph, metadata

            except TimeoutError as e:
                last_error = f"Timeout after {self.timeout_seconds}s: {str(e)}"
                self._log_failure(attempt, last_error)

            except Exception as e:
                last_error = str(e)
                self._log_failure(attempt, last_error)

        # All retries exhausted
        elapsed = time.time() - start_time
        error_msg = (
            f"Failed to generate connected {self.topology_class} graph after "
            f"{self.max_retries} attempts in {elapsed:.2f}s. Last error: {last_error}"
        )

        logger.error(error_msg)
        log_metric(
            "generation_failed",
            {
                "topology_class": self.topology_class,
                "attempts": self.max_retries,
                "total_time_seconds": elapsed,
                "final_error": last_error
            }
        )

        raise RuntimeError(error_msg)

    def get_default_params(self) -> Dict[str, Any]:
        """
        Return default parameters for this generator.
        Should be overridden by subclasses.

        Returns:
            Dictionary of default parameters
        """
        return {}