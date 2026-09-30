import logging
import random
import numpy as np
import networkx as nx
from code.src.generators.base import BaseGenerator

logger = logging.getLogger(__name__)

class ErdosRenyiGenerator(BaseGenerator):
    """
    Generator for Erdos-Renyi (ER) random graphs.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.n = config.get("topology_targets", {}).get("erdos_renyi", {}).get("n", 30)
        self.p = config.get("topology_targets", {}).get("erdos_renyi", {}).get("p", 0.1)

    def _generate_graph(self):
        """Generate an ER graph."""
        try:
            g = nx.erdos_renyi_graph(self.n, self.p, seed=self.seed)
            metadata = {
                "algorithm": "erdos_renyi",
                "n": self.n,
                "p": self.p,
                "seed": self.seed
            }
            return g, metadata
        except Exception as e:
            logger.error(f"ER generation failed: {e}")
            return None, None
