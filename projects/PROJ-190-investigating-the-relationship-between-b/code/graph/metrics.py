import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set
import json
import pickle

from ..utils.logging import get_logger, info, warning, error, debug
from .thresholding import load_thresholded_graphs

logger = get_logger(__name__)

# Representative densities as per task T019 context
REPRESENTATIVE_DENSITIES = [0.15, 0.20, 0.25]

def calculate_global_efficiency(adjacency_matrix: np.ndarray) -> float:
    """
    Calculate Global Efficiency of a graph.
    
    Global Efficiency is defined as the average of the inverse shortest path lengths
    between all pairs of nodes.
    
    E_global = (1 / (N * (N-1))) * sum_{i != j} (1 / d_ij)
    
    Parameters
    ----------
    adjacency_matrix : np.ndarray
        Binary or weighted adjacency matrix (N x N). 
        For binary graphs, 1 indicates an edge, 0 no edge.
        For weighted graphs, weights represent connection strength.
        Diagonal elements are ignored.
        
    Returns
    -------
    float
        Global efficiency value. Returns 0.0 if the graph is disconnected 
        (infinite shortest path exists) or empty.
    """
    n_nodes = adjacency_matrix.shape[0]
    if n_nodes <= 1:
        return 0.0
    
    # Compute shortest path lengths using Dijkstra's algorithm (or Floyd-Warshall for small dense graphs)
    # Since we are dealing with potentially binary graphs, we treat non-zero entries as edges.
    # For efficiency with sparse graphs, we can use scipy.sparse.csgraph if available, 
    # but for simplicity and robustness here, we use numpy-based logic or scipy if needed.
    # Given the constraint to standard libs + existing deps, scipy is likely available via requirements.txt.
    
    try:
        from scipy.sparse.csgraph import shortest_path
        from scipy.sparse import csr_matrix
        
        # Convert to sparse if dense to save memory/time
        if adjacency_matrix.shape[0] > 500:
            graph_sparse = csr_matrix(adjacency_matrix)
            dist_matrix = shortest_path(graph_sparse, method='D', directed=False, unweighted=(np.all(adjacency_matrix == 0) or np.all(adjacency_matrix == 1)))
        else:
            # For small graphs, dense might be faster or similar
            dist_matrix = shortest_path(adjacency_matrix, method='D', directed=False, unweighted=(np.all(adjacency_matrix == 0) or np.all(adjacency_matrix == 1)))
        
    except ImportError:
        error("scipy is required for shortest path calculation. Install it via requirements.txt.")
        raise
    
    # Replace 0 distances (self-loops) with infinity for inverse calculation
    np.fill_diagonal(dist_matrix, np.inf)
    
    # Replace 0 distances (disconnected components) with infinity
    dist_matrix[dist_matrix == 0] = np.inf
    
    # Calculate inverse shortest paths
    inv_dist = 1.0 / dist_matrix
    
    # Sum over all i != j
    total_inv_dist = np.sum(inv_dist)
    
    # Normalize
    n_pairs = n_nodes * (n_nodes - 1)
    if n_pairs == 0:
        return 0.0
        
    global_eff = total_inv_dist / n_pairs
    
    return float(global_eff)

def calculate_efficiency_metrics(thresholded_graphs: Dict[str, Dict[str, np.ndarray]], 
                                 densities: Optional[List[float]] = None) -> Dict[str, Dict[str, float]]:
    """
    Calculate Global Efficiency for each subject and each density.
    
    Parameters
    ----------
    thresholded_graphs : Dict[str, Dict[str, np.ndarray]]
        Dictionary mapping density (string) to subject_id (string) to adjacency matrix.
        Structure: { "0.15": { "sub-001": matrix, ... }, "0.20": ... }
    densities : List[float], optional
        List of densities to compute metrics for. Defaults to REPRESENTATIVE_DENSITIES.
        
    Returns
    -------
    Dict[str, Dict[str, float]]
        Nested dictionary: { "density": { "subject_id": global_efficiency } }
    """
    if densities is None:
        densities = REPRESENTATIVE_DENSITIES
    
    results = {}
    
    for density in densities:
        density_str = f"{density:.2f}"
        if density_str not in thresholded_graphs:
            warning(f"Density {density_str} not found in thresholded graphs. Skipping.")
            continue
        
        results[density_str] = {}
        subject_graphs = thresholded_graphs[density_str]
        
        for subject_id, adj_matrix in subject_graphs.items():
            if adj_matrix is None or adj_matrix.size == 0:
                warning(f"Skipping subject {subject_id} at density {density_str}: empty or None matrix.")
                continue
                
            try:
                eff = calculate_global_efficiency(adj_matrix)
                results[density_str][subject_id] = eff
            except Exception as e:
                error(f"Failed to calculate global efficiency for {subject_id} at density {density_str}: {e}")
                # Do not crash the whole pipeline for one subject
                results[density_str][subject_id] = None
                
    return results

def main():
    """
    Main entry point to calculate Global Efficiency metrics.
    
    This function:
    1. Loads thresholded graphs from data/results/ (produced by T019).
    2. Iterates over representative densities.
    3. Calculates Global Efficiency for each subject at each density.
    4. Saves the results to data/results/efficiency_metrics_global.csv
    """
    logger.info("Starting Global Efficiency calculation (T020).")
    
    # Paths
    results_dir = Path("data/results")
    if not results_dir.exists():
        error("data/results directory not found. Run T019 first.")
        return
        
    # Load thresholded graphs
    # We assume T019 produced a pickle file or similar structure.
    # Based on T019 API: load_thresholded_graphs returns Dict[str, Dict[str, np.ndarray]]
    try:
        thresholded_graphs = load_thresholded_graphs(results_dir)
    except FileNotFoundError:
        error("Thresholded graphs file not found. Ensure T019 has run and saved data.")
        return
    except Exception as e:
        error(f"Error loading thresholded graphs: {e}")
        return
        
    if not thresholded_graphs:
        warning("No thresholded graphs loaded. Exiting.")
        return
        
    # Calculate metrics
    densities_to_process = [0.15, 0.20, 0.25]
    efficiency_results = calculate_efficiency_metrics(thresholded_graphs, densities_to_process)
    
    # Save results to CSV
    output_path = results_dir / "efficiency_metrics_global.csv"
    rows = []
    
    for density_str, subject_metrics in efficiency_results.items():
        for subject_id, eff_val in subject_metrics.items():
            rows.append({
                "subject_id": subject_id,
                "density": density_str,
                "global_efficiency": eff_val
            })
            
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        info(f"Global Efficiency metrics saved to {output_path}")
        
        # Log summary stats
        for density_str in densities_to_process:
            density_key = f"{density_str:.2f}"
            if density_key in efficiency_results:
                valid_vals = [v for v in efficiency_results[density_key].values() if v is not None]
                if valid_vals:
                    info(f"Density {density_str}: Mean Global Efficiency = {np.mean(valid_vals):.4f} (n={len(valid_vals)})")
    else:
        warning("No efficiency metrics were calculated. Check input data.")
        
    logger.info("Global Efficiency calculation completed.")

if __name__ == "__main__":
    main()
