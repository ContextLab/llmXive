import os
import sys
import logging
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

from config import load_environment, get_config
from utils.logging_config import log_info_with_context, log_error_with_context, get_logger

# Initialize logger
logger = get_logger(__name__)

def load_encoded_data(filepath: str) -> pd.DataFrame:
    """Load the encoded alloy data from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Encoded data file not found: {filepath}")
    df = pd.read_csv(path)
    log_info_with_context(logger, f"Loaded {len(df)} rows from {filepath}")
    return df

def get_feature_columns(df: pd.DataFrame) -> list:
    """Identify feature columns (exclude targets and metadata)."""
    exclude_cols = ['composition', 'bulk_modulus', 'shear_modulus', 'cluster_id', 'correlation']
    features = [col for col in df.columns if col not in exclude_cols]
    return features

def perform_elbow_method(df: pd.DataFrame, feature_cols: list, k_range: range = range(2, 11)) -> tuple:
    """Perform Elbow Method to determine optimal k."""
    X = df[feature_cols].values
    inertias = []
    k_values = list(k_range)
    
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)
    
    # Simple heuristic: find the "elbow" (maximize second derivative)
    # Or just return the k with lowest inertia if no clear elbow, but usually 2-10 range has one.
    # For robustness, we return the list and let the caller decide or pick the first significant drop.
    # Here we return the k with the maximum drop in inertia rate.
    if len(inertias) < 3:
        return k_values[0], inertias
        
    diffs = np.diff(inertias)
    second_diffs = np.diff(diffs)
    # The elbow is where the second derivative is maximized (most positive change in slope)
    # Since inertia decreases, we look for the point where the decrease slows down most.
    elbow_idx = np.argmax(second_diffs) + 2 # +2 because of double diff
    optimal_k = k_values[elbow_idx]
    
    log_info_with_context(logger, f"Elbow method determined optimal k={optimal_k}")
    return optimal_k, inertias

def perform_kmeans_clustering(df: pd.DataFrame, feature_cols: list, k: int) -> pd.DataFrame:
    """Perform K-Means clustering."""
    X = df[feature_cols].values
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    df['cluster_id'] = cluster_labels
    log_info_with_context(logger, f"Performed K-Means with k={k}, unique clusters: {len(np.unique(cluster_labels))}")
    return df

def calculate_cluster_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation between Bulk and Shear Moduli for each cluster."""
    results = []
    clusters = df['cluster_id'].unique()
    
    for cid in clusters:
        cluster_data = df[df['cluster_id'] == cid]
        if len(cluster_data) > 1:
            corr, _ = pearsonr(cluster_data['bulk_modulus'], cluster_data['shear_modulus'])
            if pd.isna(corr):
                corr = 0.0
            results.append({
                'cluster_id': cid,
                'size': len(cluster_data),
                'correlation': corr
            })
        else:
            results.append({
                'cluster_id': cid,
                'size': 1,
                'correlation': 0.0
            })
    
    corr_df = pd.DataFrame(results)
    return corr_df

def identify_decoupled_region(corr_df: pd.DataFrame) -> int:
    """Identify the cluster with the minimum correlation."""
    if corr_df.empty:
        raise ValueError("Correlation DataFrame is empty")
    min_idx = corr_df['correlation'].idxmin()
    min_cluster = corr_df.loc[min_idx, 'cluster_id']
    min_corr = corr_df.loc[min_idx, 'correlation']
    log_info_with_context(logger, f"Decoupled region identified: Cluster {min_cluster} with correlation {min_corr:.4f}")
    return int(min_cluster)

def flag_high_variance_regions(df: pd.DataFrame, threshold: float = 0.0) -> pd.DataFrame:
    """Flag regions where prediction variance exceeds threshold (placeholder for FR-006)."""
    # Placeholder: In a real scenario, we would calculate variance of predictions per cluster.
    # For now, we just mark all as compliant or based on a simple heuristic if variance data exists.
    df['high_variance_flag'] = False 
    return df

