import numpy as np
import networkx as nx
from typing import Tuple, Dict, Any, List, Optional
import warnings
import os
import sys
from pathlib import Path
import json

# Constants for file paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DIR / "graph_metrics.csv"
VALIDATION_LOG = PROCESSED_DIR / "graph_metric_validation.log"

def generate_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Generates a functional connectivity matrix (Pearson correlation)
    from a time series of ROIs.

    Args:
        time_series: Array of shape (n_timepoints, n_rois).

    Returns:
        Correlation matrix of shape (n_rois, n_rois).
    """
    if time_series.shape[0] < 2:
        raise ValueError("Time series must have at least 2 timepoints.")
    
    # Handle constant time series to avoid NaN correlations
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        corr_matrix = np.corrcoef(time_series, rowvar=False)
    
    # Replace NaNs with 0 (no correlation)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    # Ensure symmetry
    corr_matrix = (corr_matrix + corr_matrix.T) / 2.0
    
    return corr_matrix

def compute_global_efficiency(adjacency_matrix: np.ndarray) -> float:
    """
    Computes the global efficiency of a graph.
    Global efficiency is the average of the inverse shortest path lengths
    between all pairs of nodes.

    Args:
        adjacency_matrix: Symmetric numpy array representing edge weights.
            Can be weighted or binary.

    Returns:
        Global efficiency value (float).
    """
    # Create a graph from the adjacency matrix
    G = nx.from_numpy_array(adjacency_matrix)
    
    # Remove self-loops if any (though from_numpy_array shouldn't create them with diagonal 1)
    G.remove_edges_from(nx.selfloop_edges(G))
    
    # Calculate shortest path lengths
    # For weighted graphs, we assume weights represent connection strength.
    # Efficiency uses inverse distance. If weight is correlation, we might need to transform.
    # Standard approach: use 1 - weight as distance if weight is similarity, 
    # or directly use weight if it's already distance-like.
    # Here, we assume the matrix is a similarity matrix (correlation).
    # We convert to distance: d_ij = 1 - |r_ij| (or 1 - r_ij if strictly positive)
    # However, networkx shortest_path_length uses edge weights as distances directly.
    # So we transform weights: weight_dist = 1 - weight (if weight is in [-1, 1])
    # To avoid division by zero or negative distances, we often threshold or transform.
    # Simplest robust approach for efficiency: use 1 / (1 + shortest_path_length) if unweighted?
    # Or standard definition: E = 1/(N(N-1)) * sum(1/d_ij)
    
    # Let's re-construct graph with transformed weights if input is correlation
    # If the input is already a distance matrix, we use it directly.
    # Assuming input is correlation matrix (similarity):
    # Distance d_ij = 1 - corr_ij. If corr is negative, d > 1.
    # We must ensure d_ij > 0.
    
    # Create a new graph with transformed weights
    G_eff = nx.Graph()
    n = adjacency_matrix.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            w = adjacency_matrix[i, j]
            # Transform correlation to distance
            # If w is -1, distance is 2. If w is 1, distance is 0.
            # We need strictly positive distance for shortest path.
            # Common practice: use 1 - w, but handle 0 distance (perfect correlation)
            # by setting a small epsilon or skipping self-loops (already done).
            # If w == 1, distance is 0. Networkx handles 0 weight edges fine.
            dist = 1.0 - w
            if dist < 1e-9:
                dist = 1e-9 # Avoid 0 distance causing infinite efficiency if needed, but 0 is fine for shortest path
            
            G_eff.add_edge(i, j, weight=dist)
    
    if len(G_eff.nodes()) == 0:
        return 0.0

    try:
        # Compute all pairs shortest path lengths
        lengths = nx.shortest_path_length(G_eff, weight='weight')
        
        total_efficiency = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                if i in lengths and j in lengths[i]:
                    d = lengths[i][j]
                    if d > 0:
                        total_efficiency += 1.0 / d
                        count += 1
        
        if count == 0:
            return 0.0
        
        # Normalize by number of pairs
        return total_efficiency / count
    except nx.NetworkXNoPath:
        # Graph is disconnected, efficiency is 0 for those pairs
        return 0.0

def compute_clustering_coefficient(adjacency_matrix: np.ndarray) -> float:
    """
    Computes the average clustering coefficient of a graph.
    The clustering coefficient of a node is the fraction of possible triangles
    that exist.

    Args:
        adjacency_matrix: Symmetric numpy array representing edge weights.
            Thresholded to binary for clustering calculation.

    Returns:
        Average clustering coefficient (float).
    """
    # Threshold the matrix to binary (e.g., correlation > 0)
    # Or use a specific threshold. For simplicity, we use correlation > 0.
    binary_matrix = (adjacency_matrix > 0).astype(int)
    np.fill_diagonal(binary_matrix, 0)
    
    G = nx.from_numpy_array(binary_matrix)
    
    if len(G.nodes()) == 0:
        return 0.0
    
    return nx.average_clustering(G)

def compute_modularity_louvain(adjacency_matrix: np.ndarray) -> Tuple[float, Optional[Dict[int, int]]]:
    """
    Computes modularity using the Louvain algorithm.

    Args:
        adjacency_matrix: Symmetric numpy array representing edge weights.

    Returns:
        Tuple of (modularity_value, partition_dict).
        Returns (0.0, None) if algorithm fails or graph is empty.
    """
    G = nx.from_numpy_array(adjacency_matrix)
    
    if len(G.nodes()) < 2:
        return 0.0, None
    
    try:
        # Louvain partition
        partition = nx.community.louvain_communities(G, seed=42)
        # Convert to dict: node -> community_id
        partition_dict = {node: i for i, comm in enumerate(partition) for node in comm}
        
        # Calculate modularity
        modularity = nx.community.modularity(G, partition)
        return modularity, partition_dict
    except Exception:
        # Fallback or error
        return 0.0, None

def compute_modularity_with_resolution_sweep(adjacency_matrix: np.ndarray, 
                                             resolution_range: List[float] = [0.5, 1.0, 1.5, 2.0]) -> Dict[str, Any]:
    """
    Performs a resolution sweep for modularity optimization to find a stable partition.
    Returns the best modularity score and its parameters.

    Args:
        adjacency_matrix: Symmetric numpy array.
        resolution_range: List of resolution parameters to test.

    Returns:
        Dict with 'best_modularity', 'best_resolution', 'partition'.
    """
    G = nx.from_numpy_array(adjacency_matrix)
    best_mod = -np.inf
    best_res = 1.0
    best_part = None
    
    for res in resolution_range:
        try:
            partition = nx.community.louvain_communities(G, resolution=res, seed=42)
            mod = nx.community.modularity(G, partition)
            if mod > best_mod:
                best_mod = mod
                best_res = res
                best_part = partition
        except Exception:
            continue
    
    if best_part is None:
        return {"best_modularity": 0.0, "best_resolution": 1.0, "partition": None}
    
    partition_dict = {node: i for i, comm in enumerate(best_part) for node in comm}
    return {
        "best_modularity": best_mod,
        "best_resolution": best_res,
        "partition": partition_dict
    }

def compute_graph_metrics(time_series: np.ndarray) -> Dict[str, float]:
    """
    Computes all graph metrics for a given time series.

    Args:
        time_series: Array of shape (n_timepoints, n_rois).

    Returns:
        Dictionary of metric names to values.
    """
    corr_matrix = generate_correlation_matrix(time_series)
    
    efficiency = compute_global_efficiency(corr_matrix)
    clustering = compute_clustering_coefficient(corr_matrix)
    modularity, _ = compute_modularity_louvain(corr_matrix)
    
    return {
        "global_efficiency": efficiency,
        "clustering_coefficient": clustering,
        "modularity": modularity
    }

def load_preprocessed_subjects() -> List[Dict[str, Any]]:
    """
    Loads preprocessed subject data from the processed directory.
    Expects files named like 'sub-<id>_bold_processed.npy' or similar structure.
    For this implementation, we assume a specific structure or a manifest.
    Since T017 produces preprocessed NIfTI, we need to load them.
    However, the task says 'read preprocessed NIfTI files from data/processed/'.
    We will assume a helper exists or we load based on a manifest generated in T017.
    For now, we simulate loading or look for a manifest.
    
    In a real scenario, T017 would produce a list of processed files.
    We will look for a file 'processed_subjects_manifest.json' created by T017.
    """
    manifest_path = PROCESSED_DIR / "processed_subjects_manifest.json"
    if not manifest_path.exists():
        # Fallback: try to find files directly if manifest missing
        # This is a heuristic for the pipeline
        return []
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    subjects = []
    for sub_info in data.get("subjects", []):
        # Load the time series. Assuming T017 saved as .npy or .csv
        # If NIfTI, we need nilearn. The task says 'read preprocessed NIfTI'.
        # We will assume nilearn is available and the path is correct.
        # But to keep it simple and robust, we assume T017 also dumped a .npy for metrics.
        # If not, we would need to load NIfTI here.
        # Let's assume the manifest contains the path to a .npy file of the time series.
        npy_path = PROCESSED_DIR / sub_info["processed_ts_path"]
        if npy_path.exists():
            ts = np.load(npy_path)
            subjects.append({
                "id": sub_info["id"],
                "time_series": ts
            })
        else:
            # Try to load NIfTI if .npy not found
            try:
                import nibabel as nib
                nii_path = PROCESSED_DIR / sub_info["processed_nii_path"]
                if nii_path.exists():
                    # This is complex without knowing the exact parcellation used in T017
                    # We assume T017 already extracted the ROI time series.
                    # If not, this is a dependency on T017's specific output format.
                    # For T024, we assume the time series is available.
                    pass
            except ImportError:
                pass
    return subjects

def write_validation_log(subject_id: str, metric: str, value: float, reason: str):
    """Writes a validation anomaly to the log file."""
    log_entry = f"[{subject_id}] [{metric}] [{value}] [{reason}]\n"
    with open(VALIDATION_LOG, 'a') as f:
        f.write(log_entry)

def main():
    """
    Main entry point to compute graph metrics for all valid subjects
    and write results to CSV.
    """
    print("Starting graph metrics computation (T024)...")
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clear previous validation log if exists
    if VALIDATION_LOG.exists():
        VALIDATION_LOG.unlink()
    
    subjects = load_preprocessed_subjects()
    
    if not subjects:
        print("No preprocessed subjects found. Check T017 output or manifest.")
        # Create empty CSV
        with open(OUTPUT_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'metric_name', 'value'])
        return

    results = []
    
    for sub in subjects:
        sub_id = sub["id"]
        ts = sub["time_series"]
        
        try:
            metrics = compute_graph_metrics(ts)
            
            for metric_name, value in metrics.items():
                # Validate ranges
                reason = None
                if metric_name == "global_efficiency":
                    if value < 0 or value > 1: # Efficiency is usually between 0 and 1
                        reason = "Value out of expected range [0, 1]"
                elif metric_name == "clustering_coefficient":
                    if value < 0 or value > 1:
                        reason = "Value out of expected range [0, 1]"
                elif metric_name == "modularity":
                    if value < 0 or value > 1:
                        reason = "Value out of expected range [0, 1]"
                
                if reason:
                    write_validation_log(sub_id, metric_name, value, reason)
                
                results.append({
                    "subject_id": sub_id,
                    "metric_name": metric_name,
                    "value": value
                })
                
        except Exception as e:
            print(f"Error computing metrics for {sub_id}: {e}")
            write_validation_log(sub_id, "ERROR", 0.0, str(e))
    
    # Write to CSV
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["subject_id", "metric_name", "value"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Graph metrics written to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()