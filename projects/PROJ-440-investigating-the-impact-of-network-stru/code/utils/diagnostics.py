"""
Diagnostic utilities for network analysis and simulation validation.
"""
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
        features: DataFrame with feature columns (no target variable)
    
    Returns:
        Series with VIF values for each feature
    """
    vif_data = pd.Series(index=features.columns, dtype=float)
    
    for feature in features.columns:
        other_features = [f for f in features.columns if f != feature]
        X = features[other_features]
        y = features[feature]
        
        # Fit linear model
        model = pd.DataFrame({'intercept': np.ones(len(y))}).join(X)
        rsquared = stats.linregress(model['intercept'], y)[2] ** 2
        
        # Calculate VIF
        if rsquared >= 1.0:
            vif_data[feature] = np.inf
        else:
            vif_data[feature] = 1 / (1 - rsquared)
    
    return vif_data


def plot_convergence(decay_rates: List[float], output_path: str) -> None:
    """
    Plot convergence of decay rates across multiple simulation runs.
    
    Args:
        decay_rates: List of decay rates from multiple runs
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    
    # Calculate running mean and std
    running_mean = []
    running_std = []
    for i in range(len(decay_rates)):
        running_mean.append(np.mean(decay_rates[:i+1]))
        running_std.append(np.std(decay_rates[:i+1]))
    
    # Plot
    plt.errorbar(
        range(len(decay_rates)),
        running_mean,
        yerr=running_std,
        capsize=3,
        fmt='-o',
        label='Running Mean ± Std'
    )
    
    plt.axhline(y=running_mean[-1], color='r', linestyle='--', label='Final Mean')
    
    plt.xlabel('Simulation Run')
    plt.ylabel('Decay Rate')
    plt.title('Convergence of Decay Rates')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def validate_laplacian_eigenvalues(graph: nx.Graph, tol: float = 1e-6) -> Tuple[bool, Dict]:
    """
    Validate Laplacian eigenvalues properties.
    
    The Laplacian matrix should have:
    - All eigenvalues >= 0
    - Smallest eigenvalue = 0 (for connected graphs)
    - Number of zero eigenvalues = number of connected components
    
    Args:
        graph: NetworkX graph
        tol: Tolerance for floating point comparisons
    
    Returns:
        Tuple of (is_valid, details_dict)
    """
    laplacian = nx.laplacian_matrix(graph).toarray()
    eigenvalues = np.linalg.eigvalsh(laplacian)
    
    details = {
        'min_eigenvalue': float(np.min(eigenvalues)),
        'max_eigenvalue': float(np.max(eigenvalues)),
        'n_zero_eigenvalues': int(np.sum(np.abs(eigenvalues) < tol)),
        'n_connected_components': nx.number_connected_components(graph),
        'all_non_negative': bool(np.all(eigenvalues >= -tol))
    }
    
    is_valid = (
        details['all_non_negative'] and
        details['n_zero_eigenvalues'] == details['n_connected_components']
    )
    
    return is_valid, details


def generate_ring_analytical_eigenvalues(n: int) -> np.ndarray:
    """
    Generate analytical eigenvalues for a ring graph Laplacian.
    
    For a ring graph with n nodes, the eigenvalues are:
    λ_k = 2 - 2*cos(2πk/n) for k = 0, 1, ..., n-1
    
    Args:
        n: Number of nodes
    
    Returns:
        Array of eigenvalues
    """
    k = np.arange(n)
    eigenvalues = 2 - 2 * np.cos(2 * np.pi * k / n)
    return np.sort(eigenvalues)


def check_vif_threshold(vif_series: pd.Series, threshold: float = 5.0) -> pd.Series:
    """
    Check which features exceed the VIF threshold.
    
    Args:
        vif_series: Series of VIF values
        threshold: VIF threshold for multicollinearity (default: 5.0)
    
    Returns:
        Boolean Series indicating features exceeding threshold
    """
    return vif_series > threshold
