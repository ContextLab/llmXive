"""
Barabási-Albert (Scale-Free) Graph Generator.

Inherits from BaseGenerator.
"""

import logging
import time
from typing import Dict, Optional, Tuple, Any
import networkx as nx
import numpy as np

from code.src.generators.base import BaseGenerator

logger = logging.getLogger(__name__)


class BarabasiAlbertGenerator(BaseGenerator):
    """
    Generates Barabási-Albert scale-free networks.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.n = config.get('simulation_params', {}).get('n_nodes', 100)
        self.m = config.get('simulation_params', {}).get('m_edges', 2)
    
    def generate(self, seed: Optional[int] = None) -> Tuple[nx.Graph, Dict[str, Any]]:
        """
        Generate a Barabási-Albert graph.
        """
        if seed is not None:
            np.random.seed(seed)
        
        start_time = time.time()
        
        G = nx.barabasi_albert_graph(self.n, self.m, seed=seed)
        
        metadata = {
            "algorithm": "barabasi_albert",
            "n_nodes": self.n,
            "m_edges": self.m,
            "seed": seed,
            "generation_time_seconds": time.time() - start_time,
            "graph_id": f"BA_{seed}_{int(time.time()*1000)}"
        }
        
        return G, metadata
