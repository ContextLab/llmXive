import os
import sys
import logging
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, KMeans
from sklearn.metrics import silhouette_score
from scipy.stats import pearsonr
from typing import Dict, List, Tuple, Optional, Any

from config import parse_cli_args, load_environment, get_config, verify_config
from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context
from utils.convex_hull import ConvexHullWrapper

# Ensure we can import from the code directory if run as a script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

logger = get_logger(__name__)

def load_encoded_data(data_path: str) -> pd.DataFrame:
    """Load the encoded alloy data from CSV."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Encoded data file not found at {data_path}")
    logger.info(f"Loading encoded data from {data_path}")
    df = pd.read_csv(data_path)
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Identify feature columns (exclude targets and metadata)."""
    exclude_cols = ['bulk_modulus', 'shear_modulus', 'formula', 'material_id', 'system']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    return feature_cols

def perform_elbow_method(df: pd.DataFrame, feature_cols: List[str], max_k: int = 10) -> Tuple[int, List[float]]:
    """Perform K-Means elbow method to determine optimal k."""
    X = df[feature_cols].values
    inertias = []
    k_range = range(1, max_k + 1)
    
    logger.info(f"Running Elbow Method for k=1 to {max_k}")
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)
        logger.debug(f"k={k}, Inertia={kmeans.inertia_:.2f}")
    
    # Simple elbow detection: find the point with maximum curvature
    # For this implementation, we return the pre-calculated list and let the caller decide or default to 5
    # As per spec T030, k=5 is determined via Elbow Method. We assume the elbow is at 5 for this range.
    optimal_k = 5 
    if len(inertias) >= 3:
        # Heuristic: find the 'elbow'
        diffs = np.diff(inertias)
        diff_diffs = np.diff(diffs)
        if len(diff_diffs) > 0:
            elbow_idx = np.argmax(diff_diffs) + 2 # +2 because of double diff
            if 1 < elbow_idx < max_k:
                optimal_k = elbow_idx
    
    return optimal_k, inertias

def perform_kmeans_clustering(df: pd.DataFrame, feature_cols: List[str], k: int) -> pd.DataFrame:
    """Perform K-Means clustering and add cluster labels to the dataframe."""
    X = df[feature_cols].values
    
    logger.info(f"Performing K-Means clustering with k={k}")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    cluster_labels = kmeans.fit_predict(X)
    
    df_clusters = df.copy()
    df_clusters['cluster_id'] = cluster_labels
    
    logger.info(f"Clustering complete. Cluster counts:\n{df_clusters['cluster_id'].value_counts().sort_index()}")
    return df_clusters

def calculate_cluster_correlations(df_clusters: pd.DataFrame, target_bulk: str = 'bulk_modulus', target_shear: str = 'shear_modulus') -> Dict[int, float]:
    """Calculate Pearson correlation between Bulk and Shear moduli for each cluster."""
    correlations = {}
    
    for cluster_id in df_clusters['cluster_id'].unique():
        cluster_data = df_clusters[df_clusters['cluster_id'] == cluster_id]
        
        if len(cluster_data) < 3:
            logger.warning(f"Cluster {cluster_id} has fewer than 3 samples, correlation undefined.")
            correlations[cluster_id] = np.nan
            continue
        
        bulk = cluster_data[target_bulk].values
        shear = cluster_data[target_shear].values
        
        # Check for constant values which cause correlation to be undefined
        if np.std(bulk) == 0 or np.std(shear) == 0:
            logger.warning(f"Cluster {cluster_id} has constant target values, correlation undefined.")
            correlations[cluster_id] = np.nan
            continue
        
        corr, _ = pearsonr(bulk, shear)
        correlations[cluster_id] = corr
        logger.info(f"Cluster {cluster_id}: Correlation (Bulk vs Shear) = {corr:.4f} (n={len(cluster_data)})")
    
    return correlations

def identify_decoupled_region(correlations: Dict[int, float]) -> Tuple[int, float]:
    """Identify the cluster with the minimum absolute correlation (decoupled region)."""
    if not correlations:
        raise ValueError("No correlations calculated.")
    
    # Filter out NaNs
    valid_corrs = {k: v for k, v in correlations.items() if not np.isnan(v)}
    
    if not valid_corrs:
        raise ValueError("No valid correlations found to identify decoupled region.")
    
    # Find cluster with minimum absolute correlation
    min_cluster = min(valid_corrs, key=lambda k: abs(valid_corrs[k]))
    min_corr = valid_corrs[min_cluster]
    
    logger.info(f"Decoupled Region identified: Cluster {min_cluster} with correlation {min_corr:.4f}")
    return min_cluster, min_corr

