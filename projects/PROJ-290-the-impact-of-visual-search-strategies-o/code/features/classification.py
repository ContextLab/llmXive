import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any

from utils.logging import get_logger
from config import get_config

def get_logger_wrapper(name: str = "classification") -> logging.Logger:
    return get_logger(name)

def calculate_continuous_ratio(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the continuous ratio of eye-to-mouth fixation time.
    Appends 'continuous_ratio' column to the dataframe.
    Handles division by zero and edge cases.
    """
    logger = get_logger_wrapper("classification")
    
    # Ensure columns exist
    if 'fixation_duration_eye' not in features_df.columns:
        logger.warning("Column 'fixation_duration_eye' not found. Creating with zeros.")
        features_df['fixation_duration_eye'] = 0.0
    if 'fixation_duration_mouth' not in features_df.columns:
        logger.warning("Column 'fixation_duration_mouth' not found. Creating with zeros.")
        features_df['fixation_duration_mouth'] = 0.0
    
    # Ensure numeric type
    features_df['fixation_duration_eye'] = pd.to_numeric(features_df['fixation_duration_eye'], errors='coerce').fillna(0.0)
    features_df['fixation_duration_mouth'] = pd.to_numeric(features_df['fixation_duration_mouth'], errors='coerce').fillna(0.0)
    
    # Calculate ratio: eye / mouth
    # If mouth is 0, the ratio is infinity (strong eye bias).
    # We replace 0 in denominator with NaN to get NaN, then handle inf.
    denom = features_df['fixation_duration_mouth'].replace(0, np.nan)
    ratio = features_df['fixation_duration_eye'] / denom
    
    # Handle division by zero (inf) -> set to a large number to indicate strong eye bias
    # Using 1000.0 as a proxy for infinity in this context
    ratio = ratio.replace([np.inf, -np.inf], 1000.0)
    
    # If both eye and mouth are 0, ratio was NaN/NaN -> NaN. Fill with 0.
    ratio = ratio.fillna(0.0)
    
    features_df['continuous_ratio'] = ratio
    
    mean_ratio = features_df['continuous_ratio'].mean()
    if mean_ratio <= 0:
        logger.warning(f"Mean continuous ratio is {mean_ratio} (<=0). Proceeding with descriptive stats only.")
    
    return features_df

def perform_kmeans_clustering(features_df: pd.DataFrame, k: int = 2) -> Tuple[pd.DataFrame, Dict]:
    """
    Perform k-means clustering on the continuous_ratio.
    Returns dataframe with cluster labels and metrics.
    """
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    
    logger = get_logger_wrapper("classification")
    
    if 'continuous_ratio' not in features_df.columns:
        logger.error("Column 'continuous_ratio' not found in features_df. Cannot cluster.")
        return features_df, {'silhouette': -1, 'success': False, 'error': 'missing_column'}
    
    X = features_df[['continuous_ratio']].values
    
    if len(X) < k:
        logger.warning(f"Not enough samples ({len(X)}) for k={k}. Skipping clustering.")
        return features_df, {'silhouette': -1, 'success': False, 'error': 'insufficient_samples'}
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    features_df['cluster_label'] = labels
    
    if len(np.unique(labels)) > 1:
        score = silhouette_score(X, labels)
    else:
        score = -1
        
    logger.info(f"Clustering (k={k}) completed. Silhouette score: {score:.3f}")
    
    metrics = {
        'k': k,
        'silhouette_score': float(score),
        'cluster_sizes': {int(l): int(np.sum(labels == l)) for l in np.unique(labels)}
    }
    
    if score < 0.25:
        logger.warning(f"Silhouette score {score:.3f} is low (<0.25). Clustering may be weak.")
        
    return features_df, metrics

def perform_bootstrap_stability_check(features_df: pd.DataFrame, n_iterations: int = 100) -> Dict:
    """
    Bootstrap stability check for clustering labels.
    Repeats clustering on bootstrap samples to assess label stability.
    """
    from sklearn.cluster import KMeans
    
    logger = get_logger_wrapper("classification")
    logger.info(f"Running bootstrap stability check ({n_iterations} iterations)...")
    
    if 'continuous_ratio' not in features_df.columns:
        logger.error("Cannot run stability check: 'continuous_ratio' column missing.")
        return {'status': 'failed', 'error': 'missing_column'}
    
    X = features_df[['continuous_ratio']].values
    n_samples = len(X)
    
    if n_samples < 2:
        logger.warning("Not enough samples for bootstrap stability check.")
        return {'status': 'skipped', 'reason': 'insufficient_samples'}
    
    # Store original labels if available, else generate initial clustering
    if 'cluster_label' in features_df.columns:
        original_labels = features_df['cluster_label'].values
    else:
        # Generate initial clustering if not present
        kmeans_init = KMeans(n_clusters=2, random_state=42, n_init=10)
        original_labels = kmeans_init.fit_predict(X)
    
    stability_scores = []
    
    for i in range(n_iterations):
        # Bootstrap sample indices
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_boot = X[indices]
        orig_subset = original_labels[indices]
        
        if len(np.unique(X_boot)) < 2:
            continue
            
        kmeans_boot = KMeans(n_clusters=2, random_state=42, n_init=10)
        labels_boot = kmeans_boot.fit_predict(X_boot)
        
        # Adjust for label switching (0->1, 1->0)
        # Calculate accuracy for both mappings
        acc1 = np.mean(labels_boot == orig_subset)
        acc2 = np.mean(labels_boot != orig_subset)
        stability = max(acc1, acc2)
        
        stability_scores.append(stability)
    
    if not stability_scores:
        return {
            'iterations': n_iterations,
            'stability_metric': 0.0,
            'status': 'failed',
            'reason': 'no_valid_samples'
        }
    
    return {
        'iterations': n_iterations,
        'stability_metric': float(np.mean(stability_scores)),
        'std_dev': float(np.std(stability_scores)),
        'status': 'completed'
    }

def save_ratio_features(features_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the features dataframe with ratio to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)
    logger = get_logger_wrapper("classification")
    logger.info(f"Saved ratio features to {output_path}")

def main():
    """
    Main entry point for classification module.
    Reads data/processed/features.csv, calculates continuous_ratio,
    appends it, and saves back to data/processed/features.csv.
    """
    logger = get_logger_wrapper("classification")
    logger.info("Starting classification module execution.")
    
    config = get_config()
    input_path = Path(config.PROCESSED_DATA_DIR) / "features.csv"
    output_path = Path(config.PROCESSED_DATA_DIR) / "features.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        features_df = pd.read_csv(input_path)
        logger.info(f"Loaded features from {input_path}. Shape: {features_df.shape}")
    except Exception as e:
        logger.error(f"Failed to load features: {e}")
        sys.exit(1)
    
    # Calculate continuous ratio
    features_df = calculate_continuous_ratio(features_df)
    
    # Save the updated features
    save_ratio_features(features_df, output_path)
    
    logger.info("Classification module execution completed successfully.")

if __name__ == "__main__":
    main()