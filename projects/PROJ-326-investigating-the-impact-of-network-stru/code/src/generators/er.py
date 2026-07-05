"""
Erdős-Rényi (ER) Random Graph Generator.

Implements the generation of connected Erdős-Rényi graphs with a target
edge probability, inheriting from BaseGenerator to ensure connectivity
and logging standards.
"""
import logging
import time
from typing import Dict, Optional, Tuple, Any

import networkx as nx
import numpy as np

from code.src.generators.base import BaseGenerator
from code.src.generators.timeout import timeout, TimeoutError
from code.src.utils.logging import log_run, log_metric
from code.src.utils.reproducibility import generate_run_id

logger = logging.getLogger(__name__)


class ErdosRenyiGenerator(BaseGenerator):
    """
    Generator for Erdős-Rényi random graphs.

    Generates graphs G(n, p) where edges exist with probability p.
    Ensures the resulting graph is connected via retry logic defined in the base class.
    """

    def __init__(
        self,
        n: int,
        p: float,
        seed: Optional[int] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None
    ):
        """
        Initialize the Erdős-Rényi generator.

        Args:
            n: Number of nodes.
            p: Probability of edge creation (0.0 to 1.0).
            seed: Random seed for reproducibility.
            max_retries: Maximum number of attempts to generate a connected graph.
                         Defaults to base class configuration if None.
            timeout_seconds: Timeout for the generation attempt.
        """
        super().__init__(
            topology_class="ErdosRenyi",
            n=n,
            p=p,
            seed=seed,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        self.p = p

    @timeout
    def _generate_single(self, n: int, p: float, rng: np.random.Generator) -> nx.Graph:
        """
        Generate a single Erdős-Rényi graph instance.

        Args:
            n: Number of nodes.
            p: Edge probability.
            rng: NumPy random generator instance.

        Returns:
            A networkx Graph instance.

        Raises:
            TimeoutError: If generation exceeds the timeout limit (handled by decorator).
        """
        # Use networkx's built-in ER generator
        # We use the provided rng to ensure reproducibility if we were passing it directly
        # to nx, but nx.random_graphs.erdos_renyi_graph uses global np.random by default
        # unless a seed is passed. To strictly control seed via our BaseGenerator logic,
        # we rely on the seed set in __init__ which sets global state in BaseGenerator.
        # However, to be safe and explicit with the rng passed here:
        # We construct the graph manually or use the seed parameter of nx function.
        # Since we set global seed in BaseGenerator, we can just call the function.
        
        # Note: nx.erdos_renyi_graph(n, p, seed=None)
        # If seed is None, it uses global np.random state.
        # Our BaseGenerator.__init__ sets np.random.seed(self.seed) and random.seed(self.seed).
        
        graph = nx.erdos_renyi_graph(n, p, seed=self.seed)
        return graph

    def generate(self) -> Tuple[nx.Graph, Dict[str, Any]]:
        """
        Generate a connected Erdős-Rényi graph.

        This method wraps the generation logic with retry and timeout handling
        as defined in BaseGenerator.

        Returns:
            A tuple containing:
                - The generated connected NetworkX graph.
                - A dictionary of metadata including generation time, success status, etc.

        Raises:
            RuntimeError: If a connected graph cannot be generated within max_retries.
        """
        start_time = time.time()
        run_id = generate_run_id()
        
        # Log the start of the generation attempt
        log_run(
            run_id=run_id,
            status="started",
            topology_class=self.topology_class,
            parameters={"n": self.n, "p": self.p, "seed": self.seed}
        )

        try:
            graph, attempts = super().generate_with_retry(self._generate_single)
            
            elapsed_time = time.time() - start_time

            # Compute metrics
            metrics = {
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "density": nx.density(graph),
                "is_connected": nx.is_connected(graph),
                "avg_clustering": nx.average_clustering(graph),
                "avg_path_length": nx.average_shortest_path_length(graph) if nx.is_connected(graph) else float('inf'),
            }

            metadata = {
                "run_id": run_id,
                "topology_class": self.topology_class,
                "parameters": {
                    "n": self.n,
                    "p": self.p,
                    "seed": self.seed
                },
                "attempts": attempts,
                "elapsed_seconds": elapsed_time,
                "metrics": metrics,
                "status": "success"
            }

            # Log the result
            log_metric(run_id, "generation_success", True)
            log_metric(run_id, "num_nodes", metrics["num_nodes"])
            log_metric(run_id, "num_edges", metrics["num_edges"])
            
            logger.info(f"Successfully generated connected ER graph: n={self.n}, p={self.p}, "
                        f"edges={metrics['num_edges']}, attempts={attempts}")

            return graph, metadata

        except TimeoutError as e:
            elapsed_time = time.time() - start_time
            logger.warning(f"Timeout reached while generating ER graph (n={self.n}, p={self.p}).")
            
            metadata = {
                "run_id": run_id,
                "topology_class": self.topology_class,
                "parameters": {"n": self.n, "p": self.p, "seed": self.seed},
                "elapsed_seconds": elapsed_time,
                "status": "timeout",
                "error": str(e)
            }
            log_metric(run_id, "generation_success", False)
            log_metric(run_id, "status", "timeout")
            raise RuntimeError("ER graph generation timed out.") from e
        
        except RuntimeError as e:
            elapsed_time = time.time() - start_time
            logger.warning(f"Failed to generate connected ER graph after {self.max_retries} attempts.")
            
            metadata = {
                "run_id": run_id,
                "topology_class": self.topology_class,
                "parameters": {"n": self.n, "p": self.p, "seed": self.seed},
                "elapsed_seconds": elapsed_time,
                "status": "failed",
                "error": str(e)
            }
            log_metric(run_id, "generation_success", False)
            log_metric(run_id, "status", "failed")
            raise