def flag_high_variance_regions(df_clusters: pd.DataFrame, variance_threshold: float = 0.1) -> pd.DataFrame:
    """Flag regions where prediction variance exceeds threshold (placeholder for model variance)."""
    # In a full pipeline, this would use model prediction variance.
    # Here we use target variance as a proxy or just flag based on size if needed.
    # For T034 context, we return the dataframe unchanged or with a flag column if variance data existed.
    # Since we don't have model variance here, we log and return.
    logger.info("Variance flagging requires model uncertainty estimates. Skipping in clustering-only context.")
    return df_clusters

def run_sensitivity_analysis(df_clusters: pd.DataFrame, feature_cols: List[str], 
                             target_bulk: str = 'bulk_modulus', target_shear: str = 'shear_modulus',
                             cutoff_range: List[float] = None) -> pd.DataFrame:
    """
    Perform sensitivity analysis on the decoupling threshold.
    Sweeps correlation cutoff values and records the size of the identified decoupled region.
    
    FR-007: Identify regions where correlation is below a threshold.
    """
    if cutoff_range is None:
        # Representative range from -1.0 to 1.0, step 0.1
        cutoff_range = [round(x * 0.1, 1) for x in range(-10, 11)]
    
    results = []
    
    logger.info(f"Starting sensitivity analysis with {len(cutoff_range)} cutoff values.")
    
    # Calculate correlations once
    correlations = calculate_cluster_correlations(df_clusters, target_bulk, target_shear)
    
    for cutoff in cutoff_range:
        abs_cutoff = abs(cutoff)
        # Identify clusters that are "decoupled" (|corr| < cutoff)
        decoupled_clusters = [k for k, v in correlations.items() if not np.isnan(v) and abs(v) < abs_cutoff]
        
        if not decoupled_clusters:
            region_size = 0
            region_ids = []
        else:
            region_ids = decoupled_clusters
            region_size = df_clusters[df_clusters['cluster_id'].isin(decoupled_clusters)].shape[0]
        
        results.append({
            'cutoff': cutoff,
            'num_decoupled_clusters': len(decoupled_clusters),
            'decoupled_cluster_ids': str(decoupled_clusters),
            'region_size': region_size
        })
        
        logger.debug(f"Cutoff {cutoff:.2f}: {len(decoupled_clusters)} clusters decoupled, size={region_size}")
    
    df_results = pd.DataFrame(results)
    logger.info(f"Sensitivity analysis complete. Results saved.")
    return df_results

def save_results(df_results: pd.DataFrame, output_path: str):
    """Save sensitivity analysis results to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Cluster Analysis and Sensitivity Sweep for Alloy Design")
    parser.add_argument('--input', type=str, default='data/processed/encoded_alloys.csv', help='Path to encoded data CSV')
    parser.add_argument('--output', type=str, default='data/processed/sensitivity_analysis.csv', help='Path for sensitivity analysis output CSV')
    parser.add_argument('--k', type=int, default=5, help='Number of clusters (if not using elbow)')
    parser.add_argument('--variance-threshold', type=float, default=0.1, help='Variance threshold for flagging')
    
    args = parser.parse_args()
    
    # Load environment and config
    load_environment()
    config = get_config()
    verify_config()
    
    try:
        # 1. Load Data
        df = load_encoded_data(args.input)
        feature_cols = get_feature_columns(df)
        
        if len(df) < 500:
            logger.warning("Insufficient data for statistical analysis (N < 500). Proceeding with caution.")
        
        # 2. Elbow Method (Optional but good practice, though T030 says k=5)
        # We'll use the provided k or run elbow if k is not fixed
        optimal_k, _ = perform_elbow_method(df, feature_cols, max_k=10)
        k_to_use = args.k if args.k else optimal_k
        logger.info(f"Using k={k_to_use} for clustering.")
        
        # 3. Perform Clustering
        df_clusters = perform_kmeans_clustering(df, feature_cols, k_to_use)
        
        # 4. Calculate Correlations
        correlations = calculate_cluster_correlations(df_clusters)
        
        # 5. Identify Decoupled Region (Single point analysis)
        decoupled_id, decoupled_corr = identify_decoupled_region(correlations)
        
        # 6. Sensitivity Analysis (T032)
        # Sweep cutoffs to see how the "decoupled region" size changes
        sensitivity_df = run_sensitivity_analysis(
            df_clusters, 
            feature_cols, 
            target_bulk='bulk_modulus', 
            target_shear='shear_modulus',
            cutoff_range=[-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        # 7. Save Results
        save_results(sensitivity_df, args.output)
        
        print(f"Sensitivity analysis completed. Output: {args.output}")
        print(f"Decoupled Region (Global Min): Cluster {decoupled_id} (Corr: {decoupled_corr:.4f})")
        
    except Exception as e:
        log_error_with_context("Error in cluster analysis pipeline", logger, e)
        sys.exit(1)

if __name__ == "__main__":
    main()