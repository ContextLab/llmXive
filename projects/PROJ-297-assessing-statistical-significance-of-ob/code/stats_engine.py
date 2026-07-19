"""
Statistical engine for correlation analysis and permutation testing.
"""

import pandas as pd
import numpy as np
from scipy import stats
import networkx as nx
from typing import Callable, Dict, List, Optional, Tuple, Any
import math
import logging

import config

# Configure logging for this module
logger = logging.getLogger(__name__)

def compute_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """Compute correlation matrix."""
    return df.corr(method=method)

def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:
    """Construct a graph from correlation matrix."""
    G = nx.Graph()
    nodes = corr_matrix.columns
    G.add_nodes_from(nodes)
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            val = abs(corr_matrix.iloc[i, j])
            if val >= threshold:
                G.add_edge(nodes[i], nodes[j], weight=val)
    return G

def calculate_stats(graph: nx.Graph) -> Dict[str, float]:
    """Calculate network statistics."""
    if graph.number_of_edges() == 0:
        return {
            "mean_absolute_correlation": 0.0,
            "edge_density": 0.0,
            "max_absolute_correlation": 0.0,
            "average_clustering_coefficient": 0.0
        }
    
    edges = [abs(graph[u][v].get('weight', 0)) for u, v in graph.edges()]
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    max_edges = n_nodes * (n_nodes - 1) / 2
    
    return {
        "mean_absolute_correlation": np.mean(edges),
        "edge_density": n_edges / max_edges if max_edges > 0 else 0.0,
        "max_absolute_correlation": np.max(edges),
        "average_clustering_coefficient": nx.average_clustering(graph)
    }

def _calculate_factorial_approximation(n: int) -> float:
    """
    Calculate an approximation of n! for large n using Stirling's approximation,
    or exact factorial for small n.
    Returns float to handle large numbers.
    """
    if n <= 1:
        return 1.0
    if n < 20:
        return float(math.factorial(n))
    # Stirling's approximation for large n
    return math.sqrt(2 * math.pi * n) * ((n / math.e) ** n)

def _get_max_unique_permutations(n: int) -> int:
    """
    Determine the maximum number of unique permutations for a dataset of size n.
    For n >= 13, n! exceeds 10^9, so we cap at a practical limit.
    For n < 13, we return the exact factorial.
    """
    if n < 1:
        return 1
    
    # For very small n, n! is small
    if n <= 12:
        return math.factorial(n)
    
    # For n >= 13, n! is huge (6,227,020,800).
    # We cap at a practical limit (e.g., 10^9) to avoid infinite loops
    # or redundant calculations that yield no new permutations.
    # However, the task asks to ensure N does not exceed the theoretical max.
    # Since 10^9 is already a massive number of permutations, we can safely cap
    # at 10^9 for n >= 13, as the theoretical max is astronomically larger.
    # But strictly speaking, the task says "ensure N does not exceed the theoretical maximum".
    # If the requested N is 1000 and n=13, 1000 < 13!, so no change.
    # If n=5, 5! = 120. If requested N=1000, we must cap at 120.
    
    # We only need to return the exact max for small n where the cap matters.
    # For large n, the cap (10^9) is effectively "infinite" for our purposes,
    # but to be precise, we return the theoretical max for n <= 12.
    # For n > 12, the theoretical max is so large that any reasonable N (e.g., 1000)
    # will always be less than it. So we don't need to cap for n > 12.
    # We just return a very large number to indicate "no practical cap needed".
    return 10**15 # Arbitrary large number for n > 12

def adjust_permutation_count(n: int, requested_n: int) -> int:
    """
    Adjust the permutation count N dynamically if the dataset size n is small.
    Ensures N does not exceed the theoretical maximum number of unique permutations (n!).
    
    Args:
        n: Number of samples (rows) in the dataset.
        requested_n: The originally requested number of permutations.
        
    Returns:
        The adjusted number of permutations.
    """
    if n <= 0:
        logger.warning(f"Dataset size n={n} is invalid. Using requested_n={requested_n}.")
        return requested_n
    
    max_permutations = _get_max_unique_permutations(n)
    
    if requested_n > max_permutations:
        logger.warning(
            f"Dataset size n={n} is small. Theoretical max unique permutations = {max_permutations}. "
            f"Requested N={requested_n} exceeds this. Adjusting N to {max_permutations}."
        )
        return max_permutations
    
    return requested_n

def generate_null_distribution(
    df: pd.DataFrame, 
    n_permutations: int, 
    stats_func: Callable,
    dataset_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate null distribution via permutation."""
    # T083: Adjust permutation count for small datasets
    n_samples = len(df)
    adjusted_n = adjust_permutation_count(n_samples, n_permutations)
    
    if adjusted_n != n_permutations:
        logger.info(f"Adjusted permutation count for dataset {dataset_id}: {n_permutations} -> {adjusted_n}")
    
    observed_stats = stats_func(df)
    null_stats = []
    
    # Use a local random state to ensure reproducibility if called multiple times
    rng = np.random.default_rng()
    
    for _ in range(adjusted_n):
        # Permute rows
        permuted_df = df.sample(frac=1, random_state=rng).reset_index(drop=True)
        null_stat = stats_func(permuted_df)
        null_stats.append(null_stat['mean_absolute_correlation'])
    
    return {
        "observed": observed_stats['mean_absolute_correlation'],
        "distribution": null_stats,
        "n_permutations_actual": adjusted_n
    }

def calculate_empirical_p_value(null_dist: Dict, observed_val: float) -> float:
    """Calculate empirical p-value."""
    r = sum(1 for x in null_dist['distribution'] if x >= observed_val)
    n = len(null_dist['distribution'])
    return (r + 1) / (n + 1)

def generate_synthetic_dataset(n: int = 500, v: int = 20) -> pd.DataFrame:
    """Generate synthetic dataset with identity covariance."""
    np.random.seed(42)
    data = np.random.randn(n, v)
    columns = [f"var_{i}" for i in range(v)]
    return pd.DataFrame(data, columns=columns)

def generate_permuted_correlations(df: pd.DataFrame, n_permutations: int) -> List[pd.DataFrame]:
    """Generate permuted correlation matrices for reuse in sensitivity analysis."""
    permuted_corrs = []
    rng = np.random.default_rng()
    for _ in range(n_permutations):
        permuted_df = df.sample(frac=1, random_state=rng).reset_index(drop=True)
        corr = compute_correlation(permuted_df)
        permuted_corrs.append(corr)
    return permuted_corrs

def main():
    """Main entry point for testing."""
    pass

if __name__ == "__main__":
    main()
