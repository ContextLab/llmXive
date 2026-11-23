import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from sklearn.cluster import DBSCAN
from scipy.stats import mannwhitneyu

from src.config import get_project_root, load_config, get_data_processed_path

logger = logging.getLogger(__name__)

def load_umap_embedding() -> pd.DataFrame:
    """Load the UMAP embedding from the processed data directory."""
    file_path = get_data_processed_path() / "umap_embedding.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"UMAP embedding not found at {file_path}")
    return pd.read_csv(file_path)

def load_resistance_labels() -> pd.Series:
    """Load resistance labels associated with the compounds in the embedding."""
    # Assuming the resistance labels are stored in a CSV with an 'InChIKey' column
    # and a 'resistance_label' or similar column.
    # Based on T015/T025 context, we expect a merged file or a specific label file.
    # We will look for 'resistance_labels.csv' or derive from the processed descriptors if merged.
    # For this implementation, we assume a specific file exists as per T015 output expectations.
    file_path = get_data_processed_path() / "resistance_labels.csv"
    if not file_path.exists():
        # Fallback to checking if it's part of the merged descriptors file if that's the convention
        # But T025 implies separate loading or merging. Let's assume the standard path.
        raise FileNotFoundError(f"Resistance labels not found at {file_path}")
    
    df = pd.read_csv(file_path)
    # Ensure we have a consistent column name, likely 'resistance_label' or 'resistance'
    if 'resistance_label' in df.columns:
        return df.set_index('InChIKey')['resistance_label']
    elif 'resistance' in df.columns:
        return df.set_index('InChIKey')['resistance']
    else:
        raise ValueError(f"Unknown column for resistance in {file_path}. Columns: {df.columns.tolist()}")

def run_dbscan(embedding: pd.DataFrame, eps: float = 0.5, min_samples: int = 10) -> np.ndarray:
    """Run DBSCAN clustering on the UMAP embedding."""
    coords = embedding[['UMAP_1', 'UMAP_2']].values
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    return db.labels_

def perform_fisher_exact_test(
    labels: np.ndarray, 
    resistance: pd.Series, 
    cluster_id: int
) -> Tuple[float, float]:
    """
    Perform Fisher's exact test for a specific cluster against high resistance.
    Returns (p_value, odds_ratio).
    """
    # Create a mask for the cluster
    cluster_mask = labels == cluster_id
    non_cluster_mask = ~cluster_mask

    # Extract resistance values for the cluster and non-cluster
    # We need to align indices if resistance is a Series
    cluster_res = resistance[cluster_mask]
    non_cluster_res = resistance[non_cluster_mask]

    # Count high resistance (1) vs low resistance (0) in both groups
    # Assuming resistance is binary (0/1) or can be thresholded. 
    # If continuous, we might need to binarize, but T025 implies Fisher which is for categorical.
    # We assume the resistance data passed in is already binary (High/Low mapped to 1/0).
    
    if cluster_res.empty or non_cluster_res.empty:
        return 1.0, 0.0

    # Construct contingency table
    # Rows: Cluster vs Non-Cluster
    # Cols: High Resistance (1) vs Low Resistance (0)
    high_cluster = cluster_res.sum()
    low_cluster = len(cluster_res) - high_cluster
    
    high_non_cluster = non_cluster_res.sum()
    low_non_cluster = len(non_cluster_res) - high_non_cluster

    table = [[high_cluster, low_cluster],
             [high_non_cluster, low_non_cluster]]

    if min(table[0]) + max(table[0]) == 0 or min(table[1]) + max(table[1]) == 0:
        return 1.0, 0.0

    try:
        odds_ratio, p_value = fisher_exact(table, alternative='greater')
        return p_value, float(odds_ratio)
    except Exception as e:
        logger.warning(f"Fisher exact test failed for cluster {cluster_id}: {e}")
        return 1.0, 0.0

