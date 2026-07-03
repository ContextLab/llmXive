"""
Sensitivity Analysis Clustering Module.

Implements k-means clustering for k=2 and k=3 to generate labels
for sensitivity analysis as per T024b.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from project API
from utils.logging import get_logger
from config import get_config
from sklearn.cluster import KMeans

def get_logger_wrapper(name: str = __name__) -> logging.Logger:
    """Helper to get a configured logger."""
    return get_logger(name)

def perform_sensitivity_clustering(
    features_df: pd.DataFrame,
    k_values: List[int] = [2, 3],
    random_state: int = 42
) -> Dict[int, pd.DataFrame]:
    """
    Perform k-means clustering for specified k values on feature data.

    Args:
        features_df: DataFrame containing extracted features (must have 'participant_id', 'fixation_eye_ratio' or similar).
        k_values: List of k values to test (default [2, 3]).
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary mapping k value to a DataFrame with added cluster labels.
    """
    logger = get_logger()
    results = {}

    # Ensure we have necessary columns
    # The continuous ratio is calculated in T020/classification.py as 'eye_to_mouth_ratio'
    # We assume features_df has been enriched with this column or similar.
    # If not, we might need to calculate it here or rely on existing columns.
    # Based on T020, the column is likely 'eye_to_mouth_ratio' or similar.
    # Let's check for common names or calculate if missing.
    
    # Fallback: If 'eye_to_mouth_ratio' doesn't exist, try to calculate from raw fixation times if available.
    if 'eye_to_mouth_ratio' not in features_df.columns:
        # Try to find columns that might represent eye and mouth fixation
        eye_cols = [c for c in features_df.columns if 'eye' in c.lower() and 'fix' in c.lower()]
        mouth_cols = [c for c in features_df.columns if 'mouth' in c.lower() and 'fix' in c.lower()]
        
        if eye_cols and mouth_cols:
            # Use the first found
            eye_col = eye_cols[0]
            mouth_col = mouth_cols[0]
            features_df['eye_to_mouth_ratio'] = features_df[eye_col] / (features_df[mouth_col] + 1e-6)
            logger.info(f"Calculated eye_to_mouth_ratio from {eye_col} and {mouth_col}")
        else:
            # Fallback to using first numeric column if ratio not found
            numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) >= 2:
                features_df['eye_to_mouth_ratio'] = features_df[numeric_cols[0]] / (features_df[numeric_cols[1]] + 1e-6)
                logger.warning(f"Using {numeric_cols[0]} and {numeric_cols[1]} as proxy for ratio calculation")
            else:
                raise ValueError("Cannot perform clustering: No suitable numeric columns found to derive predictor.")

    predictor_col = 'eye_to_mouth_ratio'
    
    # Prepare data for clustering (exclude non-numeric and ID columns)
    # We only use the ratio for clustering in this sensitivity check
    X = features_df[[predictor_col]].values

    for k in k_values:
        logger.info(f"Performing k-means clustering with k={k}")
        
        kmeans = KMeans(
            n_clusters=k,
            random_state=random_state,
            n_init=10,
            algorithm='lloyd'
        )
        
        cluster_labels = kmeans.fit_predict(X)
        
        # Create a copy of the dataframe and add the labels
        result_df = features_df.copy()
        result_df[f'cluster_label_k{k}'] = cluster_labels
        
        # Log cluster sizes
        unique, counts = np.unique(cluster_labels, return_counts=True)
        logger.info(f"Cluster distribution for k={k}: {dict(zip(unique, counts))}")
        
        results[k] = result_df

    return results

def save_clustering_results(
    results: Dict[int, pd.DataFrame],
    output_dir: Path
) -> List[str]:
    """
    Save clustering results to CSV files.

    Args:
        results: Dictionary of k -> DataFrame with labels.
        output_dir: Directory to save files.

    Returns:
        List of paths to saved files.
    """
    saved_files = []
    
    for k, df in results.items():
        # Select only relevant columns for the output: participant_id, ratio, and the specific cluster label
        # Ensure participant_id exists
        if 'participant_id' not in df.columns:
            # Try to find an ID column
            id_cols = [c for c in df.columns if 'id' in c.lower()]
            if id_cols:
                id_col = id_cols[0]
            else:
                # Create a dummy ID if none exists
                df['participant_id'] = range(len(df))
                id_col = 'participant_id'
        
        # Select columns: ID, the predictor used, and the specific cluster label
        label_col = f'cluster_label_k{k}'
        output_cols = [id_col, 'eye_to_mouth_ratio', label_col]
        
        # Filter to only existing columns
        output_cols = [c for c in output_cols if c in df.columns]
        
        output_df = df[output_cols].copy()
        
        filename = f"labels_k{k}.csv"
        filepath = output_dir / filename
        
        output_df.to_csv(filepath, index=False)
        saved_files.append(str(filepath))
        logging.info(f"Saved clustering results for k={k} to {filepath}")
        
    return saved_files

def main():
    """
    Main entry point for T024b execution.
    """
    logger = get_logger()
    config = get_config()
    
    # Paths
    features_path = Path(config['paths']['data_processed']) / 'features.csv'
    output_dir = Path(config['paths']['data_processed'])
    
    logger.info(f"Starting sensitivity clustering (T024b)")
    logger.info(f"Loading features from {features_path}")
    
    if not features_path.exists():
        logger.error(f"Features file not found: {features_path}. Please run feature extraction first.")
        sys.exit(1)
    
    try:
        features_df = pd.read_csv(features_path)
        logger.info(f"Loaded {len(features_df)} rows of features.")
    except Exception as e:
        logger.error(f"Failed to load features: {e}")
        sys.exit(1)
    
    # Perform clustering for k=2 and k=3
    results = perform_sensitivity_clustering(features_df, k_values=[2, 3])
    
    # Save results
    saved_files = save_clustering_results(results, output_dir)
    
    logger.info(f"Sensitivity clustering completed. Files saved: {saved_files}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
