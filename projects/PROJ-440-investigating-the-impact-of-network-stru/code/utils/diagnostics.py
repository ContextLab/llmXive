import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from scipy import stats
from typing import Dict, List, Tuple, Optional, Union

def calculate_vif(features: pd.DataFrame) -> pd.Series:
    """Calculate Variance Inflation Factor for each feature."""
    vif_data = pd.Series()
    for i, col in enumerate(features.columns):
        X = features.drop(columns=[col])
        y = features[col]
        try:
            model = pd.DataFrame(y).join(X)
            # Simple linear regression to get R^2
            # Note: In a real scenario, we might use sklearn or statsmodels
            # Here we use a simplified approach for the demo
            if X.shape[1] == 0:
                vif_data[col] = 1.0
                continue
            # Use correlation matrix for VIF approximation if needed, 
            # but standard VIF requires regression.
            # Implementing full VIF calculation:
            from sklearn.linear_model import LinearRegression
            lr = LinearRegression()
            lr.fit(X, y)
            r_squared = lr.score(X, y)
            vif = 1.0 / (1.0 - r_squared)
            vif_data[col] = vif
        except Exception:
            vif_data[col] = np.inf
    return vif_data

def plot_convergence(decay_rates: List[float], output_path: str = "data/analysis/convergence_plot.png") -> None:
    """Plot the convergence of decay rates."""
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(decay_rates)), decay_rates, marker='o')
    plt.xlabel("Iteration")
    plt.ylabel("Decay Rate")
    plt.title("Convergence of Decay Rates")
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()

def generate_ring_analytical_eigenvalues(n: int) -> np.ndarray:
    """Generate analytical eigenvalues for a ring graph Laplacian."""
    k = np.arange(n)
    return 2 - 2 * np.cos(2 * np.pi * k / n)

def validate_laplacian_eigenvalues(graph: nx.Graph, tol: float = 1e-6) -> Tuple[bool, float]:
    """Validate Laplacian eigenvalues against analytical solution for a ring graph."""
    if not nx.is_cycle_graph(graph):
        return False, 0.0
    
    n = graph.number_of_nodes()
    laplacian = nx.laplacian_matrix(graph).toarray()
    eigenvalues = np.linalg.eigvalsh(laplacian)
    analytical = generate_ring_analytical_eigenvalues(n)
    
    max_diff = np.max(np.abs(np.sort(eigenvalues) - np.sort(analytical)))
    return max_diff < tol, max_diff

def check_vif_threshold(vif_values: pd.Series, threshold: float = 5.0) -> List[str]:
    """Check which features exceed the VIF threshold."""
    return [col for col, vif in vif_values.items() if vif > threshold]
