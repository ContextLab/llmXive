"""
Analysis utilities for brain network metrics.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import logging
from utils.io import save_parquet, load_parquet, save_json, load_json, ensure_dir

logger = logging.getLogger(__name__)

def regress_confounds(time_series: np.array, confounds: np.array) -> np.array:
    """Regress out FD/DVARS confounds from the time series."""
    # Simple linear regression using least squares
    X = np.column_stack([confounds, np.ones(confounds.shape[0])])
    betas = np.linalg.lstsq(X, time_series, rcond=None)[0]
    residuals = time_series - X @ betas
    return residuals

def compute_static_connectivity(time_series: np.array) -> np.array:
    """Compute static functional connectivity matrix (Pearson correlation)."""
    return np.corrcoef(time_series.T)

def compute_static_metrics(matrix: np.array, network_map: Dict[str, List[int]]) -> Dict[str, float]:
    """Derive static network metrics for specific networks."""
    import networkx as nx

    G = nx.from_numpy_array(matrix)
    metrics = {}

    # Global efficiency
    metrics["global_efficiency"] = nx.global_efficiency(G)

    # Modularity (using the greedy modularity communities as a proxy)
    communities = nx.algorithms.community.greedy_modularity_communities(G)
    modularity = nx.algorithms.community.modularity(G, communities)
    metrics["modularity_Q"] = modularity

    # Within‑module degree for each network in network_map
    for net_name, roi_indices in network_map.items():
        subgraph = G.subgraph(roi_indices)
        degrees = dict(subgraph.degree())
        mean_degree = np.mean(list(degrees.values()))
        metrics[f"{net_name}_within_degree"] = mean_degree

    return metrics

def compute_dynamic_connectivity(time_series: np.array, window_size: int, step: int) -> List[np.array]:
    """Compute sliding-window dynamic connectivity matrices."""
    n_timepoints = time_series.shape[0]
    windows = []
    for start in range(0, n_timepoints - window_size + 1, step):
        window_ts = time_series[start:start + window_size, :]
        corr = np.corrcoef(window_ts.T)
        windows.append(corr)
    return windows

def compute_reconfiguration_rate(dynamic_matrices: List[np.array]) -> float:
    """Calculate the dynamic reconfiguration rate from sliding-window matrices."""
    diffs = []
    for i in range(1, len(dynamic_matrices)):
        diff = np.abs(dynamic_matrices[i] - dynamic_matrices[i - 1]).mean()
        diffs.append(diff)
    return float(np.mean(diffs)) if diffs else 0.0

def compute_icc(metrics: List[float]) -> float:
    """Calculate Intraclass Correlation Coefficient (ICC) for a list of metrics."""
    # Simplified ICC(3,1) implementation
    n = len(metrics)
    if n < 2:
        return 0.0
    mean_total = np.mean(metrics)
    ms_between = np.var(metrics, ddof=1) * n
    ms_within = np.mean([(m - mean_total) ** 2 for m in metrics])
    icc = (ms_between - ms_within) / (ms_between + (n - 1) * ms_within)
    return float(icc)

def run_sensitivity_analysis(time_series: np.array, window_sizes: List[int]) -> Dict[str, Any]:
    """Run sensitivity analysis with multiple window sizes to assess stability of dynamic metrics."""
    reconfig_rates = {}
    for ws in window_sizes:
        dyn = compute_dynamic_connectivity(time_series, ws, step=5)
        reconfig_rates[ws] = compute_reconfiguration_rate(dyn)

    icc = compute_icc(list(reconfig_rates.values()))

    stability_assessment = "stable" if icc >= 0.7 else "unstable"

    return {
        "window_sizes": window_sizes,
        "reconfiguration_rates": reconfig_rates,
        "icc": icc,
        "stability_assessment": stability_assessment,
    }

def main():
    """Demonstration entry point."""
    # Generate synthetic data for illustration
    rng = np.random.default_rng(42)
    ts = rng.normal(size=(200, 400))
    result = run_sensitivity_analysis(ts, [20, 30, 40])
    print(result)

if __name__ == "__main__":
    main()
