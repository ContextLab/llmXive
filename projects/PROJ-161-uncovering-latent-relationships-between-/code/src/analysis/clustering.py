import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

from src.config import get_project_root, get_data_processed_path, load_config, get_config_value

logger = logging.getLogger(__name__)

def load_umap_embedding() -> pd.DataFrame:
    """Load the UMAP embedding from the processed data directory."""
    processed_path = get_data_processed_path()
    file_path = processed_path / "umap_embedding.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"UMAP embedding file not found: {file_path}")
    df = pd.read_csv(file_path)
    # Ensure required columns exist
    if 'umap_1' not in df.columns or 'umap_2' not in df.columns:
        raise ValueError("UMAP embedding must contain 'umap_1' and 'umap_2' columns")
    return df

def load_resistance_labels() -> pd.Series:
    """Load resistance labels (high/low) aligned with UMAP embedding indices."""
    processed_path = get_data_processed_path()
    # Assuming resistance labels are stored in a file generated during US1 processing
    # or merged into the descriptor/UMap dataframe. 
    # Based on typical pipeline flow, we expect a file 'resistance_labels.csv' or similar.
    # If the labels are part of the UMAP embedding file (common in this pipeline), we read from there.
    # Let's check for a dedicated file first, then fallback to embedding if column exists.
    
    labels_file = processed_path / "resistance_labels.csv"
    if labels_file.exists():
        df_labels = pd.read_csv(labels_file)
        # Expect 'index' and 'resistance_label' or similar
        if 'index' in df_labels.columns and 'resistance_label' in df_labels.columns:
            return df_labels.set_index('index')['resistance_label']
        elif 'compound_id' in df_labels.columns and 'resistance_label' in df_labels.columns:
            # Map back to embedding index if possible, assuming embedding index is compound_id
            return df_labels.set_index('compound_id')['resistance_label']
    
    # Fallback: Check if UMAP embedding has the column
    embedding = load_umap_embedding()
    if 'resistance_label' in embedding.columns:
        return embedding.set_index(embedding.index if 'index' not in embedding.columns else 'index')['resistance_label']
    
    raise FileNotFoundError("Could not find resistance labels in expected locations.")

def run_dbscan(embedding_df: pd.DataFrame, eps: float = 0.5, min_samples: int = 10) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run DBSCAN clustering on UMAP coordinates."""
    coords = embedding_df[['umap_1', 'umap_2']].values
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(coords)
    
    # Add labels to dataframe
    result_df = embedding_df.copy()
    result_df['cluster_label'] = labels
    
    # Calculate silhouette score if more than 1 cluster and not all noise
    unique_labels = set(labels)
    if len(unique_labels) > 1 and -1 in unique_labels:
        # Exclude noise (-1) for silhouette score
        mask = labels != -1
        if np.sum(mask) > 1:
            score = silhouette_score(coords[mask], labels[mask])
        else:
            score = None
    elif len(unique_labels) > 1:
        score = silhouette_score(coords, labels)
    else:
        score = None
        
    metadata = {
        "eps": eps,
        "min_samples": min_samples,
        "n_clusters": len(unique_labels) - (1 if -1 in unique_labels else 0),
        "n_noise": np.sum(labels == -1),
        "silhouette_score": score
    }
    
    return result_df, metadata

def perform_fisher_exact_test(cluster_df: pd.DataFrame, global_df: pd.DataFrame, 
                              cluster_id: int, high_res_label: str = 'high') -> Dict[str, Any]:
    """Perform Fisher's exact test for a specific cluster against the rest."""
    # Filter cluster and non-cluster (excluding noise if cluster_id != -1, but usually we test positive clusters)
    if cluster_id == -1:
        return {"cluster_id": cluster_id, "status": "skipped", "reason": "Noise cluster"}
    
    cluster_mask = cluster_df['cluster_label'] == cluster_id
    non_cluster_mask = cluster_df['cluster_label'] != cluster_id
    
    # Create contingency table
    # Rows: Cluster, Non-Cluster
    # Cols: High Resistance, Low Resistance (or Not High)
    
    # We need the resistance label column. Assuming it's in the dataframe passed in or global
    # The input cluster_df should have the resistance label column if it was merged before clustering
    # If not, we need to map it back. For this implementation, we assume the dataframe passed 
    # to this function (or derived from it) has the 'resistance_label' column.
    
    # Let's assume the dataframe passed to run_dbscan had the resistance label column added
    # If not, we need to load it again. To be safe, we look for it in the dataframe.
    if 'resistance_label' not in cluster_df.columns:
        # Try to load it
        try:
            labels = load_resistance_labels()
            # Align by index
            cluster_df = cluster_df.join(labels, how='left')
        except Exception as e:
            return {"cluster_id": cluster_id, "status": "error", "reason": f"Could not load resistance labels: {e}"}

    high_cluster = (cluster_df.loc[cluster_mask, 'resistance_label'] == high_res_label).sum()
    low_cluster = (cluster_df.loc[cluster_mask, 'resistance_label'] != high_res_label).sum()
    
    high_non_cluster = (cluster_df.loc[non_cluster_mask, 'resistance_label'] == high_res_label).sum()
    low_non_cluster = (cluster_df.loc[non_cluster_mask, 'resistance_label'] != high_res_label).sum()
    
    if high_cluster + low_cluster == 0 or high_non_cluster + low_non_cluster == 0:
        return {"cluster_id": cluster_id, "status": "skipped", "reason": "Empty group"}
    
    try:
        oddsratio, pvalue = stats.fisher_exact([[high_cluster, low_cluster], 
                                                [high_non_cluster, low_non_cluster]])
        return {
            "cluster_id": cluster_id,
            "status": "success",
            "contingency": [[high_cluster, low_cluster], [high_non_cluster, low_non_cluster]],
            "odds_ratio": float(oddsratio),
            "p_value": float(pvalue)
        }
    except Exception as e:
        return {"cluster_id": cluster_id, "status": "error", "reason": str(e)}

