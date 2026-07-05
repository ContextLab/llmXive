"""
code/clustering.py
Implements Leiden clustering engine and fidelity metrics (ARI, NMI).
Dependencies: T006 (preprocess), T004 (config), leidenalg, igraph, scikit-learn, scanpy.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
import scanpy as sc
import leidenalg
import igraph as ig
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

# Import from project config
from config import get_accession_seed, set_global_seed, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_preprocessed_data(accession: str, data_dir: Path) -> Tuple[sc.AnnData, str]:
    """
    Load preprocessed AnnData object from disk.
    Expects file at: data_dir/processed/{accession}_preprocessed.h5ad
    """
    file_path = data_dir / "processed" / f"{accession}_preprocessed.h5ad"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Preprocessed data not found for {accession} at {file_path}. "
            "Ensure T006 (preprocess) has been run."
        )
    
    logger.info(f"Loading preprocessed data from {file_path}")
    adata = sc.read_h5ad(file_path)
    
    # Ensure ground truth labels exist if available
    if 'ground_truth' not in adata.obs.columns:
        logger.warning(f"No 'ground_truth' column found in {accession} data. Fidelity metrics will be skipped.")
    
    return adata, str(file_path)

def run_leiden_clustering(
    adata: sc.AnnData, 
    resolution: float, 
    random_state: int
) -> np.ndarray:
    """
    Run Leiden clustering on the AnnData object.
    
    Args:
        adata: Preprocessed AnnData object (expects 'X' or 'obsm['pca']' for neighbors).
        resolution: Leiden resolution parameter.
        random_state: Seed for reproducibility.
        
    Returns:
        Numpy array of cluster assignments.
    """
    logger.info(f"Running Leiden clustering with resolution={resolution}, seed={random_state}")
    
    # Set global seed for reproducibility within this function context
    set_global_seed(random_state)
    
    # Build neighbor graph if not already present
    if 'neighbors' not in adata.uns:
        logger.info("Building neighbor graph for Leiden clustering...")
        # Use PCA if available, otherwise raw data (log-transformed)
        if 'pca' in adata.obsm:
            sc.pp.neighbors(adata, use_rep='pca', random_state=random_state)
        else:
            sc.pp.neighbors(adata, random_state=random_state)
    
    # Run Leiden
    try:
        sc.tl.leiden(adata, resolution=resolution, random_state=random_state)
        clusters = adata.obs['leiden'].astype(int).to_numpy()
        logger.info(f"Leiden clustering complete. Found {len(np.unique(clusters))} clusters.")
        return clusters
    except Exception as e:
        logger.error(f"Leiden clustering failed: {e}")
        raise

def calculate_fidelity_metrics(
    predicted_labels: np.ndarray,
    true_labels: np.ndarray
) -> Dict[str, float]:
    """
    Calculate Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI).
    
    Args:
        predicted_labels: Cluster assignments from Leiden.
        true_labels: Ground truth labels.
        
    Returns:
        Dictionary with ARI and NMI scores.
    """
    if true_labels is None or len(true_labels) == 0:
        logger.warning("Ground truth labels missing. Returning None for metrics.")
        return {"ari": None, "nmi": None}
    
    try:
        ari = adjusted_rand_score(true_labels, predicted_labels)
        nmi = normalized_mutual_info_score(true_labels, predicted_labels)
        logger.info(f"Fidelity calculated: ARI={ari:.4f}, NMI={nmi:.4f}")
        return {"ari": float(ari), "nmi": float(nmi)}
    except Exception as e:
        logger.error(f"Error calculating fidelity metrics: {e}")
        return {"ari": None, "nmi": None}

def process_accession(
    accession: str,
    resolution: float,
    data_dir: Path,
    results_dir: Path
) -> Dict[str, Any]:
    """
    Main entry point for clustering and fidelity calculation for a single accession.
    
    Args:
        accession: GEO accession ID (e.g., GSE131907).
        resolution: Leiden resolution parameter.
        data_dir: Root directory for data (contains 'processed' subdir).
        results_dir: Root directory for results (will write 'clustering' subdir).
        
    Returns:
        Dictionary containing clustering results and metrics.
    """
    logger.info(f"Processing accession: {accession} with resolution {resolution}")
    
    # Load data
    adata, _ = load_preprocessed_data(accession, data_dir)
    
    # Get seed for reproducibility
    seed = get_accession_seed(accession)
    set_global_seed(seed)
    
    # Run clustering
    clusters = run_leiden_clustering(adata, resolution, seed)
    
    # Prepare ground truth
    true_labels = None
    if 'ground_truth' in adata.obs.columns:
        true_labels = adata.obs['ground_truth'].to_numpy()
        # Handle non-numeric labels if necessary
        if not np.issubdtype(true_labels.dtype, np.number):
            # Map unique labels to integers
            unique_labels = np.unique(true_labels)
            label_map = {label: i for i, label in enumerate(unique_labels)}
            true_labels = np.array([label_map[l] for l in true_labels])
    
    # Calculate fidelity
    metrics = calculate_fidelity_metrics(clusters, true_labels)
    
    # Save results
    output_dir = results_dir / "clustering"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save cluster assignments
    cluster_file = output_dir / f"{accession}_clusters.json"
    result_data = {
        "accession": accession,
        "resolution": resolution,
        "n_clusters": int(len(np.unique(clusters))),
        "metrics": metrics,
        "cluster_assignments": clusters.tolist()
    }
    
    with open(cluster_file, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    logger.info(f"Results saved to {cluster_file}")
    
    return result_data

def main():
    """
    Command-line entry point for clustering.
    Usage: python code/clustering.py <accession> <resolution>
    """
    if len(sys.argv) < 3:
        print("Usage: python code/clustering.py <accession> <resolution>")
        print("Example: python code/clustering.py GSE131907 0.5")
        sys.exit(1)
    
    accession = sys.argv[1]
    try:
        resolution = float(sys.argv[2])
    except ValueError:
        print(f"Error: Resolution must be a number, got {sys.argv[2]}")
        sys.exit(1)
    
    # Initialize paths
    config = Config()
    data_dir = Path(config.data_dir)
    results_dir = Path(config.results_dir)
    
    try:
        result = process_accession(accession, resolution, data_dir, results_dir)
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error processing {accession}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