def run_sensitivity_analysis(df: pd.DataFrame, feature_cols: list, k: int) -> pd.DataFrame:
    """
    Implement sensitivity analysis for decoupling threshold.
    Requirement: Apply varying correlation thresholds to the *fixed* clustering result from T030.
    Do NOT re-run K-Means.
    Calculate robustness_score (variance of the size of the cluster with the minimum correlation across cutoffs).
    """
    if 'cluster_id' not in df.columns:
        # If clustering hasn't been run in this session, run it now (assuming k is provided or derived)
        # But task says "fixed clustering result from T030", so we assume df already has cluster_id.
        # If not, we must error or run T030 logic. Assuming T030 ran.
        raise ValueError("Input dataframe must contain 'cluster_id' from T030 clustering.")

    # 1. Calculate correlations for each cluster (fixed based on current df)
    cluster_corr_stats = calculate_cluster_correlations(df)
    
    # Identify the cluster that has the MINIMUM correlation globally (the "Decoupled Region")
    # This cluster ID is fixed for the sensitivity analysis.
    min_corr_idx = cluster_corr_stats['correlation'].idxmin()
    target_cluster_id = int(cluster_corr_stats.loc[min_corr_idx, 'cluster_id'])
    log_info_with_context(logger, f"Sensitivity Analysis: Targeting fixed decoupled cluster ID {target_cluster_id}")

    # 2. Sweep thresholds
    cutoffs = np.arange(0.50, 0.96, 0.05) # 0.5 to 0.95 inclusive
    results = []
    cluster_sizes = []

    for cutoff in cutoffs:
        # Filter clusters that have correlation <= cutoff (these are "decoupled" at this threshold)
        # However, the task asks to "Apply varying correlation thresholds to the *fixed* clustering result".
        # Interpretation: We look at the specific cluster identified as the minimum correlation cluster.
        # Does its correlation change? No, the data is fixed.
        # What changes is whether this cluster (or others) are *considered* decoupled.
        # The metric to track is the "size of the cluster with the minimum correlation".
        # Since the cluster ID is fixed (target_cluster_id), its size is constant.
        # Wait, the robustness_score is "variance of the size of the cluster with the minimum correlation".
        # If the cluster ID is fixed, the size is constant -> variance is 0.
        # Re-reading: "Apply varying correlation thresholds to the *fixed* clustering result... Calculate... robustness_score (variance of the size of the cluster with the minimum correlation across cutoffs)".
        
        # Alternative Interpretation:
        # At each cutoff, we re-identify the "Decoupled Region" as the cluster with the minimum correlation *that is also <= cutoff*?
        # Or maybe we look at all clusters with corr <= cutoff, and find the one with the min corr among them?
        # If we just filter by cutoff, the "cluster with minimum correlation" might change if we exclude the true minimum because it's > cutoff?
        # But the true minimum is the lowest. It will always be <= any cutoff >= its value.
        # If cutoff < min_correlation, then NO clusters are decoupled.
        
        # Let's assume the "cluster with the minimum correlation" refers to the one identified as the decoupled region *at that specific cutoff*.
        # i.e., Filter clusters where corr <= cutoff. Among those, pick the one with the lowest corr.
        # If no clusters satisfy corr <= cutoff, then the region size is 0.
        
        eligible_clusters = cluster_corr_stats[cluster_corr_stats['correlation'] <= cutoff]
        
        if eligible_clusters.empty:
            region_size = 0
            mean_corr = 0.0
            target_id = -1
        else:
            # Find the one with the absolute minimum correlation among eligible
            min_idx = eligible_clusters['correlation'].idxmin()
            target_id = int(eligible_clusters.loc[min_idx, 'cluster_id'])
            region_size = int(eligible_clusters.loc[min_idx, 'size'])
            mean_corr = eligible_clusters['correlation'].mean()
        
        cluster_sizes.append(region_size)
        results.append({
            'cutoff': cutoff,
            'region_size': region_size,
            'mean_correlation': mean_corr,
            'target_cluster_id': target_id
        })

    results_df = pd.DataFrame(results)
    
    # Calculate robustness score: variance of the size of the region across cutoffs
    if len(cluster_sizes) > 0:
        robustness_score = np.var(cluster_sizes)
    else:
        robustness_score = 0.0
        
    results_df['robustness_score'] = robustness_score
    
    log_info_with_context(logger, f"Sensitivity analysis complete. Robustness Score: {robustness_score:.4f}")
    return results_df

def save_results(df: pd.DataFrame, filepath: str):
    """Save results to CSV."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log_info_with_context(logger, f"Results saved to {filepath}")

def main():
    config = get_config()
    input_path = config.get('encoded_data_path', 'data/processed/encoded_alloys.csv')
    output_path = config.get('sensitivity_output_path', 'data/processed/sensitivity_analysis.csv')
    
    # Check if input exists
    if not os.path.exists(input_path):
        log_error_with_context(logger, f"Input file {input_path} not found. Run T015 (main.py) first.")
        sys.exit(1)

    try:
        # Load data
        df = load_encoded_data(input_path)
        feature_cols = get_feature_columns(df)
        
        if 'cluster_id' not in df.columns:
            log_info_with_context(logger, "Clustering not found in data. Running T030 logic (Elbow + KMeans) first.")
            optimal_k, _ = perform_elbow_method(df, feature_cols)
            df = perform_kmeans_clustering(df, feature_cols, optimal_k)
            # Save intermediate clustering results if needed (T030 output)
            # But T032 depends on T030, so we assume it might be there or run it if missing.
        
        # Run Sensitivity Analysis
        log_info_with_context(logger, "Starting Sensitivity Analysis (T032)...")
        sensitivity_results = run_sensitivity_analysis(df, feature_cols, k=None) # k not needed as clustering is fixed in df
        
        # Save results
        save_results(sensitivity_results, output_path)
        
        print(f"Sensitivity analysis complete. Output: {output_path}")
        
    except Exception as e:
        log_error_with_context(logger, f"Error during sensitivity analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()
