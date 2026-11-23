import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from scipy import stats
from typing import Dict, List, Tuple, Optional, Union

def calculate_vif(features: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        features: DataFrame containing features (predictors).
        
    Returns:
        pd.Series: VIF values for each feature.
    """
    vif_data = pd.Series()
    for col in features.columns:
        other_cols = [c for c in features.columns if c != col]
        if len(other_cols) == 0:
            vif_data[col] = 1.0
        else:
            r2 = stats.linregress(features[col], features[other_cols].mean(axis=1)).rvalue ** 2
            # Better approach: use linear regression model
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(features[other_cols], features[col])
            r2 = model.score(features[other_cols], features[col])
            vif_data[col] = 1.0 / (1.0 - r2) if r2 < 1.0 else float('inf')
    return vif_data

def plot_convergence(seeds: List[int], decay_rates: List[float], output_path: str):
    """
    Plot the convergence of decay rates across different random seeds.
    
    Args:
        seeds: List of random seeds used.
        decay_rates: List of decay rates obtained.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.errorbar(seeds, decay_rates, yerr=np.std(decay_rates), fmt='o', capsize=5)
    plt.axhline(y=np.mean(decay_rates), color='r', linestyle='--', label='Mean')
    plt.xlabel('Random Seed')
    plt.ylabel('Decay Rate')
    plt.title('Convergence of Decay Rates')
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def generate_ring_analytical_eigenvalues(N: int) -> np.ndarray:
    """
    Generate analytical eigenvalues for a ring graph Laplacian.
    
    Args:
        N: Number of nodes in the ring.
        
    Returns:
        np.ndarray: Array of eigenvalues.
    """
    k = np.arange(N)
    eigenvalues = 2 - 2 * np.cos(2 * np.pi * k / N)
    return eigenvalues

def validate_laplacian_eigenvalues(graph: nx.Graph, tolerance: float = 1e-6) -> bool:
    """
    Validate the Laplacian eigenvalues of a graph against analytical solutions for specific topologies.
    
    Args:
        graph: A NetworkX graph.
        tolerance: Tolerance for comparison.
        
    Returns:
        bool: True if validation passes, False otherwise.
    """
    L = nx.laplacian_matrix(graph).toarray()
    eigenvalues = np.linalg.eigvalsh(L)
    eigenvalues = np.sort(eigenvalues)
    
    # For a ring graph
    N = graph.number_of_nodes()
    if N > 2 and all(graph.degree() == 2):  # Check if it's a ring
        analytical = generate_ring_analytical_eigenvalues(N)
        analytical = np.sort(analytical)
        if not np.allclose(eigenvalues, analytical, atol=tolerance):
            return False
    return True

def check_vif_threshold(vif_values: pd.Series, threshold: float = 5.0) -> List[str]:
    """
    Check which features exceed the VIF threshold.
    
    Args:
        vif_values: Series of VIF values.
        threshold: VIF threshold.
        
    Returns:
        List[str]: List of feature names exceeding the threshold.
    """
    return [col for col, vif in vif_values.items() if vif > threshold]
