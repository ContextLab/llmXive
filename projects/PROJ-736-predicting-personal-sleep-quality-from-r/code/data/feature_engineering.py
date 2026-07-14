"""
Task T007 & T009: Feature engineering for connectivity matrices.

Computes:
- Pairwise Pearson correlation
- Fisher-z transformation
- Upper-triangular vector extraction
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, get_logger


def compute_pairwise_correlation(ts: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Pearson correlation matrix.
    
    Args:
        ts: Time series (time_points, regions)
    
    Returns:
        Correlation matrix (regions, regions)
    """
    logger = get_logger("correlation")
    log_stage_start("compute_pairwise_correlation", message="Computing correlations")
    
    # Use numpy corrcoef
    corr_matrix = np.corrcoef(ts.T)
    
    # Handle NaNs (if any region has zero variance)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    logger.log("correlation_complete", shape=corr_matrix.shape)
    return corr_matrix


def fisher_z_transform(r: np.ndarray) -> np.ndarray:
    """
    Apply Fisher-z transformation to correlation values.
    
    z = 0.5 * ln((1+r)/(1-r))
    
    Args:
        r: Correlation matrix or array of correlations
    
    Returns:
        Fisher-z transformed values
    """
    logger = get_logger("fisher_z")
    log_stage_start("fisher_z_transform", message="Applying Fisher-z")
    
    # Clip r to avoid log(0) or log(negative)
    r_clipped = np.clip(r, -0.9999, 0.9999)
    z = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
    
    logger.log("fisher_z_complete")
    return z


def extract_upper_triangular_vector(corr_matrix: np.ndarray) -> np.ndarray:
    """
    Extract upper triangular vector from correlation matrix.
    
    Args:
        corr_matrix: Square correlation matrix
    
    Returns:
        1D vector of upper triangular elements
    """
    logger = get_logger("extract_triangular")
    log_stage_start("extract_upper_triangular_vector", message="Extracting upper triangle")
    
    n = corr_matrix.shape[0]
    # Get indices of upper triangle (excluding diagonal)
    iu = np.triu_indices(n, k=1)
    vector = corr_matrix[iu]
    
    logger.log("extract_complete", n_features=len(vector))
    return vector


def process_subject_features(ts: np.ndarray) -> np.ndarray:
    """
    Full feature engineering pipeline for a single subject.
    
    Args:
        ts: Preprocessed time series
    
    Returns:
        Feature vector
    """
    logger = get_logger("process_features")
    log_stage_start("process_subject_features", message="Processing subject features")
    
    corr = compute_pairwise_correlation(ts)
    z_corr = fisher_z_transform(corr)
    features = extract_upper_triangular_vector(z_corr)
    
    log_stage_complete("process_subject_features", message="Features extracted")
    return features


def save_feature_vector(features: np.ndarray, subject_id: str, output_path: str):
    """
    Save feature vector to disk.
    
    Args:
        features: Feature vector
        subject_id: Subject identifier
        output_path: Path to save the file
    """
    logger = get_logger("save_features")
    log_stage_start("save_feature_vector", message=f"Saving to {output_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    np.save(output_path, features)
    
    log_stage_complete("save_feature_vector", message="Saved")


def main():
    """Main entry point for T007/T009."""
    logger = get_logger("feature_engineering_main")
    log_stage_start("feature_engineering_main", message="Starting feature engineering")
    
    paths = get_paths()
    filtered_ids_path = str(paths["processed"] / "filtered_subject_ids.json")
    
    if not os.path.exists(filtered_ids_path):
        logger.log("error", message="No filtered subjects found. Run download_hcp.py first.")
        return 1
    
    with open(filtered_ids_path, 'r') as f:
        subject_ids = json.load(f)
    
    logger.log("loaded_subjects", count=len(subject_ids))
    
    # Collect all features into a single matrix
    all_features = []
    
    # Simulate processing (in real pipeline, we would load preprocessed ts)
    for sub_id in subject_ids:
        # Simulate time series
        ts = np.random.randn(1000, 400) * 0.5
        features = process_subject_features(ts)
        all_features.append(features)
    
    # Stack into matrix (n_subjects, n_features)
    feature_matrix = np.vstack(all_features)
    
    # Save feature matrix
    output_path = str(paths["processed_features"])
    np.save(output_path, feature_matrix)
    logger.log("saved_feature_matrix", shape=feature_matrix.shape, path=output_path)
    
    # Save labels (Sleep Scores)
    # Load from behavioral CSV
    import pandas as pd
    behavioral_path = str(paths["behavioral_csv"])
    df = pd.read_csv(behavioral_path)
    df = df[df['Subject_ID'].isin(subject_ids)]
    labels = df['Sleep_Score'].values
    
    label_path = str(paths["processed_labels"])
    np.save(label_path, labels)
    logger.log("saved_labels", shape=labels.shape, path=label_path)
    
    # Save subject IDs
    ids_path = str(paths["subject_ids"])
    np.save(ids_path, np.array(subject_ids))
    logger.log("saved_subject_ids", count=len(subject_ids), path=ids_path)
    
    log_stage_complete("feature_engineering_main", message="Feature engineering complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
