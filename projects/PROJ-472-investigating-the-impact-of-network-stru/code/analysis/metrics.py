"""
Compute node-wise degree, mean clustering coefficient, and rich-club coefficient.
Uses NetworkX for graph metrics and BCTpy for rich-club analysis.
"""
import os
import json
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import project utilities and config
from config import get_data_root, ensure_directories
from data.store import load_connectome_matrix
from utils.logger import get_logger

logger = get_logger(__name__)


def compute_degree_centrality(adj_matrix: np.ndarray) -> np.ndarray:
    """
    Compute node-wise degree centrality.
    
    Args:
        adj_matrix: Square adjacency matrix (N x N).
        
    Returns:
        Array of degree centrality values for each node (length N).
    """
    n = adj_matrix.shape[0]
    # Normalize by max possible degree (n-1)
    degree_sum = np.sum(adj_matrix, axis=1)
    if n > 1:
        degree_centrality = degree_sum / (n - 1)
    else:
        degree_centrality = degree_sum
    return degree_centrality


def compute_clustering_coefficient(adj_matrix: np.ndarray) -> float:
    """
    Compute the mean clustering coefficient of the graph.
    
    Args:
        adj_matrix: Square adjacency matrix (N x N).
        
    Returns:
        Mean clustering coefficient (scalar).
    """
    G = nx.from_numpy_array(adj_matrix)
    cc = nx.average_clustering(G)
    return float(cc)


def compute_rich_club_coefficient(adj_matrix: np.ndarray, 
                                  normalized: bool = True,
                                  k_range: Optional[List[int]] = None) -> Tuple[Dict[int, float], Dict[int, float]]:
    """
    Compute the rich-club coefficient (and optionally normalized) for the graph.
    
    Args:
        adj_matrix: Square adjacency matrix (N x N).
        normalized: If True, compute normalized rich-club coefficient using BCTpy.
        k_range: List of degrees to evaluate. If None, uses default BCTpy range.
        
    Returns:
        Tuple of (raw_rich_club, normalized_rich_club) as dicts mapping degree k to coefficient.
        If normalized=False, returns (raw, None).
    """
    try:
        import bct
    except ImportError:
        logger.error("BCTpy not installed. Please install it to compute rich-club coefficients.")
        raise

    # BCT expects a 2D numpy array
    # Ensure binary for rich-club calculation if thresholding is not applied here
    # For this task, we assume the input is the weighted matrix but BCT's rc_exp requires binary or weighted
    # We use the weighted version if possible, or convert to binary based on non-zero
    
    # BCT's rich_club_coefficient function (rc)
    # rc = bct.rich_club_coefficient(W, k) -> returns dict
    
    # We need to iterate over k values or let BCT handle it. 
    # BCT's rc function returns a dictionary of k: coeff.
    
    # To get normalized, we use bct.rich_club_coefficient with normalized=True if supported,
    # or compute manually against random graphs. BCTpy has `rich_club_coefficient` which can return normalized.
    # However, standard BCT `rc` returns raw. Normalized is `rc_norm = rc / rc_random`.
    # Let's use the dedicated function if available or implement the logic.
    
    # Using BCTpy's rich_club_coefficient which returns raw
    # Note: BCTpy might expect a binary matrix for some versions, but `rc` usually handles weighted by thresholding.
    # We will pass the matrix directly.
    
    # To ensure compatibility, we convert to binary (non-zero = 1) for the structural connectome context
    # as rich-club is often defined on binary topology in neuroscience literature, 
    # though weighted exists. We'll compute on the binary version of the input.
    binary_matrix = (adj_matrix > 0).astype(float)
    
    # Compute raw rich-club
    # BCTpy returns a dict {k: value}
    rc_raw = bct.rich_club_coefficient(binary_matrix)
    
    if normalized:
        # Compute normalized rich-club
        # We need to generate random graphs with same degree distribution
        # BCTpy has `rich_club_coefficient` with normalized argument in some versions, 
        # but standard is to compute manually or use `rc_exp`
        # Let's use the standard approach: rc / rc_random
        # BCTpy `rich_club_coefficient` doesn't take normalized flag directly in all versions.
        # We'll compute rc_random using `rich_club_coefficient` on random graphs.
        
        # Generate 100 random graphs with same degree sequence
        # BCTpy function: `randomize_graph` (binary) or `rewiring`
        # We use `rewiring` to preserve degree distribution
        
        n_random = 100
        rc_random_sum = {}
        
        for _ in range(n_random):
            # Rewire the graph to preserve degree distribution
            random_matrix = bct.rewire_edges(binary_matrix, 1.0) # Rewire 100%
            rc_rand = bct.rich_club_coefficient(random_matrix)
            
            for k, val in rc_rand.items():
                rc_random_sum[k] = rc_random_sum.get(k, 0) + val
        
        rc_normalized = {}
        for k, val in rc_raw.items():
            avg_rand = rc_random_sum[k] / n_random
            if avg_rand > 0:
                rc_normalized[k] = val / avg_rand
            else:
                rc_normalized[k] = 0.0
                
        return rc_raw, rc_normalized
    else:
        return rc_raw, None


