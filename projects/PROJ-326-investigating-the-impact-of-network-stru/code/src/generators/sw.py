"""
Watts-Strogatz (Small-World) Graph Generator.

Inherits from BaseGenerator.
"""

import logging
import time
from typing import Dict, Optional, Tuple, Any
import networkx as nx
import numpy as np

from code.src.generators.base import BaseGenerator

logger = logging.getLogger(__name__)


class WattsStrogatzGenerator(BaseGenerator):
    """
    Generates Watts-Strogatz small-world networks.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.n = config.get('simulation_params', {}).get('n_nodes', 100)
        self.k = config.get('simulation_params', {}).get('k_neighbors', 4)
        self.p_rewire = config.get('simulation_params', {}).get('rewiring_probability', 0.1)
    
    def generate(self, seed: Optional[int] = None) -> Tuple[nx.Graph, Dict[str, Any]]:
        """
        Generate a Watts-Strogatz graph.
        """
        if seed is not None:
            np.random.seed(seed)
        
        start_time = time.time()
        
        # Use seed for networkx if possible
        G = nx.watts_strogatz_graph(self.n, self.k, self.p_rewire, seed=seed)
        
        metadata = {
            "algorithm": "watts_strogatz",
            "n_nodes": self.n,
            "k_neighbors": self.k,
            "rewiring_probability": self.p_rewire,
            "seed": seed,
            "generation_time_seconds": time.time() - start_time,
            "graph_id": f"WS_{seed}_{int(time.time()*1000)}"
        }
        
        return G, metadata
