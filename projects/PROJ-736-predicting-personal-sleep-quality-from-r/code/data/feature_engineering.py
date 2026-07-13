import os
import sys
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging
from scipy.stats import pearsonr

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error

def compute_pairwise_correlation(time_series):
    """
    Compute pairwise Pearson correlation matrix from time series.
    time_series: shape (n_timepoints, n_regions)
    Returns: correlation matrix shape (n_regions, n_regions)
    """
    logger = logging.getLogger(__name__)
    n_timepoints, n_regions = time_series.shape
    logger.info(f"Computing pairwise correlations for {n_regions} regions")
    
    corr_matrix = np.zeros((n_regions, n_regions))
    
    for i in range(n_regions):
        for j in range(i, n_regions):
            r, _ = pearsonr(time_series[:, i], time_series[:, j])
            corr_matrix[i, j] = r
            corr_matrix[j, i] = r
    
    return corr_matrix

def fisher_z_transform(corr_matrix):
    """
    Apply Fisher-z transformation to correlation matrix.
    """
    logger = logging.getLogger(__name__)
    logger.info("Applying Fisher-z transformation")
    
    # Clip values to avoid log(0) or log(inf)
    corr_clipped = np.clip(corr_matrix, -0.9999, 0.9999)
    z_matrix = 0.5 * np.log((1 + corr_clipped) / (1 - corr_clipped))
    
    return z_matrix

def extract_upper_triangular_vector(z_matrix):
    """
    Extract upper triangular vector from correlation matrix (excluding diagonal).
    """
    logger = logging.getLogger(__name__)
    n = z_matrix.shape[0]
    
    # Create mask for upper triangle (excluding diagonal)
    mask = np.triu(np.ones((n, n)), k=1).astype(bool)
    vector = z_matrix[mask]
    
    logger.info(f"Extracted {len(vector)} edges from {n}x{n} matrix")
    return vector

def process_subject_features(subject_id, input_dir, output_dir):
    """
    Process a single subject:
    1. Load preprocessed time series
    2. Compute pairwise correlations
    3. Apply Fisher-z transform
    4. Extract upper triangular vector
    5. Save feature vector as .npy
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing features for subject: {subject_id}")
    
    # Load time series
    timeseries_path = os.path.join(input_dir, f"{subject_id}_timeseries.npy")
    if not os.path.exists(timeseries_path):
        raise FileNotFoundError(f"Time series file not found: {timeseries_path}")
    
    time_series = np.load(timeseries_path)
    
    # Compute correlations
    corr_matrix = compute_pairwise_correlation(time_series)
    
    # 2. Fisher Z
    z = fisher_z_transform(corr)
    
    # Extract upper triangle
    feature_vector = extract_upper_triangular_vector(z_matrix)
    
    # Save feature vector
    output_path = os.path.join(output_dir, f"{subject_id}_features.npy")
    os.makedirs(output_dir, exist_ok=True)
    np.save(output_path, feature_vector)
    logger.info(f"Saved feature vector to {output_path} (shape: {feature_vector.shape})")
    
    return feature_vector

def get_filtered_subject_list():
    """Load the list of filtered subjects from the CSV."""
    paths = get_paths()
    filtered_subjects_path = paths['filtered_subjects']
    
    if not os.path.exists(filtered_subjects_path):
        raise FileNotFoundError(f"Filtered subjects file not found: {filtered_subjects_path}")
    
    import pandas as pd
    df = pd.read_csv(filtered_subjects_path)
    return df['Subject'].tolist()

def load_feature_vectors(subject_ids, input_dir):
    """Load feature vectors for multiple subjects."""
    vectors = []
    for subject_id in subject_ids:
        path = os.path.join(input_dir, f"{subject_id}_features.npy")
        if os.path.exists(path):
          vectors.append(np.load(path))
    return np.array(vectors)

def save_feature_vector(subject_id, vector, output_dir):
    """Save a single feature vector."""
    output_path = os.path.join(output_dir, f"{subject_id}_features.npy")
    os.makedirs(output_dir, exist_ok=True)
    np.save(output_path, vector)
    return output_path

def main():
    """
    Main function to compute connectivity vectors for all filtered subjects.
    Loads preprocessed time series, computes correlations, and saves .npy files.
    """
    logger = logging.getLogger(__name__)
    paths = get_paths()
    ensure_dirs()
    
    try:
        # Get filtered subject list
        subject_ids = get_filtered_subject_list()
        logger.info(f"Processing features for {len(subject_ids)} subjects")
        
        input_dir = paths['preprocessed_data']
        output_dir = paths['processed_features']
        
        # Process each subject
        for subject_id in subject_ids:
            process_subject_features(subject_id, input_dir, output_dir)
        
        # Also save a combined matrix for modeling
        combined_vectors = load_feature_vectors(subject_ids, output_dir)
        combined_path = os.path.join(output_dir, "all_subjects_features.npy")
        np.save(combined_path, combined_vectors)
        logger.info(f"Saved combined feature matrix to {combined_path}")
        
        log_stage_complete("feature_engineering", f"Generated feature vectors for {len(subject_ids)} subjects")
        
    except Exception as e:
        log_stage_error("feature_engineering", str(e))
        raise

if __name__ == "__main__":
    main()