def run_label_permutation_test(cluster_df: pd.DataFrame, iterations: int = 1000, 
                               high_res_label: str = 'high') -> List[float]:
    """Run label permutation test to validate enrichment."""
    if 'resistance_label' not in cluster_df.columns:
        try:
            labels = load_resistance_labels()
            cluster_df = cluster_df.join(labels, how='left')
        except Exception as e:
            logger.error(f"Failed to load resistance labels for permutation test: {e}")
            return []
    
    p_values = []
    unique_labels = cluster_df['cluster_label'].unique()
    positive_clusters = [c for c in unique_labels if c != -1]
    
    if not positive_clusters:
        logger.warning("No positive clusters found for permutation test.")
        return []
    
    # We will perform permutation for each positive cluster and collect p-values
    # Or perform a global test? The task says "validate enrichment". 
    # Typically, we check if the observed p-value is in the tail of the permuted distribution.
    # Let's collect permuted p-values for the most significant cluster or all clusters.
    # For simplicity and robustness, we'll run the permutation for the cluster with the lowest observed p-value.
    
    # First, get observed p-values
    observed_results = {}
    for cid in positive_clusters:
        res = perform_fisher_exact_test(cluster_df, cluster_df, cid, high_res_label)
        if res['status'] == 'success':
            observed_results[cid] = res['p_value']
    
    if not observed_results:
        return []
    
    target_cluster = min(observed_results, key=observed_results.get)
    observed_p = observed_results[target_cluster]
    
    logger.info(f"Running {iterations} permutations for cluster {target_cluster} (observed p={observed_p:.4f})")
    
    cluster_mask = cluster_df['cluster_label'] == target_cluster
    non_cluster_mask = cluster_df['cluster_label'] != target_cluster
    
    high_counts = []
    low_counts = []
    
    # Pre-calculate indices to avoid repeated lookups
    cluster_indices = cluster_df.index[cluster_mask].tolist()
    non_cluster_indices = cluster_df.index[non_cluster_mask].tolist()
    all_indices = cluster_df.index.tolist()
    resistance_values = cluster_df['resistance_label'].values
    index_to_val = dict(zip(all_indices, resistance_values))
    
    # We need to permute the labels across the whole dataset? Or just within the groups?
    # Standard permutation: shuffle the labels (High/Low) across all samples, keeping cluster structure fixed.
    # Then recalculate the statistic (or p-value) for the target cluster.
    
    # Let's create a binary array for permutation
    binary_labels = (cluster_df['resistance_label'] == high_res_label).astype(int)
    total_high = binary_labels.sum()
    total_low = len(binary_labels) - total_high
    
    cluster_size = cluster_mask.sum()
    
    for i in range(iterations):
        # Permute labels
        permuted_labels = np.random.permutation(binary_labels.values)
        
        # Count high in cluster
        perm_high_cluster = permuted_labels[cluster_mask].sum()
        perm_low_cluster = cluster_size - perm_high_cluster
        
        # Count high in non-cluster
        perm_high_non = permuted_labels[non_cluster_mask].sum()
        perm_low_non = total_low - perm_low_cluster # or len(non_cluster) - perm_high_non
        
        if perm_high_cluster + perm_low_cluster == 0 or perm_high_non + perm_low_non == 0:
            continue
            
        try:
            _, p_val = stats.fisher_exact([[perm_high_cluster, perm_low_cluster],
                                           [perm_high_non, perm_low_non]])
            p_values.append(p_val)
        except:
            continue
    
    return p_values

