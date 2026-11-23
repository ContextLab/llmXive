import os
import sys
import logging
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy.stats import pearsonr
import hdbscan

# Import local utilities
from utils.logging_config import log_info_with_context, log_warning_with_context, log_error_with_context, get_logger
from utils.ilr_transform import transform_compositions

# Configure logger
logger = get_logger(__name__)

# Constants
DATA_PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("data/results")

def load_encoded_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load encoded alloy data from CSV."""
    if filepath is None:
        filepath = DATA_PROCESSED_DIR / "encoded_alloys.csv"
    path = Path(filepath)
    if not path.exists():
        log_error_with_context(f"Encoded data file not found: {path}")
        raise FileNotFoundError(f"Encoded data file not found: {path}")
    logger.info(f"Loading encoded data from {path}")
    df = pd.read_csv(path)
    # Handle potential list-string parsing for features if not already parsed by pandas
    # Assuming 'element_features' is stored as a string representation of list or JSON
    if 'element_features' in df.columns and df['element_features'].dtype == 'object':
        # Attempt to parse if it looks like a stringified list
        if isinstance(df['element_features'].iloc[0], str):
            df['element_features'] = df['element_features'].apply(lambda x: np.array(json.loads(x)) if isinstance(x, str) else x)
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Get columns used for feature analysis (excluding metadata)."""
    exclude_cols = ['composition', 'bulk_modulus', 'shear_modulus', 'element_features', 'cluster_id']
    return [col for col in df.columns if col not in exclude_cols]

def perform_elbow_method(df: pd.DataFrame, feature_cols: List[str], max_k: int = 10) -> List[float]:
    """Perform elbow method to find optimal K for K-Means (fallback)."""
    X = df[feature_cols].values
    inertias = []
    for k in range(1, max_k + 1):
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)
    return inertias

def perform_kmeans_clustering(df: pd.DataFrame, feature_cols: List[str], k: int) -> pd.DataFrame:
    """Perform K-Means clustering."""
    from sklearn.cluster import KMeans
    X = df[feature_cols].values
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    df['cluster_id'] = labels
    return df

def calculate_cluster_correlations(df: pd.DataFrame, cluster_col: str = 'cluster_id') -> Dict[int, float]:
    """Calculate Pearson correlation between Bulk and Shear moduli for each cluster."""
    correlations = {}
    for cluster_id in df[cluster_col].unique():
        if cluster_id == -1: # Noise
            continue
        cluster_data = df[df[cluster_col] == cluster_id]
        if len(cluster_data) < 3:
            correlations[cluster_id] = np.nan
            continue
        corr, _ = pearsonr(cluster_data['bulk_modulus'], cluster_data['shear_modulus'])
        correlations[cluster_id] = corr
    return correlations

def identify_decoupled_region(correlations: Dict[int, float], threshold: float = 0.5) -> Optional[int]:
    """Identify the cluster with the minimum correlation (decoupled region)."""
    if not correlations:
        return None
    # Filter out NaNs
    valid_corr = {k: v for k, v in correlations.items() if not np.isnan(v)}
    if not valid_corr:
        return None
    min_cluster = min(valid_corr, key=valid_corr.get)
    if valid_corr[min_cluster] < threshold:
        return min_cluster
    return None

def flag_high_variance_regions(df: pd.DataFrame, threshold: float = 10.0) -> pd.DataFrame:
    """Flag regions where prediction variance exceeds threshold."""
    # Placeholder for variance calculation logic if residuals are available
    df['high_variance'] = False
    return df

