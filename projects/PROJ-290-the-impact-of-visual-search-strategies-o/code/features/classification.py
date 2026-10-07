import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from config import get_config
from utils.logging import get_logger

def get_logger_wrapper(func):
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        return func(*args, logger=logger, **kwargs)
    return wrapper

def load_processed_features(logger: logging.Logger) -> pd.DataFrame:
    """Load the processed features CSV."""
    config = get_config()
    features_path = config.PROCESSED_FEATURES_PATH
    if not os.path.exists(features_path):
        logger.error(f"Processed features file not found: {features_path}")
        raise FileNotFoundError(f"Processed features file not found: {features_path}")
    logger.info(f"Loading processed features from {features_path}")
    return pd.read_csv(features_path)

def calculate_continuous_ratio(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Calculate the continuous ratio of eye-to-mouth fixation time.
    Appends the result to the DataFrame.
    """
    if 'fixation_eye_duration' not in df.columns or 'fixation_mouth_duration' not in df.columns:
        logger.error("Required columns 'fixation_eye_duration' or 'fixation_mouth_duration' missing.")
        raise ValueError("Missing required fixation duration columns.")

    df = df.copy()
    # Avoid division by zero
    df['fixation_mouth_duration'] = df['fixation_mouth_duration'].replace(0, np.nan)
    df['eye_mouth_ratio'] = df['fixation_eye_duration'] / df['fixation_mouth_duration']
    
    mean_ratio = df['eye_mouth_ratio'].mean()
    if mean_ratio <= 0:
        logger.warning(f"Mean eye-to-mouth ratio is {mean_ratio:.4f} (<= 0). Proceeding with descriptive stats only.")
    
    logger.info(f"Calculated eye-mouth ratio. Mean: {mean_ratio:.4f}")
    return df

def perform_kmeans_clustering(df: pd.DataFrame, k: int = 2, logger: Optional[logging.Logger] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform k-means clustering on the eye-mouth ratio to identify strategies.
    
    Returns the DataFrame with cluster labels and a metrics dict.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    if 'eye_mouth_ratio' not in df.columns:
        logger.error("Column 'eye_mouth_ratio' not found in DataFrame.")
        raise ValueError("Column 'eye_mouth_ratio' not found.")

    # Prepare data for clustering (reshape for sklearn)
    X = df[['eye_mouth_ratio']].dropna()
    
    if len(X) < k:
        logger.warning(f"Insufficient data points ({len(X)}) for k={k} clustering.")
        # Assign all NaN or a default if possible, but strictly speaking we can't cluster
        labels = pd.Series([0] * len(df), index=df.index)
        metrics = {"silhouette_score": -1, "cluster_sizes": {0: len(df)}}
        return df.assign(cluster_strategy=labels), metrics

    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Map labels back to original index, filling NaNs where data was missing
    full_labels = pd.Series(index=df.index, dtype=int)
    full_labels[X.index] = labels
    full_labels = full_labels.fillna(-1).astype(int) # -1 for missing ratio data

    # Calculate silhouette score only if we have at least 2 clusters in the valid data
    unique_labels = np.unique(labels)
    if len(unique_labels) > 1:
        score = silhouette_score(X, labels)
    else:
        score = -1.0
        logger.warning("Only one cluster formed; silhouette score undefined (set to -1.0).")

    # Check cluster sizes
    cluster_counts = pd.Series(labels).value_counts()
    min_cluster_size = cluster_counts.min() if len(cluster_counts) > 0 else 0
    cluster_sizes = cluster_counts.to_dict()

    # Add to dataframe
    df_with_labels = df.copy()
    df_with_labels['cluster_strategy'] = full_labels

    metrics = {
        "silhouette_score": float(score),
        "cluster_sizes": {int(k): int(v) for k, v in cluster_sizes.items()},
        "min_cluster_size": min_cluster_size,
        "k": k
    }

    return df_with_labels, metrics

def perform_bootstrap_stability_check(df: pd.DataFrame, n_iterations: int = 100, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Perform bootstrap stability check for clustering labels.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Starting bootstrap stability check with {n_iterations} iterations.")
    
    if 'eye_mouth_ratio' not in df.columns:
        logger.error("Column 'eye_mouth_ratio' not found.")
        return {}

    X = df[['eye_mouth_ratio']].dropna()
    if len(X) < 2:
        logger.warning("Not enough data for bootstrap stability check.")
        return {}

    stability_scores = []
    
    for i in range(n_iterations):
        # Sample with replacement
        sample_indices = np.random.choice(X.index, size=len(X), replace=True)
        X_sample = X.loc[sample_indices]
        
        kmeans = KMeans(n_clusters=2, random_state=i, n_init=10)
        labels = kmeans.fit_predict(X_sample)
        
        if len(np.unique(labels)) > 1:
            score = silhouette_score(X_sample, labels)
            stability_scores.append(score)
        else:
            stability_scores.append(-1.0)
    
    avg_stability = np.mean([s for s in stability_scores if s != -1.0])
    std_stability = np.std([s for s in stability_scores if s != -1.0])
    
    logger.info(f"Bootstrap stability check complete. Avg Silhouette: {avg_stability:.4f}, Std: {std_stability:.4f}")
    
    return {
        "avg_silhouette": float(avg_stability),
        "std_silhouette": float(std_stability),
        "iterations": n_iterations
    }

def save_ratio_features(df: pd.DataFrame, logger: logging.Logger):
    """Save the features with ratio to the processed CSV."""
    config = get_config()
    output_path = config.PROCESSED_FEATURES_PATH
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved features with ratio to {output_path}")

def main():
    """
    Main entry point for T020/T022 logic.
    Calculates ratio, performs clustering, and handles T022 warning logic.
    """
    logger = get_logger(__name__)
    logger.info("Starting feature classification pipeline (Ratio & Clustering).")
    
    try:
        df = load_processed_features(logger)
        
        # 1. Calculate Continuous Ratio
        df = calculate_continuous_ratio(df, logger)
        
        # 2. Perform Clustering (T021)
        # We use k=2 as per T021, but T024b handles k=3 separately if needed.
        # For T022, we check the result of this clustering.
        df_clustered, metrics = perform_kmeans_clustering(df, k=2, logger=logger)
        
        # 3. T022: Warning Logic
        silhouette = metrics.get('silhouette_score', -1.0)
        min_size = metrics.get('min_cluster_size', 0)
        
        warning_triggered = False
        warning_reasons = []
        
        if silhouette < 0.25:
            warning_triggered = True
            warning_reasons.append(f"Silhouette score ({silhouette:.4f}) is < 0.25")
        
        if min_size < 5:
            warning_triggered = True
            warning_reasons.append(f"Minimum cluster size ({min_size}) is < 5")
        
        if warning_triggered:
            logger.warning("CLUSTERING WARNINGS TRIGGERED:")
            for reason in warning_reasons:
                logger.warning(f"  - {reason}")
            logger.warning("Proceeding with descriptive statistics only. Cluster labels may be unreliable for inference.")
            # Note: We still save the labels, but the downstream analysis (T029b) 
            # should ideally check these flags or rely on the continuous predictor (T029a).
            # The task specifically asks to log and proceed.
        else:
            logger.info("Clustering metrics acceptable. Proceeding with cluster-based analysis.")
        
        # Save the clustered dataframe (T019/T020 output extension)
        save_ratio_features(df_clustered, logger)
        
        # Save clustering metrics for reference
        metrics_path = Path(get_config().PROCESSED_FEATURES_PATH).parent / "clustering_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Saved clustering metrics to {metrics_path}")
        
        return df_clustered, metrics

    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()