def save_clustering_results(results: List[Dict[str, Any]], permutation_p_values: List[float],
                            metadata: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save clustering results to JSON."""
    if output_path is None:
        processed_path = get_data_processed_path()
        output_path = processed_path / "clustering_results.json"
    
    final_results = {
        "metadata": metadata,
        "clusters": results,
        "permutation_test": {
            "iterations": len(permutation_p_values),
            "permuted_p_values": permutation_p_values,
            "diagnostic": f"Permuted p-values distribution: min={min(permutation_p_values) if permutation_p_values else 0:.4f}, max={max(permutation_p_values) if permutation_p_values else 0:.4f}, mean={np.mean(permutation_p_values) if permutation_p_values else 0:.4f}"
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Clustering results saved to {output_path}")
    return output_path

def run_clustering_pipeline(eps: float = 0.5, min_samples: int = 10, 
                            permutation_iterations: Optional[int] = None) -> Path:
    """Run the full clustering pipeline: DBSCAN -> Fisher -> Permutation -> Save."""
    config = load_config()
    if permutation_iterations is None:
        permutation_iterations = get_config_value(config, "PERMUTATION_ITERATIONS", 1000)
    
    logger.info(f"Starting clustering pipeline with eps={eps}, min_samples={min_samples}, perms={permutation_iterations}")
    
    # Load data
    embedding_df = load_umap_embedding()
    
    # Run DBSCAN
    clustered_df, db_metadata = run_dbscan(embedding_df, eps, min_samples)
    
    # Filter clusters for enrichment (exclude noise and small clusters)
    # T027: Exclude clusters with <10 samples
    cluster_counts = clustered_df.groupby('cluster_label').size()
    valid_clusters = [cid for cid, count in cluster_counts.items() if cid != -1 and count >= 10]
    
    if not valid_clusters:
        logger.warning("No valid clusters found (size >= 10 and not noise). Saving empty results.")
        results = []
        perm_p_values = []
    else:
        # Perform Fisher's exact test for each valid cluster
        results = []
        for cid in valid_clusters:
            fisher_res = perform_fisher_exact_test(clustered_df, clustered_df, cid)
            results.append(fisher_res)
        
        # Run permutation test
        # We run permutation on the most significant cluster or all? 
        # To be thorough, we can run it for the best one, or aggregate.
        # Let's run it for the cluster with the lowest p-value among results.
        successful_results = [r for r in results if r['status'] == 'success']
        if successful_results:
            best_cluster = min(successful_results, key=lambda x: x['p_value'])
            best_cid = best_cluster['cluster_id']
            
            # Run permutation for this best cluster
            # We need to re-run the logic or pass the dataframe and target cluster
            # The function run_label_permutation_test currently runs for the best one internally if we modify it,
            # but let's make it explicit.
            # Actually, let's modify run_label_permutation_test to accept a specific cluster ID if needed,
            # or just run it for the best one found.
            
            # Re-implementing the specific permutation for the best cluster to ensure accuracy
            perm_p_values = run_label_permutation_test(clustered_df, permutation_iterations)
        else:
            perm_p_values = []
    
    # Save results
    output_path = save_clustering_results(results, perm_p_values, db_metadata)
    
    return output_path

def main():
    """Entry point for the clustering pipeline script."""
    logging.basicConfig(level=logging.INFO)
    try:
        output_path = run_clustering_pipeline()
        print(f"Clustering pipeline completed. Results saved to: {output_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
