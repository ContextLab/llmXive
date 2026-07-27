"""
Erdős-Rényi Graph Generator.

Inherits from BaseGenerator and implements ER specific logic.
"""

import logging
import time
from typing import Dict, Optional, Tuple, Any
import networkx as nx
import numpy as np

from code.src.generators.base import BaseGenerator

logger = logging.getLogger(__name__)


class ErdosRenyiGenerator(BaseGenerator):
    """
    Generates Erdős-Rényi random graphs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Extract params
        self.n = config.get('simulation_params', {}).get('n_nodes', 100)
        self.p = config.get('simulation_params', {}).get('edge_probability', 0.1)
    
    def generate(self, seed: Optional[int] = None) -> Tuple[nx.Graph, Dict[str, Any]]:
        """
        Generate a single Erdős-Rényi graph.
        
        Args:
            seed: Random seed for reproducibility.
        
        Returns:
            Tuple of (networkx graph, metadata dict).
        """
        if seed is not None:
            np.random.seed(seed)
            # Note: networkx uses its own random state, we pass it if needed
            # or rely on global seed if set.
        
        start_time = time.time()
        
        # Generate graph
        G = nx.erdos_renyi_graph(self.n, self.p)
        
        metadata = {
            "algorithm": "erdos_renyi",
            "n_nodes": self.n,
            "edge_probability": self.p,
            "seed": seed,
            "generation_time_seconds": time.time() - start_time,
            "graph_id": f"ER_{seed}_{int(time.time()*1000)}"
        }
        
        return G, metadata