def run_sensitivity_analysis(
    encoded_data_path: Optional[str] = None,
    clustering_results_path: Optional[str] = None,
    correlation_stats_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Implement sensitivity analysis for HDBSCAN parameters.
    
    Re-runs HDBSCAN on ilr-transformed residuals with varied parameters.
    Calculates robustness_score (Jaccard Index) of decoupled region membership
    against the optimal set defined in T031.
    
    Args:
        encoded_data_path: Path to encoded_alloys.csv
        clustering_results_path: Path to clustering_results.csv (contains optimal clusters)
        correlation_stats_path: Path to correlation_stats.csv (contains decoupled threshold)
        output_path: Path to save sensitivity_analysis.csv
    
    Returns:
        DataFrame with sensitivity analysis results.
    """
    logger.info("Starting sensitivity analysis for HDBSCAN parameters")
    
    # Load inputs
    if encoded_data_path is None:
        encoded_data_path = DATA_PROCESSED_DIR / "encoded_alloys.csv"
    if clustering_results_path is None:
        clustering_results_path = DATA_PROCESSED_DIR / "clustering_results.csv"
    if correlation_stats_path is None:
        correlation_stats_path = DATA_PROCESSED_DIR / "correlation_stats.csv"
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "sensitivity_analysis.csv"
    
    encoded_df = load_encoded_data(encoded_data_path)
    
    if not Path(clustering_results_path).exists():
        log_error_with_context(f"Clustering results file not found: {clustering_results_path}")
        raise FileNotFoundError(f"Clustering results file not found: {clustering_results_path}")
    optimal_clusters_df = pd.read_csv(clustering_results_path)
    
    if not Path(correlation_stats_path).exists():
        log_error_with_context(f"Correlation stats file not found: {correlation_stats_path}")
        raise FileNotFoundError(f"Correlation stats file not found: {correlation_stats_path}")
    correlation_stats_df = pd.read_csv(correlation_stats_path)
    
    # Identify the decoupled region threshold and optimal cluster ID from T031 results
    # T031 output: cluster_id, local_correlation, global_correlation, delta, p-value
    # We need the 'decoupled' status. Assuming the cluster with min correlation is the target.
    # If T031 explicitly marked a 'decoupled' column, use that. Otherwise, infer from min correlation.
    
    if 'is_decoupled' in correlation_stats_df.columns:
        decoupled_cluster_id = correlation_stats_df[correlation_stats_df['is_decoupled'] == True]['cluster_id'].iloc[0]
    else:
        # Fallback: find cluster with minimum local correlation
        valid_rows = correlation_stats_df[~correlation_stats_df['local_correlation'].isna()]
        if valid_rows.empty:
            log_error_with_context("No valid correlation stats found to identify decoupled region.")
            raise ValueError("No valid correlation stats found.")
        decoupled_cluster_id = valid_rows.loc[valid_rows['local_correlation'].idxmin()]['cluster_id']
    
    logger.info(f"Identified decoupled region cluster ID from T031: {decoupled_cluster_id}")
    
    # Prepare data for HDBSCAN: need ilr-transformed residuals
    # We need to reconstruct the residuals. 
    # Option 1: If clustering_results.csv has residuals, use them.
    # Option 2: Re-calculate residuals using the models (requires loading models, complex).
    # Option 3: Assume clustering_results.csv has the ilr-transformed features used for clustering.
    # The task says "Re-run HDBSCAN ... on the ilr-transformed residuals from T030".
    # T030 output is clustering_results.csv. It should contain the features used.
    # Let's assume clustering_results.csv has columns: 'ilr_features' (list/array) or individual ilr columns.
    # If not, we need to compute residuals.
    
    # Check for residuals in clustering results
    if 'residuals' in optimal_clusters_df.columns:
        # Assuming residuals is a stringified list or array
        residuals_list = optimal_clusters_df['residuals'].apply(lambda x: np.array(json.loads(x)) if isinstance(x, str) else x)
        X_residuals = np.vstack(residuals_list.values)
    else:
        # Fallback: Compute residuals if we have predictions?
        # This is complex without loading models. Let's assume the clustering_results.csv 
        # was generated with ilr-transformed residuals and those are stored.
        # If not present, we might need to re-run the encoding + residual calculation.
        # For robustness, let's try to compute residuals from encoded data if we have predictions.
        # But we don't have predictions here.
        # Let's assume the 'ilr_features' column exists in clustering_results or encoded_data.
        
        # Actually, T029b provides ilr_transform. T030 used it.
        # Let's assume we can re-calculate residuals if we had the model predictions.
        # Since we don't have the model easily accessible here without loading, 
        # and the task says "from T030", we assume T030 output contains the necessary data.
        # Let's look for 'ilr_residuals' or similar.
        
        # If not found, we must fail loudly or try to reconstruct.
        # Let's try to reconstruct from encoded data if we have bulk/shear and predictions?
        # We don't have predictions.
        
        # CRITICAL: If we cannot find the residuals, we cannot proceed.
        # Let's assume the 'element_features' in encoded_data are used, but T030 used residuals.
        # We need to be careful.
        
        # Alternative: Re-run the prediction step? No, that's T020/T021.
        # Let's assume the clustering_results.csv has a column 'ilr_residuals' or 'residuals'.
        # If not, we might need to re-calculate.
        
        # For this implementation, we will assume 'residuals' column exists in clustering_results.csv.
        # If not, we raise an error.
        raise ValueError("Clustering results must contain 'residuals' column for sensitivity analysis.")

    # Define sweep ranges
    min_cluster_size_range = range(5, 21) # [5, 20] inclusive
    min_samples_range = range(5, 16)      # [5, 15] inclusive
    
    # Get optimal parameters from T030 if available in clustering_results_df metadata or a separate file?
    # T030 output might not explicitly store optimal params in the CSV.
    # Let's assume we know the optimal params from T030 run (e.g., hardcoded or from a config).
    # For now, we need to identify the 'optimal' set to compare against.
    # If clustering_results.csv has a 'is_optimal' flag or we know the params used to generate it.
    # Let's assume the optimal params were min_cluster_size=10, min_samples=5 (example).
    # We need to extract this.
    
    # If not available, we can't calculate Jaccard against 'optimal'.
    # Let's assume the optimal parameters are stored in a metadata file or we use the first valid one.
    # Better: The task says "against the optimal set (from T030)".
    # We assume T030 output (clustering_results.csv) was generated with specific params.
    # We need to know what those were.
    # If not stored, we might need to infer or assume.
    # Let's assume the optimal params are min_cluster_size=10, min_samples=5 for this run.
    # In a real scenario, this would be passed or stored.
    
    # Let's try to find the optimal cluster assignment in optimal_clusters_df.
    # We need to map the decoupled cluster from T031 to the clusters in the sweep.
    
    # We need the optimal cluster assignment (labels) to compute Jaccard.
    optimal_labels = optimal_clusters_df['cluster_id'].values
    optimal_decoupled_cluster_id = decoupled_cluster_id
    
    # We need to identify which cluster ID in the optimal run corresponds to the decoupled region.
    # T031 identified decoupled_cluster_id.
    # We need to map this to the new clustering results.
    
    results = []
    
    for min_c_size in min_cluster_size_range:
        for min_s in min_samples_range:
            logger.info(f"Running HDBSCAN with min_cluster_size={min_c_size}, min_samples={min_s}")
            
            # Run HDBSCAN
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_c_size,
                min_samples=min_s,
                metric='euclidean',
                cluster_selection_method='eom'
            )
            labels = clusterer.fit_predict(X_residuals)
            
            # Create a temporary DataFrame for this run
            temp_df = pd.DataFrame({'cluster_id': labels})
            
            # Calculate cluster correlations for this run
            current_correlations = calculate_cluster_correlations_for_labels(temp_df, X_residuals, encoded_df) 
            # Note: We need to map residuals back to bulk/shear to calculate correlations.
            # This is tricky. We need to know which residual belongs to which sample.
            # X_residuals is derived from the original samples.
            # So temp_df['cluster_id'] corresponds to the original encoded_df index.
            
            # Calculate mean correlation of the cluster identified as 'decoupled' in this run?
            # Or calculate correlation for all clusters and find the min?
            # The task says: "re-evaluate the 'decoupled' status of clusters against the correlation threshold identified in T031"
            # So we find clusters with correlation < threshold.
            
            # We need to calculate correlations for each cluster in this run.
            # We need to attach bulk/shear moduli to the clusters.
            # We have encoded_df which has bulk/shear.
            # We need to merge temp_df with encoded_df.
            
            temp_df_with_data = encoded_df.copy()
            temp_df_with_data['cluster_id'] = labels
            
            current_cluster_corrs = calculate_cluster_correlations(temp_df_with_data, 'cluster_id')
            
            # Identify decoupled clusters in this run (correlation < threshold from T031)
            # Threshold from T031: global correlation? Or a specific threshold?
            # T031 output has 'global_correlation'. Let's use that as threshold?
            # Or the 'local_correlation' of the decoupled region?
            # The task says "against the correlation threshold identified in T031".
            # Let's assume the threshold is the global correlation from T031.
            # Or maybe the local correlation of the decoupled cluster?
            # Let's use the global correlation from T031 as the threshold.
            global_corr_threshold = correlation_stats_df['global_correlation'].iloc[0]
            
            decoupled_clusters_this_run = [cid for cid, corr in current_cluster_corrs.items() if corr < global_corr_threshold and not np.isnan(corr)]
            
            # Map to Jaccard Index
            # We need to compare the set of samples in the decoupled region of optimal run vs this run.
            # Optimal decoupled region: samples where optimal_labels == optimal_decoupled_cluster_id
            # Current decoupled region: samples where labels == any of decoupled_clusters_this_run
            
            optimal_decoupled_mask = (optimal_labels == optimal_decoupled_cluster_id)
            current_decoupled_mask = np.isin(labels, decoupled_clusters_this_run)
            
            intersection = np.sum(optimal_decoupled_mask & current_decoupled_mask)
            union = np.sum(optimal_decoupled_mask | current_decoupled_mask)
            
            if union == 0:
                jaccard = 0.0
            else:
                jaccard = intersection / union
            
            # Calculate region size (number of points in decoupled region)
            region_size = np.sum(current_decoupled_mask)
            
            # Calculate mean correlation of the decoupled region in this run
            if decoupled_clusters_this_run:
                mean_corr = np.mean([current_cluster_corrs[cid] for cid in decoupled_clusters_this_run])
            else:
                mean_corr = np.nan
            
            results.append({
                'min_cluster_size': min_c_size,
                'min_samples': min_s,
                'region_size': region_size,
                'mean_correlation': mean_corr,
                'robustness_score': jaccard
            })
    
    results_df = pd.DataFrame(results)
    
    # Save results
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis results saved to {output_path}")
    
    return results_df

def calculate_cluster_correlations_for_labels(temp_df: pd.DataFrame, X_residuals: np.ndarray, encoded_df: pd.DataFrame) -> Dict[int, float]:
    """Helper to calculate correlations for a given set of labels."""
    # This function is a placeholder. We need to merge temp_df with encoded_df to get bulk/shear.
    # But temp_df only has cluster_id. We need to ensure the index matches encoded_df.
    # Assuming X_residuals was derived from encoded_df in order.
    # So temp_df index matches encoded_df index.
    # We need to assign cluster_id to encoded_df.
    combined_df = encoded_df.copy()
    combined_df['cluster_id'] = temp_df['cluster_id'].values
    return calculate_cluster_correlations(combined_df, 'cluster_id')

def save_results(df: pd.DataFrame, filepath: str):
    """Save results to CSV."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Results saved to {path}")

def main():
    parser = argparse.ArgumentParser(description="Cluster Analysis and Sensitivity for Alloy Design")
    parser.add_argument("--encoded-data", type=str, default=None, help="Path to encoded_alloys.csv")
    parser.add_argument("--clustering-results", type=str, default=None, help="Path to clustering_results.csv")
    parser.add_argument("--correlation-stats", type=str, default=None, help="Path to correlation_stats.csv")
    parser.add_argument("--output", type=str, default=None, help="Path to save sensitivity_analysis.csv")
    parser.add_argument("--run-sensitivity", action="store_true", help="Run sensitivity analysis")
    
    args = parser.parse_args()
    
    if args.run_sensitivity:
        run_sensitivity_analysis(
            encoded_data_path=args.encoded_data,
            clustering_results_path=args.clustering_results,
            correlation_stats_path=args.correlation_stats,
            output_path=args.output
        )
    else:
        logger.info("No action specified. Use --run-sensitivity to run sensitivity analysis.")

if __name__ == "__main__":
    main()