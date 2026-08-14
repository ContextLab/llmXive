"""
Topological metric extraction.
"""
import networkx as nx
import numpy as np
from typing import Dict, Any
from .models import DefectGraph
from .utils import get_logger

logger = get_logger(__name__)

class MetricCalculator:
    """
    Computes network descriptors.
    """
    def __init__(self):
        self.logger = logger

    def calculate(self, graph: DefectGraph) -> Dict[str, float]:
        """
        Calculates Clustering Coefficient, Mean Degree, Moments, Percolation.
        """
        # Reconstruct NetworkX graph from DefectGraph
        G = nx.Graph()
        for node, neighbors in graph.adjacency_list.items():
            for neighbor in neighbors:
                G.add_edge(int(node), int(neighbor))
        
        if G.number_of_nodes() == 0:
            return {"clustering": 0.0, "mean_degree": 0.0, "variance": 0.0, "percolation": float('nan')}

        metrics = {}
        
        # Clustering Coefficient
        metrics["clustering"] = nx.average_clustering(G)
        
        # Mean Degree
        degrees = [d for n, d in G.degree()]
        metrics["mean_degree"] = np.mean(degrees)
        
        # Variance (2nd moment - mean^2)
        metrics["variance"] = np.var(degrees)
        
        # Percolation Threshold (approximation for random graphs)
        # For general graphs, we check giant component
        try:
            if nx.is_connected(G):
                metrics["percolation"] = 1.0 # Fully connected
            else:
                # Largest component size
                largest_cc = max(nx.connected_components(G), key=len)
                metrics["percolation"] = len(largest_cc) / G.number_of_nodes()
        except Exception as e:
            self.logger.warning(f"Percolation check failed: {e}")
            metrics["percolation"] = float('nan')

        return metrics
