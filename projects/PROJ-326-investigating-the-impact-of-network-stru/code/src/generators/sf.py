"""
Barabási-Albert (Scale-Free) Generator Module.

Implements the generation of scale-free networks using the preferential
attachment mechanism, inheriting from BaseGenerator.
"""
import logging
import time
from typing import Dict, Optional, Tuple, Any

import networkx as nx
import numpy as np

from code.src.generators.base import BaseGenerator
from code.src.generators.timeout import enforce_timeout, TimeoutError

logger = logging.getLogger(__name__)


class BarabasiAlbertGenerator(BaseGenerator):
    """
    Generates scale-free networks using the Barabási-Albert preferential
    attachment model.

    Inherits from BaseGenerator to utilize shared connectivity checks,
    retry logic, and timeout mechanisms.

    Attributes:
        m (int): Number of edges to attach from a new node to existing nodes.
    """

    def __init__(
        self,
        n: int,
        m: Optional[int] = None,
        seed: Optional[int] = None,
        timeout_seconds: float = 300.0,
        max_retries: int = 10,
        **kwargs: Any
    ):
        """
        Initialize the Barabási-Albert generator.

        Args:
            n: The number of nodes to generate.
            m: Number of edges to attach from a new node to existing nodes.
               If None, defaults to max(1, int(sqrt(n))).
            seed: Random seed for reproducibility.
            timeout_seconds: Maximum time allowed for generation attempts.
            max_retries: Maximum number of retry attempts if connectivity
                         validation fails (though BA is naturally connected).
            **kwargs: Additional parameters passed to BaseGenerator.
        """
        super().__init__(
            n=n,
            seed=seed,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            **kwargs
        )
        self.m = m if m is not None else max(1, int(np.sqrt(n)))
        self.generator_name = "BarabasiAlbert"
        self.topology_class = "scale_free"

        logger.info(
            f"Initialized {self.__class__.__name__} with n={n}, m={self.m}, seed={seed}"
        )

    def _generate_single_attempt(self) -> Tuple[Any, float]:
        """
        Perform a single attempt to generate the graph.

        This method uses networkx's barabasi_albert_graph function.

        Returns:
            Tuple of (networkx.Graph, generation_time_seconds).

        Raises:
            TimeoutError: If the generation exceeds the timeout limit.
            RuntimeError: If generation fails unexpectedly.
        """
        start_time = time.time()

        try:
            # Use networkx's built-in BA generator
            # The 'seed' argument ensures reproducibility
            G = nx.barabasi_albert_graph(
                n=self.n,
                m=self.m,
                seed=self.seed
            )

            elapsed = time.time() - start_time
            logger.debug(f"Graph generated in {elapsed:.4f}s")
            return G, elapsed

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Graph generation failed: {e}")
            raise RuntimeError(f"Failed to generate BA graph: {e}")

    def generate(self) -> Tuple[Any, Dict[str, Any]]:
        """
        Generate the Barabási-Albert graph with retry and timeout logic.

        Overrides BaseGenerator.generate to apply the specific timeout
        mechanism defined in T016a.

        Returns:
            Tuple of (networkx.Graph, metadata_dict).

        Raises:
            TimeoutError: If all attempts exceed the timeout limit.
            RuntimeError: If all retry attempts fail.
        """
        attempt = 0
        last_error = None
        start_total = time.time()

        while attempt < self.max_retries:
            attempt += 1
            logger.info(f"Generation attempt {attempt}/{self.max_retries}")

            try:
                # Wrap the generation attempt with timeout enforcement
                # We use a partial function to pass arguments to the wrapper
                def run_gen():
                    return self._generate_single_attempt()

                # Enforce timeout using the utility from T016a
                graph, gen_time = enforce_timeout(
                    run_gen,
                    timeout_seconds=self.timeout_seconds,
                    logger=logger
                )

                # BA graphs are inherently connected, but we verify as per base contract
                if not nx.is_connected(graph):
                    logger.warning(f"Attempt {attempt}: Generated graph is not connected. Retrying.")
                    continue

                # Success
                elapsed_total = time.time() - start_total
                metadata = self._build_metadata(
                    success=True,
                    attempts=attempt,
                    total_time=elapsed_total,
                    generation_time=gen_time,
                    extra_params={"m": self.m}
                )

                logger.info(f"Successfully generated scale-free graph (n={self.n}, m={self.m})")
                return graph, metadata

            except TimeoutError as te:
                last_error = te
                logger.warning(f"Attempt {attempt} timed out after {self.timeout_seconds}s")
                if attempt >= self.max_retries:
                    logger.error("Max retries exceeded due to timeout.")
                    raise
                continue

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed with error: {e}")
                if attempt >= self.max_retries:
                    logger.error("Max retries exceeded due to generation errors.")
                    raise
                continue

        # Should not reach here if logic is correct, but safe fallback
        raise RuntimeError(f"Failed to generate graph after {self.max_retries} attempts")

    def _build_metadata(
        self,
        success: bool,
        attempts: int,
        total_time: float,
        generation_time: float,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Construct metadata dictionary for the generated graph.

        Args:
            success: Whether the generation was successful.
            attempts: Number of attempts made.
            total_time: Total time elapsed for the operation.
            generation_time: Time taken for the successful generation call.
            extra_params: Additional parameters specific to this generator.

        Returns:
            Dictionary containing metadata.
        """
        base_meta = super()._build_metadata(
            success=success,
            attempts=attempts,
            total_time=total_time,
            generation_time=generation_time,
            extra_params=extra_params
        )
        base_meta["algorithm"] = "BarabasiAlbert"
        base_meta["preferential_attachment_m"] = self.m
        return base_meta