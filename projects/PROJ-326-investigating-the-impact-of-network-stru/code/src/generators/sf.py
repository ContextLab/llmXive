import logging
import random
import numpy as np
import networkx as nx
from code.src.generators.base import BaseGenerator

logger = logging.getLogger(__name__)

class BarabasiAlbertGenerator(BaseGenerator):
    """
    Generator for Barabasi-Albert (BA) scale-free graphs.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.n = config.get("topology_targets", {}).get("barabasi_albert", {}).get("n", 30)
        self.m = config.get("topology_targets", {}).get("barabasi_albert", {}).get("m", 2)

    def _generate_graph(self):
        """Generate a BA graph."""
        try:
            g = nx.barabasi_albert_graph(self.n, self.m, seed=self.seed)
            metadata = {
                "algorithm": "barabasi_albert",
                "n": self.n,
                "m": self.m,
                "seed": self.seed
            }
            return g, metadata
        except Exception as e:
            logger.error(f"BA generation failed: {e}")
            return None, None
