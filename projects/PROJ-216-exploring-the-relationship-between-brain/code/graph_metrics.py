import os
import sys
import json
import logging
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Attempt to import community (python-louvain) for modularity
try:
    import community
    HAS_COMMUNITY = True
except ImportError:
    HAS_COMMUNITY = False
    logging.warning("community (python-louvain) package not found. Modularity calculations will fail unless dependency is installed.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_preprocessed_subjects(input_dir: str) -> List[Dict[str, Any]]:
    """
    Scans the input directory for preprocessed subject data (e.g., time series files).
    Returns a list of dicts with subject_id and path to the time series.
    """
    subjects = []
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory {input_dir} does not exist.")
    
    # Assuming preprocessed data is stored as .npy or .csv time series per subject
    # or a specific naming convention like subj_XXX_time_series.npy
    for f in input_path.iterdir():
        if f.suffix in ['.npy', '.csv'] and 'time_series' in f.name.lower():
            # Infer subject ID from filename or a sidecar JSON if available
            # For this implementation, we assume the filename format: subj_XXX_time_series.npy
            subj_id = f.stem.replace('_time_series', '')
            subjects.append({
                "subject_id": subj_id,
                "time_series_path": str(f)
            })
    return subjects

def scan_preprocessed_directory(input_dir: str) -> List[str]:
    """
    Helper to scan directory for valid subject files.
    """
    return [f.name for f in Path(input_dir).iterdir() if f.is_file() and f.suffix in ['.npy', '.csv']]

def get_schaefer_atlas(atlas_name: str = "Schaefer200") -> np.ndarray:
    """
    Loads or fetches the Schaefer atlas parcellation mask.
    Returns a 1D array of labels corresponding to voxels/regions.
    In a real pipeline, this would fetch from nilearn or a local path.
    For this task, we assume the atlas is available or generate a valid placeholder
    if strictly necessary for the graph logic (though the task demands real data).
    
    Since T022a handles acquiring the atlas, we expect it to be in data/external.
    """
    # Check for real atlas file first
    possible_paths = [
        Path("data/external/Schaefer200_7Networks.nii.gz"),
        Path("data/external/Schaefer200_7Networks_labels.npy")
    ]
    
    for p in possible_paths:
        if p.exists():
            logger.info(f"Loading Schaefer atlas from {p}")
            if p.suffix == '.npy':
                return np.load(p)
            elif p.suffix == '.gz' or p.suffix == '.nii':
                # In a full pipeline, use nilearn to load and average time series
                # Here we return a dummy label array if the file exists but we can't load it easily
                # In a real scenario, we would raise an error if nilearn is missing
                try:
                    from nilearn import image, masking
                    # Placeholder logic: assume we have a way to get labels
                    # This part is dependent on the full preprocessing pipeline
                    raise NotImplementedError("Full atlas loading requires nilearn and preprocessing setup.")
                except ImportError:
                    raise RuntimeError("nilearn required to load NIfTI atlas.")
    
    # If not found, we must NOT generate synthetic data per constraints.
    # However, for the purpose of this specific task (T025) which focuses on the
    # modularity algorithm logic, we assume the time series (N x Regions) is passed
    # directly or the atlas is already loaded by the caller.
    # If this function is called and no real atlas exists, we raise.
    raise FileNotFoundError(f"Schaefer atlas not found at expected paths. Run T022a.")

def generate_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Computes the Pearson correlation matrix from a time series array.
    time_series shape: (time_points, regions)
    Returns: (regions, regions) symmetric correlation matrix.
    """
    if time_series.ndim != 2:
        raise ValueError("Time series must be 2D (time, regions).")
    
    # Compute correlation
    corr_matrix = np.corrcoef(time_series.T)
    
    # Handle NaNs (if constant time series exist)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    # Ensure symmetry
    corr_matrix = (corr_matrix + corr_matrix.T) / 2.0
    np.fill_diagonal(corr_matrix, 1.0)
    
    return corr_matrix

def compute_global_efficiency(corr_matrix: np.ndarray) -> float:
    """
    Computes global efficiency using NetworkX.
    """
    if not HAS_COMMUNITY:
         # We still need networkx for efficiency, but modularity needs community
         pass
    
    G = nx.from_numpy_array(corr_matrix)
    # Global efficiency is 1/L where L is average shortest path length
    # For weighted graphs, we use weights. Correlation can be negative,
    # but for efficiency we often use absolute value or threshold.
    # Standard approach: use 1 - |r| as distance or just |r| as weight.
    # Here we use 1 - r as distance (assuming r > 0).
    # If negative correlations exist, we might take absolute value.
    # Simple approach: convert correlation to distance: d = 1 - r
    # But we must handle r=1 -> d=0.
    
    # Reconstruct graph with weights = 1 - correlation (distance)
    # Or use correlation as weight and use nx.global_efficiency which handles weights?
    # nx.global_efficiency uses edge weights as distances.
    # So we need to convert correlation to distance.
    
    # Let's create a graph where weight = 1 - r (if r > 0)
    # But for simplicity in this snippet, we assume we use the correlation as weight
    # and nx.global_efficiency will compute sum(1/d_ij) / (n*(n-1))
    # Actually, nx.global_efficiency expects weights to be distances.
    # So we pass 1 - r as weight.
    
    # Create a new graph for distance
    G_dist = nx.Graph()
    n = corr_matrix.shape[0]
    for i in range(n):
        for j in range(i+1, n):
            w = corr_matrix[i, j]
            if w > 0: # Only positive correlations as edges
                dist = 1.0 - w
                if dist == 0: dist = 0.001 # Avoid division by zero
                G_dist.add_edge(i, j, weight=dist)
    
    try:
        eff = nx.global_efficiency(G_dist)
    except nx.NetworkXError:
        eff = 0.0
    return float(eff)

def compute_clustering_coefficient(corr_matrix: np.ndarray) -> float:
    """
    Computes the average clustering coefficient.
    """
    G = nx.from_numpy_array(corr_matrix)
    # Convert to unweighted for clustering coefficient (standard)
    # Or use weighted version? nx.clustering supports weight.
    # We'll use unweighted for standard clustering coefficient.
    G_unw = nx.Graph()
    n = corr_matrix.shape[0]
    for i in range(n):
        for j in range(i+1, n):
            if corr_matrix[i, j] > 0.2: # Threshold
                G_unw.add_edge(i, j)
    
    if len(G_unw.nodes) == 0:
        return 0.0
    return float(nx.average_clustering(G_unw))

def compute_modularity_louvain(corr_matrix: np.ndarray, resolution: float = 1.0) -> float:
    """
    Computes modularity using the Louvain algorithm (python-louvain).
    Resolution parameter controls the size of communities.
    """
    if not HAS_COMMUNITY:
        raise RuntimeError("The 'community' (python-louvain) package is required for modularity calculation.")
    
    # Create a graph from the correlation matrix
    G = nx.from_numpy_array(corr_matrix)
    
    # Remove negative edges for Louvain (it typically assumes positive weights)
    # Or convert to positive weights. We'll keep only positive correlations.
    G_pos = nx.Graph()
    n = corr_matrix.shape[0]
    for i in range(n):
        for j in range(i+1, n):
            w = corr_matrix[i, j]
            if w > 0:
                G_pos.add_edge(i, j, weight=w)
    
    if G_pos.number_of_edges() == 0:
        return 0.0
    
    try:
        partition = community.best_partition(G_pos, resolution=resolution)
        modularity = community.modularity(partition, G_pos, resolution=resolution)
        return float(modularity)
    except Exception as e:
        logger.error(f"Error computing modularity with resolution {resolution}: {e}")
        raise

def compute_modularity_with_resolution_sweep(corr_matrix: np.ndarray, 
                                             min_res: float = 0.5, 
                                             max_res: float = 2.0, 
                                             steps: int = 10) -> Tuple[float, float]:
    """
    Implements modularity calculation with a resolution parameter sweep fallback.
    If the default resolution (1.0) fails or yields suboptimal results, it sweeps
    across a range.
    
    Returns: (best_modularity, best_resolution)
    """
    if not HAS_COMMUNITY:
        raise RuntimeError("The 'community' (python-louvain) package is required for modularity calculation.")
    
    best_mod = -1.0
    best_res = 1.0
    
    # Define the resolution range
    resolutions = np.linspace(min_res, max_res, steps)
    
    for res in resolutions:
        try:
            mod = compute_modularity_louvain(corr_matrix, resolution=res)
            if mod > best_mod:
                best_mod = mod
                best_res = res
        except Exception as e:
            logger.warning(f"Failed at resolution {res}: {e}")
            continue
    
    if best_mod < 0:
        # If all failed, return 0
        return 0.0, 1.0
    
    return best_mod, best_res

def compute_graph_metrics(subject_data: Dict[str, Any], corr_matrix: np.ndarray) -> Dict[str, float]:
    """
    Computes all graph metrics for a subject.
    """
    metrics = {}
    
    # Global Efficiency
    try:
        metrics['global_efficiency'] = compute_global_efficiency(corr_matrix)
    except Exception as e:
        logger.error(f"Failed to compute global efficiency: {e}")
        metrics['global_efficiency'] = 0.0
    
    # Clustering Coefficient
    try:
        metrics['clustering_coefficient'] = compute_clustering_coefficient(corr_matrix)
    except Exception as e:
        logger.error(f"Failed to compute clustering coefficient: {e}")
        metrics['clustering_coefficient'] = 0.0
    
    # Modularity with Resolution Sweep (T025 implementation)
    try:
        mod_val, res_val = compute_modularity_with_resolution_sweep(corr_matrix)
        metrics['modularity_louvain'] = mod_val
        metrics['modularity_resolution'] = res_val
    except Exception as e:
        logger.error(f"Failed to compute modularity: {e}")
        metrics['modularity_louvain'] = 0.0
        metrics['modularity_resolution'] = 1.0
    
    return metrics

def write_validation_log(anomalies: List[Dict[str, Any]], log_path: str):
    """
    Writes validation anomalies to a log file.
    """
    with open(log_path, 'w') as f:
        json.dump(anomalies, f, indent=2)

def main():
    """
    Main entry point for the graph metrics pipeline.
    Expects:
      --input: directory with preprocessed time series
      --atlas: name of atlas (e.g., Schaefer200)
      --output: output CSV path
    """
    parser = argparse.ArgumentParser(description="Compute graph metrics from preprocessed fMRI data.")
    parser.add_argument("--input", required=True, help="Directory containing preprocessed time series")
    parser.add_argument("--atlas", default="Schaefer200", help="Atlas name")
    parser.add_argument("--output", required=True, help="Output CSV path")
    args = parser.parse_args()
    
    # 1. Load subjects
    subjects = load_preprocessed_subjects(args.input)
    if not subjects:
        logger.error("No subjects found in input directory.")
        sys.exit(1)
    
    # 2. Load Atlas (if needed for parcellation, but here we assume time series are already parcellated)
    # If the input is voxel-wise, we would need to apply the atlas here.
    # Assuming input is already parcellated time series (N_regions, T).
    
    all_metrics = []
    
    for subj in subjects:
        logger.info(f"Processing subject: {subj['subject_id']}")
        try:
            # Load time series
            ts_path = subj['time_series_path']
            if ts_path.endswith('.npy'):
                ts = np.load(ts_path)
            elif ts_path.endswith('.csv'):
                ts = np.loadtxt(ts_path, delimiter=',')
            else:
                continue
            
            # Generate Correlation Matrix
            corr_mat = generate_correlation_matrix(ts)
            
            # Compute Metrics
            metrics = compute_graph_metrics(subj, corr_mat)
            metrics['subject_id'] = subj['subject_id']
            all_metrics.append(metrics)
            
        except Exception as e:
            logger.error(f"Error processing subject {subj['subject_id']}: {e}")
            continue
    
    # 3. Write Output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if all_metrics:
        keys = all_metrics[0].keys()
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_metrics)
        logger.info(f"Metrics written to {output_path}")
    else:
        logger.warning("No metrics computed. Output file not created.")

if __name__ == "__main__":
    main()
