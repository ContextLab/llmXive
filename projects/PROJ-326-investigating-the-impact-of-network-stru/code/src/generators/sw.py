import logging
import time
from typing import Dict, Optional, Tuple, Any
import networkx as nx
import numpy as np
from code.src.generators.base import BaseGenerator
from code.src.generators.timeout import timeout, TimeoutError

logger = logging.getLogger(__name__)

class WattsStrogatzGenerator(BaseGenerator):
    """
    Generator for Watts-Strogatz (Small-World) graphs.
    
    Inherits from BaseGenerator to utilize shared connectivity checks,
    retry logic, and timeout mechanisms.
    
    Specifics:
    - Uses networkx.watts_strogatz_graph
    - Enforces clustering coefficient targets via retry logic
    - Logs warnings after 10 failed attempts to meet clustering target
    """

    def __init__(
        self,
        n: int,
        k: int,
        p: float,
        target_clustering: Optional[float] = None,
        max_retries: int = 10,
        timeout_seconds: float = 5.0,
        seed: Optional[int] = None
    ):
        """
        Initialize the Watts-Strogatz generator.
        
        Args:
            n: Number of nodes
            k: Each node is joined to its k nearest neighbors
            p: Probability of edge rewiring
            target_clustering: Optional target clustering coefficient to retry against
            max_retries: Maximum number of attempts to meet clustering target (default 10)
            timeout_seconds: Timeout for generation attempts
            seed: Random seed for reproducibility
        """
        super().__init__(
            topology_type="Watts-Strogatz",
            seed=seed,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        self.n = n
        self.k = k
        self.p = p
        self.target_clustering = target_clustering

    def _generate_single(self) -> Tuple[Any, Dict[str, Any]]:
        """
        Generate a single Watts-Strogatz graph.
        
        Returns:
            Tuple of (networkx.Graph, metadata_dict)
        """
        # Apply seed locally for this attempt
        if self.seed is not None:
            np.random.seed(self.seed)
        
        start_time = time.time()
        
        def _do_generation():
            # networkx.watts_strogatz_graph handles the core logic
            # seed is passed to ensure reproducibility within the call
            g = nx.watts_strogatz_graph(self.n, self.k, self.p, seed=self.seed)
            return g

        # Enforce timeout on the generation step
        try:
            graph = timeout(_do_generation, timeout_seconds=self.timeout_seconds)
        except TimeoutError as e:
            logger.warning(f"Timeout reached during Watts-Strogatz generation: {e}")
            # Fallback: try one more time without strict timeout if possible, 
            # or raise. Per base logic, we treat this as a failed attempt.
            raise e

        elapsed = time.time() - start_time
        
        metadata = {
            "algorithm": "Watts-Strogatz",
            "n": self.n,
            "k": self.k,
            "p": self.p,
            "generation_time_sec": elapsed,
            "seed": self.seed
        }

        return graph, metadata

    def _validate(self, graph: Any) -> Tuple[bool, Optional[float]]:
        """
        Validate the generated graph against clustering target if specified.
        
        Args:
            graph: The generated networkx graph
            
        Returns:
            Tuple of (is_valid, current_clustering_coefficient)
        """
        if self.target_clustering is None:
            return True, None

        try:
            cc = nx.average_clustering(graph)
        except Exception as e:
            logger.warning(f"Could not compute clustering coefficient: {e}")
            return False, 0.0

        # Check if within acceptable tolerance (e.g., 1% relative error or 0.01 absolute)
        # For strictness, we check if it meets the target. 
        # Often in WS, exact target is hard, so we check if it's >= target or close.
        # Given the prompt implies "retry logic" for clustering, we assume we want 
        # to hit the target. Let's define success as being within 5% relative or 0.05 absolute.
        tolerance = 0.05
        if abs(cc - self.target_clustering) <= tolerance:
            return True, cc
        
        return False, cc

    def generate(self) -> Tuple[Any, Dict[str, Any]]:
        """
        Generate a Watts-Strogatz graph, retrying if clustering target is not met.
        
        Utilizes shared timeout and retry logic from BaseGenerator.
        Logs a warning if 10 attempts are made without success.
        """
        return super().generate()

    def _generate_with_retry(self) -> Tuple[Any, Dict[str, Any]]:
        """
        Internal override to handle the specific retry loop for clustering.
        """
        attempt = 0
        last_clustering = None
        
        while attempt < self.max_retries:
            attempt += 1
            try:
                graph, metadata = self._generate_single()
                is_valid, current_cc = self._validate(graph)
                
                last_clustering = current_cc
                metadata["actual_clustering"] = current_cc

                if is_valid:
                    logger.info(f"Watts-Strogatz generation successful on attempt {attempt} (CC: {current_cc:.4f})")
                    return graph, metadata
                
                # If not valid, log and retry
                logger.debug(f"Attempt {attempt}: Clustering {current_cc:.4f} did not meet target {self.target_clustering}")
                
            except TimeoutError:
                logger.warning(f"Attempt {attempt} timed out during Watts-Strogatz generation")
                continue
            except Exception as e:
                logger.error(f"Attempt {attempt} failed with error: {e}")
                continue

        # If we reach here, all retries failed
        warning_msg = (
            f"Failed to generate Watts-Strogatz graph meeting clustering target "
            f"({self.target_clustering}) after {self.max_retries} attempts. "
            f"Last achieved clustering: {last_clustering}"
        )
        logger.warning(warning_msg)
        
        # Return the last generated graph anyway to avoid total failure, 
        # but metadata will reflect the failure
        if last_clustering is not None:
            metadata["generation_status"] = "failed_clustering_target"
        else:
            metadata["generation_status"] = "failed_no_graph_generated"
            
        return graph, metadata