import logging
import time
import signal
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, TypeVar, Generic, List
import networkx as nx
import numpy as np
from code.src.utils.logging import log_run, log_metric
from code.src.utils.config import get_global_config

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=nx.Graph)

class BaseGenerator(ABC, Generic[T]):
    """
    Abstract base class for network topology generators.
    Enforces connectivity verification with retry logic.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_global_config()
        self.retry_limit = self.config.get('simulation_params', {}).get('max_retry_attempts', 10)
        self.seed = self.config.get('global_seed', 42)
        self._run_id = None

    def set_run_id(self, run_id: str):
        """Set the run ID for logging purposes."""
        self._run_id = run_id

    @abstractmethod
    def _generate_attempt(self, rng: np.random.Generator) -> T:
        """
        Generate a single graph attempt.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the generator (e.g., 'ErdosRenyi')."""
        pass

    def _log_warning(self, message: str):
        """Helper to log warnings with run context if available."""
        if self._run_id:
            logger.warning(f"[Run {self._run_id}] {message}")
        else:
            logger.warning(message)

    def _log_retry_event(self, attempt: int, reason: str):
        """Log a retry event to the run log."""
        if self._run_id:
            log_run(
                event_type="retry_attempt",
                run_id=self._run_id,
                seed=self.seed,
                metadata={
                    "attempt": attempt,
                    "reason": reason,
                    "generator": self.get_name()
                }
            )

    def _log_connectivity_warning(self, attempts: int):
        """Log a warning when max retries are reached."""
        self._log_warning(
            f"Generator {self.get_name()} reached max retries ({attempts}) "
            "without generating a connected graph. Proceeding to next graph."
        )
        # Log divergence/timeout event type as per spec requirements for warnings
        if self._run_id:
            log_run(
                event_type="divergence_detected", # Using divergence_detected for failed topology generation as a warning event
                run_id=self._run_id,
                seed=self.seed,
                metadata={
                    "type": "connectivity_failure",
                    "max_attempts": attempts,
                    "generator": self.get_name()
                }
            )

    def generate(self, rng: np.random.Generator, graph_id: str = "unknown") -> Optional[T]:
        """
        Generate a connected graph with retry logic.
        
        Returns:
            nx.Graph: A connected graph if successful within retry limits.
            None: If the retry limit is exceeded.
        """
        start_time = time.time()
        attempts = 0
        max_attempts = self.retry_limit

        while attempts < max_attempts:
            attempts += 1
            try:
                # Generate attempt
                graph = self._generate_attempt(rng)
                
                # Verify connectivity
                if nx.is_connected(graph):
                    duration = time.time() - start_time
                    log_metric(
                        event_type="graph_generated",
                        run_id=self._run_id,
                        seed=self.seed,
                        metric="generation_duration_seconds",
                        value=duration,
                        metadata={
                            "graph_id": graph_id,
                            "attempts": attempts,
                            "status": "success",
                            "generator": self.get_name()
                        }
                    )
                    return graph
                else:
                    # Not connected, retry
                    self._log_retry_event(attempts, "graph_disconnected")
                    # Clean up disconnected graph to free memory if needed
                    del graph 
                
            except Exception as e:
                self._log_retry_event(attempts, f"generation_error: {str(e)}")
                logger.error(f"Error generating graph on attempt {attempts}: {e}")

        # Max retries reached
        self._log_connectivity_warning(attempts)
        duration = time.time() - start_time
        log_metric(
            event_type="divergence_detected", # Using divergence_detected for failed topology generation
            run_id=self._run_id,
            seed=self.seed,
            metric="generation_failure",
            value=1.0,
            metadata={
                "graph_id": graph_id,
                "attempts": attempts,
                "status": "failed",
                "reason": "max_retries_exceeded",
                "generator": self.get_name()
            }
        )
        return None
