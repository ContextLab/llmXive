import networkx as nx
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy.stats import moment as scipy_moment
from .models import DefectGraph
from .utils import get_logger

logger = get_logger(__name__)

class MetricCalculator:
    """
    Calculates topological metrics for DefectGraphs.
    
    Implements:
    - Clustering Coefficient
    - Mean Degree
    - Degree Distribution Moments
    - Percolation Threshold (Critical Probability)
    - Bonferroni-corrected p-value verification (FR-006)
    """

    def __init__(self):
        self.logger = logger

    def calculate_all(self, graph_obj: DefectGraph) -> Dict[str, Any]:
        """
        Calculate all supported metrics for a given DefectGraph.
        
        Args:
            graph_obj: The DefectGraph instance containing the NetworkX graph.
            
        Returns:
            Dictionary mapping metric names to their calculated values.
            Includes a 'bonferroni_verification' key if p-values are provided.
        """
        G = graph_obj.graph
        if G is None:
            self.logger.error("Cannot calculate metrics: Graph is None.")
            return {
                "clustering_coefficient": np.nan,
                "mean_degree": np.nan,
                "degree_variance": np.nan,
                "percolation_threshold": np.nan,
                "bonferroni_verification": None
            }

        metrics = {}
        
        # Clustering Coefficient
        metrics["clustering_coefficient"] = self._calculate_clustering(G)
        
        # Mean Degree
        metrics["mean_degree"] = self._calculate_mean_degree(G)
        
        # Degree Distribution Moments (Variance)
        metrics["degree_variance"] = self._calculate_degree_moment(G, 2)
        
        # Percolation Threshold
        metrics["percolation_threshold"] = self._calculate_percolation_threshold(G)
        
        # Bonferroni Verification
        # If the graph object contains raw p-values from a correlation test,
        # we verify the correction here.
        if hasattr(graph_obj, 'metadata') and graph_obj.metadata:
            raw_p_values = graph_obj.metadata.get('raw_p_values')
            if raw_p_values:
                metrics["bonferroni_verification"] = self._verify_bonferroni_correction(raw_p_values)
            else:
                metrics["bonferroni_verification"] = None
        else:
            metrics["bonferroni_verification"] = None
        
        return metrics

    def _calculate_clustering(self, G: nx.Graph) -> float:
        """Calculate the average clustering coefficient."""
        if G.number_of_nodes() == 0:
            return 0.0
        return nx.average_clustering(G)

    def _calculate_mean_degree(self, G: nx.Graph) -> float:
        """Calculate the mean degree of the graph."""
        if G.number_of_nodes() == 0:
            return 0.0
        degrees = [d for n, d in G.degree()]
        return float(np.mean(degrees))

    def _calculate_degree_moment(self, G: nx.Graph, order: int) -> float:
        """Calculate the specified order moment of the degree distribution."""
        if G.number_of_nodes() == 0:
            return 0.0
        degrees = np.array([d for n, d in G.degree()])
        if len(degrees) == 0:
            return 0.0
        # scipy.stats.moment calculates the central moment
        return float(scipy_moment(degrees, order))

    def _calculate_percolation_threshold(self, G: nx.Graph) -> float:
        """
        Calculate the site percolation threshold (pc) for the graph.
        
        Strategy:
        1. Identify the largest connected component (LCC) to handle disconnected graphs.
        2. Estimate pc using the inverse of the mean degree approximation: pc ≈ 1 / <k>.
        3. If the graph is empty or has no edges, return NaN with a warning.
        """
        if G.number_of_nodes() == 0:
            self.logger.warning("Graph is empty. Percolation threshold is undefined (NaN).")
            return np.nan

        # Handle disconnected graphs by focusing on the largest component
        if not nx.is_connected(G):
            try:
                largest_cc = max(nx.connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc).copy()
                self.logger.info(f"Graph is disconnected. Calculating threshold on largest component "
                               f"(size: {len(largest_cc)} nodes).")
            except Exception as e:
                self.logger.error(f"Failed to identify largest connected component: {e}")
                return np.nan
        else:
            subgraph = G

        mean_degree = self._calculate_mean_degree(subgraph)

        # Avoid division by zero
        if mean_degree <= 0:
            self.logger.warning(f"Mean degree of largest component is {mean_degree}. "
                              "Percolation threshold is undefined (NaN).")
            return np.nan

        # Approximation: pc ≈ 1 / <k>
        pc = 1.0 / mean_degree
        
        self.logger.debug(f"Estimated percolation threshold (pc ≈ 1/<k>): {pc:.6f} (mean_degree: {mean_degree:.6f})")
        return pc

    def _verify_bonferroni_correction(self, raw_p_values: List[float]) -> Dict[str, Any]:
        """
        Explicitly verifies Bonferroni-corrected p-values against the raw values.
        
        This enforces FR-006 by ensuring the family-wise error rate is controlled.
        It flags any instance where an uncorrected p < 0.05 but the corrected p > 0.05.
        
        Args:
            raw_p_values: List of raw p-values from statistical tests.
            
        Returns:
            Dictionary containing:
            - 'n_tests': Number of tests performed.
            - 'alpha': Significance level used (default 0.05).
            - 'corrected_threshold': The Bonferroni-corrected threshold (alpha / n).
            - 'flags': List of indices where significance status changed due to correction.
            - 'summary': A string summary of the verification.
        """
        if not raw_p_values:
            return {
                "n_tests": 0,
                "alpha": 0.05,
                "corrected_threshold": np.nan,
                "flags": [],
                "summary": "No p-values provided for verification."
            }

        n_tests = len(raw_p_values)
        alpha = 0.05
        corrected_threshold = alpha / n_tests
        
        flags = []
        significant_uncorrected = []
        significant_corrected = []
        
        for i, p in enumerate(raw_p_values):
            is_sig_uncorrected = p < alpha
            is_sig_corrected = p < corrected_threshold
            
            if is_sig_uncorrected and not is_sig_corrected:
                flags.append({
                    "index": i,
                    "raw_p": p,
                    "reason": "Significant uncorrected, non-significant corrected"
                })
            
            if is_sig_uncorrected:
                significant_uncorrected.append(i)
            if is_sig_corrected:
                significant_corrected.append(i)

        if flags:
            summary = (
                f"Bonferroni verification: {len(flags)} metric(s) lost significance after correction. "
                f"Raw p < {alpha} but Corrected p > {alpha}. "
                f"Indices: {[f['index'] for f in flags]}."
            )
            self.logger.warning(summary)
        else:
            summary = (
                f"Bonferroni verification: No metrics lost significance. "
                f"Family-wise error rate controlled at {alpha}."
            )
            self.logger.info(summary)

        return {
            "n_tests": n_tests,
            "alpha": alpha,
            "corrected_threshold": corrected_threshold,
            "flags": flags,
            "summary": summary,
            "significant_uncorrected_count": len(significant_uncorrected),
            "significant_corrected_count": len(significant_corrected)
        }

    def calculate_batch(self, graph_objects: List[DefectGraph]) -> List[Dict[str, Any]]:
        """
        Calculate metrics for a list of DefectGraph objects.
        
        Args:
            graph_objects: List of DefectGraph instances.
            
        Returns:
            List of metric dictionaries.
        """
        return [self.calculate_all(g) for g in graph_objects]
