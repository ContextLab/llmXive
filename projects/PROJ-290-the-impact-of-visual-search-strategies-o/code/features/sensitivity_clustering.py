"""
Sensitivity Clustering Implementation (T024b)

Implements k-means clustering for k=2 and k=3 to generate labels for sensitivity analysis.
Outputs:
  - data/processed/labels_k2.csv
  - data/processed/labels_k3.csv
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from existing project modules
from config import get_config
from utils.logging import get_logger
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

def get_logger_wrapper():
    """Get a logger instance configured for this module."""
    config = get_config()
    return get_logger(__name__, config.log_level)

def load_processed_features(logger: logging.Logger, config: Any) -> pd.DataFrame:
    """
    Load the processed features from data/processed/features.csv.
    Expects the file to exist (produced by T019/T020).
    """
    features_path = config.data_processed_path / "features.csv"
    if not features_path.exists():
        logger.error(f"Processed features file not found at {features_path}. "
                     "Please run feature extraction tasks first.")
        raise FileNotFoundError(f"Missing features file: {features_path}")
    
    logger.info(f"Loading processed features from {features_path}")
    df = pd.read_csv(features_path)
    return df

def perform_sensitivity_clustering(
    df: pd.DataFrame,
    logger: logging.Logger,
    config: Any
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform k-means clustering for k=2 and k=3.
    
    Args:
        df: DataFrame containing processed features with columns for clustering.
        logger: Logger instance.
        config: Config object for paths.
        
    Returns:
        Tuple of (df_k2, df_k3) where each has an added 'cluster_label' column.
    """
    # Identify clustering features. Based on T018/T020, we expect:
    # fixation_duration_eye, fixation_duration_mouth, saccade_amplitude, dispersion
    # We use the continuous ratio as well if available, but standard features are safer.
    # Let's select numeric columns that are likely features, excluding metadata.
    
    feature_cols = [
        'fixation_duration_eye',
        'fixation_duration_mouth', 
        'saccade_amplitude',
        'dispersion',
        'eye_mouth_ratio' # From T020
    ]
    
    # Filter to only existing columns
    available_cols = [col for col in feature_cols if col in df.columns]
    
    if len(available_cols) < 2:
        logger.warning(f"Insufficient feature columns found. Available: {list(df.columns)}. "
                       "Using all numeric columns except 'participant_id' and 'cluster_label'."
                       )
        # Fallback: use all numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        exclude_cols = ['participant_id', 'cluster_label']
        available_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    logger.info(f"Using columns for clustering: {available_cols}")
    
    X = df[available_cols].dropna()
    original_indices = X.index
    
    # Handle missing values in features (drop rows with NaN in features)
    if len(X) < len(df):
        logger.warning(f"Dropped {len(df) - len(X)} rows due to NaN in feature columns.")
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    results = {}
    
    for k in [2, 3]:
        logger.info(f"Performing k-means clustering with k={k}")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)
        
        # Calculate silhouette score if we have enough points and clusters
        if len(X) > k and k > 1:
            try:
                score = silhouette_score(X_scaled, labels)
                logger.info(f"k={k}: Silhouette Score = {score:.4f}")
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score for k={k}: {e}")
                score = None
        else:
            score = None
        
        # Create a copy of the original dataframe and assign labels
        # We need to map the labels back to the original indices
        temp_df = df.copy()
        temp_df['cluster_label'] = np.nan
        temp_df.loc[original_indices, 'cluster_label'] = labels
        
        results[k] = {
            'df': temp_df,
            'silhouette_score': score,
            'model': kmeans
        }
        
    return results[2]['df'], results[3]['df']

def save_clustering_results(
    df_k2: pd.DataFrame,
    df_k3: pd.DataFrame,
    logger: logging.Logger,
    config: Any
) -> None:
    """
    Save the clustering results to data/processed/labels_k2.csv and labels_k3.csv.
    """
    output_dir = config.data_processed_path
    output_dir.mkdir(parents=True, exist_ok=True)
    
    path_k2 = output_dir / "labels_k2.csv"
    path_k3 = output_dir / "labels_k3.csv"
    
    logger.info(f"Saving k=2 labels to {path_k2}")
    df_k2.to_csv(path_k2, index=False)
    
    logger.info(f"Saving k=3 labels to {path_k3}")
    df_k3.to_csv(path_k3, index=False)
    
    if not path_k2.exists() or not path_k3.exists():
        raise IOError("Failed to write output files.")

def main():
    """Main entry point for T024b."""
    config = get_config()
    logger = get_logger_wrapper()
    
    logger.info("Starting Sensitivity Clustering (T024b)")
    
    try:
        # 1. Load data
        df = load_processed_features(logger, config)
        
        # 2. Perform clustering
        df_k2, df_k3 = perform_sensitivity_clustering(df, logger, config)
        
        # 3. Save results
        save_clustering_results(df_k2, df_k3, logger, config)
        
        logger.info("Sensitivity Clustering completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during clustering: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()