def run_label_permutation_test(
    labels: np.ndarray,
    resistance: pd.Series,
    cluster_id: int,
    n_iterations: int,
    observed_p_value: float
) -> float:
    """
    Run label permutation test to validate enrichment is not a tautology.
    Randomly permute resistance labels and re-run Fisher's test.
    Returns the empirical p-value (fraction of permutations where p <= observed_p_value).
    """
    count_extreme = 0
    total = n_iterations
    
    # Pre-convert resistance to numpy array for speed
    resistance_array = resistance.values
    
    # Cache the cluster mask
    cluster_mask = labels == cluster_id
    non_cluster_mask = ~cluster_mask
    
    # Pre-calculate counts for the non-cluster group (these remain constant in permutation of labels)
    # Actually, in permutation, we shuffle the labels across ALL samples, so the counts change.
    # We must shuffle the entire resistance array.
    
    logger.info(f"Starting permutation test for cluster {cluster_id} with {total} iterations...")
    
    for i in range(total):
        # Permute labels
        permuted_resistance = np.random.permutation(resistance_array)
        
        # Re-calculate counts
        high_cluster = permuted_resistance[cluster_mask].sum()
        low_cluster = cluster_mask.sum() - high_cluster
        
        high_non_cluster = permuted_resistance[non_cluster_mask].sum()
        low_non_cluster = non_cluster_mask.sum() - high_non_cluster
        
        # Check for degenerate cases
        if low_cluster < 0 or low_non_cluster < 0:
            continue
            
        table = [[high_cluster, low_cluster],
                 [high_non_cluster, low_non_cluster]]
        
        # Check for zero rows/cols
        if (high_cluster + low_cluster) == 0 or (high_non_cluster + low_non_cluster) == 0:
            continue

        try:
            _, p_perm = fisher_exact(table, alternative='greater')
            if p_perm <= observed_p_value:
                count_extreme += 1
        except Exception:
            continue
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation iteration {i+1}/{total}")

    empirical_p_value = count_extreme / total
    logger.info(f"Permutation test for cluster {cluster_id} complete. Empirical p-value: {empirical_p_value:.4f}")
    return empirical_p_value

def save_clustering_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """Save clustering results to JSON."""
    if output_path is None:
        output_path = get_data_processed_path() / "clustering_results.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved clustering results to {output_path}")

def run_clustering_pipeline(
    eps: float = 0.5, 
    min_samples: int = 10, 
    permutation_iterations: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full clustering pipeline: UMAP -> DBSCAN -> Fisher -> Permutation.
    """
    config = load_config()
    if permutation_iterations is None:
        permutation_iterations = config.get('PERMUTATION_ITERATIONS', 1000)
    
    logger.info("Loading UMAP embedding...")
    embedding = load_umap_embedding()
    
    logger.info("Loading resistance labels...")
    resistance = load_resistance_labels()
    
    # Ensure resistance and embedding indices align
    # The embedding likely has an InChIKey index or a row index that matches the resistance file.
    # Assuming the CSVs are ordered or indexed by InChIKey.
    # If embedding has InChIKey column, set it as index.
    if 'InChIKey' in embedding.columns:
        embedding.set_index('InChIKey', inplace=True)
    
    # Align resistance to embedding index
    resistance = resistance.reindex(embedding.index)
    resistance = resistance.dropna()
    embedding = embedding.loc[resistance.index]
    
    logger.info("Running DBSCAN...")
    labels = run_dbscan(embedding, eps=eps, min_samples=min_samples)
    
    results = {
        "dbscan_params": {"eps": eps, "min_samples": min_samples},
        "n_clusters": len(set(labels)) - (1 if -1 in labels else 0),
        "n_noise": sum(labels == -1),
        "clusters": []
    }
    
    unique_labels = set(labels)
    if -1 in unique_labels:
        unique_labels.remove(-1)
    
    for cluster_id in unique_labels:
        logger.info(f"Processing cluster {cluster_id}...")
        
        # Filter for this cluster
        cluster_mask = labels == cluster_id
        cluster_size = cluster_mask.sum()
        
        if cluster_size < min_samples:
            logger.warning(f"Cluster {cluster_id} has size {cluster_size} < {min_samples}, skipping enrichment.")
            continue
        
        p_val, odds_ratio = perform_fisher_exact_test(labels, resistance, cluster_id)
        
        # Run permutation test
        perm_p_val = run_label_permutation_test(
            labels, resistance, cluster_id, permutation_iterations, p_val
        )
        
        cluster_result = {
            "cluster_id": int(cluster_id),
            "size": int(cluster_size),
            "fisher_p_value": float(p_val),
            "odds_ratio": float(odds_ratio),
            "permutation_p_value": float(perm_p_val),
            "is_significant": p_val < 0.05,
            "permutation_validated": perm_p_val < 0.05
        }
        results["clusters"].append(cluster_result)
        
        # Sort by Fisher p-value
        results["clusters"].sort(key=lambda x: x["fisher_p_value"])
    
    save_clustering_results(results)
    return results

def main():
    """Entry point for the clustering pipeline."""
    logging.basicConfig(level=logging.INFO)
    run_clustering_pipeline()

if __name__ == "__main__":
    main()