import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.stats import gini

# Configure logging
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """Load parquet data from the specified path."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    logger.info(f"Loading data from {file_path}")
    return pd.read_parquet(path)

def identify_target_columns(df: pd.DataFrame) -> List[str]:
    """Identify target property columns (exclude composition and descriptors)."""
    # Assuming descriptors are numeric and target columns are specific known names
    # or non-composition columns. We'll filter for numeric columns that are likely targets.
    # Based on typical materials datasets, targets are often 'formation_energy', 'band_gap', etc.
    # For this implementation, we assume columns starting with 'target_' or specific known names.
    # However, a safer heuristic is to look for columns that are NOT in the descriptor set.
    # Since we don't have a schema here, we'll assume the 'composition' column is excluded
    # and the rest are potential targets or descriptors.
    # A robust way: if we have a known list of descriptors, exclude them.
    # For now, we assume the input to this function for targets is handled by T008a logic.
    # Here, we just return numeric columns that are not 'composition'.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'composition' in numeric_cols:
        numeric_cols.remove('composition')
    return numeric_cols

def calculate_gini(values: np.ndarray) -> float:
    """
    Calculate the Gini coefficient for an array of values.
    Handles negative values by taking absolute value as per common practice for inequality
    when direction doesn't matter, or by shifting to positive if necessary.
    Here we use absolute values to ensure non-negative inputs for Gini calculation.
    """
    if len(values) == 0:
        return 0.0
    # Ensure non-negative
    values = np.abs(values)
    if np.sum(values) == 0:
        return 0.0
    return gini(values)

def calculate_target_imbalance_score(df: pd.DataFrame, property_col: str) -> float:
    """
    Calculate Target Imbalance Score (Gini coefficient) for a specific property.
    Skips properties with < 100 samples.
    """
    if property_col not in df.columns:
        logger.warning(f"Property {property_col} not found in data, skipping.")
        return 0.0
    
    samples = df[property_col].dropna()
    if len(samples) < 100:
        logger.info(f"Skipping {property_col}: only {len(samples)} samples (< 100).")
        return 0.0
    
    return calculate_gini(samples.values)

def calculate_compositional_imbalance_score(df: pd.DataFrame, k_clusters: int = 50) -> float:
    """
    Calculate Compositional Imbalance Score.
    Step 1: Perform K-Means clustering (k=50) on compositional features.
    Step 2: Calculate Gini coefficient of the frequency of samples assigned to each cluster.
    
    Args:
        df: DataFrame containing compositional descriptors.
        k_clusters: Number of clusters for K-Means.
        
    Returns:
        Gini coefficient of cluster assignment counts.
    """
    logger.info(f"Calculating compositional imbalance score with k={k_clusters} clusters.")
    
    # Select numeric feature columns (descriptors)
    # Assuming the DataFrame contains only numeric descriptors for clustering
    # or we need to exclude non-numeric columns like 'composition' string.
    feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if 'composition' in feature_cols:
        feature_cols.remove('composition')
        
    if len(feature_cols) == 0:
        raise ValueError("No numeric feature columns found for clustering.")
    
    X = df[feature_cols].values
    
    # Handle missing values if any (replace with mean)
    if np.isnan(X).any():
        logger.warning("NaN values found in features. Replacing with column mean.")
        col_means = np.nanmean(X, axis=0)
        for i in range(X.shape[1]):
            col = feature_cols[i]
            mask = np.isnan(X[:, i])
            X[mask, i] = col_means[i]
    
    logger.info(f"Running K-Means clustering on {X.shape[0]} samples with {X.shape[1]} features.")
    
    # Perform K-Means clustering
    kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    
    # Calculate frequency of samples in each cluster
    unique, counts = np.unique(cluster_labels, return_counts=True)
    cluster_counts = counts
    
    # Calculate Gini coefficient of the cluster counts
    imbalance_score = calculate_gini(cluster_counts)
    
    logger.info(f"Compositional Imbalance Score: {imbalance_score:.4f}")
    logger.info(f"Cluster distribution (min: {np.min(cluster_counts)}, max: {np.max(cluster_counts)}, mean: {np.mean(cluster_counts):.2f})")
    
    return imbalance_score

def analyze_all_properties(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze imbalance for all target properties.
    Returns a dictionary mapping property name to imbalance score.
    """
    results = {}
    target_cols = identify_target_columns(df)
    
    for col in target_cols:
        score = calculate_target_imbalance_score(df, col)
        if score > 0:
            results[col] = score
            
    return results

def save_results(results: Dict[str, Any], output_path: str):
    """
    Save imbalance results to a CSV file.
    For compositional imbalance, results is a dict with a single key 'compositional' or similar.
    For target imbalance, results is a dict of property -> score.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    
    if isinstance(results, dict):
        # Check if it's a single score or multiple
        if len(results) == 1 and 'compositional' in results:
            # Single compositional score
            df_out = pd.DataFrame([
                {'score_type': 'compositional', 'score': results['compositional']}
            ])
        else:
            # Multiple target scores
            data = [{'property': k, 'score_type': 'target', 'score': v} for k, v in results.items()]
            df_out = pd.DataFrame(data)
    else:
        raise ValueError("Results must be a dictionary.")
    
    df_out.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df_out)} rows to {output_path}")

def main():
    """Main entry point for calculating imbalance scores."""
    # Paths
    data_path = "data/processed/descriptors.parquet"
    output_path = "results/compositional_imbalance_score.csv"
    
    # Ensure results directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        df = load_data(data_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns.")
    
    # Calculate compositional imbalance score
    try:
        compositional_score = calculate_compositional_imbalance_score(df, k_clusters=50)
    except Exception as e:
        logger.error(f"Error calculating compositional imbalance: {e}")
        sys.exit(1)
    
    # Save results
    results = {'compositional': compositional_score}
    save_results(results, output_path)
    
    logger.info("Compositional imbalance calculation completed successfully.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