def run_metrics_pipeline(subject_id: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run all metrics for a single subject and return results.
    
    Args:
        subject_id: The subject identifier.
        output_dir: Directory to save results. If None, uses default data/results path.
        
    Returns:
        Dictionary containing computed metrics.
    """
    if output_dir is None:
        data_root = get_data_root()
        output_dir = data_root / "results"
    
    ensure_directories([output_dir])
    
    # Load connectome
    try:
        adj_matrix = load_connectome_matrix(subject_id)
    except FileNotFoundError as e:
        logger.error(f"Connectome not found for {subject_id}: {e}")
        return {"subject_id": subject_id, "error": str(e)}
    
    if adj_matrix is None:
        return {"subject_id": subject_id, "error": "Failed to load connectome"}
    
    # Compute metrics
    degree_centrality = compute_degree_centrality(adj_matrix)
    mean_clustering = compute_clustering_coefficient(adj_matrix)
    rc_raw, rc_norm = compute_rich_club_coefficient(adj_matrix, normalized=True)
    
    # Prepare results
    results = {
        "subject_id": subject_id,
        "mean_degree_centrality": float(np.mean(degree_centrality)),
        "degree_centrality_vector": degree_centrality.tolist(),
        "mean_clustering_coefficient": mean_clustering,
        "rich_club_coefficient_raw": rc_raw,
        "rich_club_coefficient_normalized": rc_norm
    }
    
    # Save results to JSON
    output_path = output_dir / f"metrics_{subject_id}.json"
    with open(output_path, 'w') as f:
        # Convert numpy types and complex structures to serializable formats
        def default_serializer(obj):
            if isinstance(obj, dict):
                return {str(k): v for k, v in obj.items()}
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        json.dump(results, f, indent=2, default=default_serializer)
    
    logger.info(f"Metrics computed and saved for {subject_id} to {output_path}")
    return results


def main():
    """Main entry point to run metrics for all available subjects."""
    data_root = get_data_root()
    processed_dir = data_root / "processed"
    output_dir = data_root / "results"
    
    ensure_directories([output_dir])
    
    # Find all available connectome files
    # Assuming files are named connectome_{subject_id}.npy or similar
    # We rely on the store module's pattern or list files in processed
    
    subject_files = list(processed_dir.glob("connectome_*.npy"))
    
    if not subject_files:
        logger.warning("No connectome files found in data/processed/. Skipping metrics computation.")
        return
    
    all_results = []
    
    for file_path in subject_files:
        # Extract subject_id from filename: connectome_sub-001.npy -> sub-001
        stem = file_path.stem
        subject_id = stem.replace("connectome_", "")
        
        logger.info(f"Processing {subject_id}...")
        try:
            result = run_metrics_pipeline(subject_id, output_dir)
            if "error" not in result:
                all_results.append(result)
        except Exception as e:
            logger.error(f"Error processing {subject_id}: {e}")
            all_results.append({"subject_id": subject_id, "error": str(e)})
    
    # Aggregate results to CSV (flattened for main metrics)
    if all_results:
        rows = []
        for res in all_results:
            if "error" in res:
                rows.append({
                    "subject_id": res["subject_id"],
                    "status": "failed",
                    "error": res["error"]
                })
            else:
                rows.append({
                    "subject_id": res["subject_id"],
                    "mean_degree_centrality": res["mean_degree_centrality"],
                    "mean_clustering_coefficient": res["mean_clustering_coefficient"],
                    "status": "success"
                })
        
        df = pd.DataFrame(rows)
        csv_path = output_dir / "metrics_summary.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Summary saved to {csv_path}")


if __name__ == "__main__":
    main()
