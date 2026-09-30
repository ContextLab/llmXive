import logging
import random
import numpy as np
import networkx as nx
from code.src.generators.base import BaseGenerator

logger = logging.getLogger(__name__)

class WattsStrogatzGenerator(BaseGenerator):
    """
    Generator for Watts-Strogatz (WS) small-world graphs.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.n = config.get("topology_targets", {}).get("watts_strogatz", {}).get("n", 30)
        self.k = config.get("topology_targets", {}).get("watts_strogatz", {}).get("k", 4)
        self.p = config.get("topology_targets", {}).get("watts_strogatz", {}).get("p", 0.3)

    def _generate_graph(self):
        """Generate a WS graph."""
        try:
            # Ensure n is odd or k is even for WS graph to be valid
            if self.n % 2 == 0 and self.k % 2 != 0:
                self.k += 1
                logger.warning(f"Adjusted k to {self.k} for valid WS graph")

            g = nx.watts_strogatz_graph(self.n, self.k, self.p, seed=self.seed)
            metadata = {
                "algorithm": "watts_strogatz",
                "n": self.n,
                "k": self.k,
                "p": self.p,
                "seed": self.seed
            }
            return g, metadata
        except Exception as e:
            logger.error(f"WS generation failed: {e}")
            return None, None
