"""
Feature Engineering Module for Sleep Quality Prediction.
Implements:
1. Pairwise Pearson correlation
2. Fisher-z transformation
3. Upper-triangular vector extraction
4. Subject-level processing and saving
"""
import os
import sys
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging
from scipy.stats import pearsonr
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths
from utils.logging import setup_logging

def compute_pairwise_correlation(time_series: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Pearson correlation matrix from time series.
    
    Args:
        time_series: Array of shape (time_points, regions)
        
    Returns:
        Correlation matrix of shape (regions, regions)
    """
    n_regions = time_series.shape[1]
    corr_matrix = np.zeros((n_regions, n_regions))
    
    for i in range(n_regions):
        for j in range(i, n_regions):
            # Compute correlation
            corr, _ = pearsonr(time_series[:, i], time_series[:, j])
            corr_matrix[i, j] = corr
            corr_matrix[j, i] = corr
            
    return corr_matrix

def fisher_z_transform(r_value: float) -> float:
    """
    Apply Fisher-z transformation to a correlation coefficient.
    Handles edge cases where r is exactly 1 or -1.
    """
    # Clip to avoid math domain errors
    r_clipped = np.clip(r_value, -0.9999, 0.9999)
    return 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))

def extract_upper_triangular_vector(corr_matrix: np.ndarray) -> np.ndarray:
    """
    Extract the upper triangular part of a symmetric matrix as a vector.
    Excludes the diagonal.
    
    Args:
        corr_matrix: Symmetric matrix of shape (n, n)
        
    Returns:
        Vector of shape (n*(n-1)/2,)
    """
    n = corr_matrix.shape[0]
    # Get indices for upper triangle (excluding diagonal)
    rows, cols = np.triu_indices(n, k=1)
    return corr_matrix[rows, cols]

def process_subject_features(time_series: np.ndarray) -> np.ndarray:
    """
    Process a single subject's time series into a feature vector.
    1. Compute correlation matrix
    2. Apply Fisher-z transform
    3. Extract upper triangular vector
    
    Args:
        time_series: Array of shape (time_points, regions)
        
    Returns:
        Feature vector of shape (n_edges,)
    """
    # Step 1: Correlation
    corr_matrix = compute_pairwise_correlation(time_series)
    
    # Step 2: Fisher-z transform element-wise
    z_matrix = np.zeros_like(corr_matrix)
    for i in range(corr_matrix.shape[0]):
        for j in range(corr_matrix.shape[1]):
            z_matrix[i, j] = fisher_z_transform(corr_matrix[i, j])
            
    # Step 3: Extract vector
    feature_vector = extract_upper_triangular_vector(z_matrix)
    
    # Save feature vector
    output_path = os.path.join(output_dir, f"{subject_id}_features.npy")
    os.makedirs(output_dir, exist_ok=True)
    np.save(output_path, feature_vector)
    logger.info(f"Saved feature vector to {output_path} (shape: {feature_vector.shape})")
    
    return feature_vector

def save_feature_vector(subject_id: str, feature_vector: np.ndarray, paths: Dict) -> None:
    """
    Save a single subject's feature vector to disk.
    
    Args:
        subject_id: Subject identifier string
        feature_vector: The computed feature vector
        paths: Dictionary of paths from get_paths()
    """
    output_dir = paths['processed_dir']
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        
    output_file = output_dir / f"features_{subject_id}.npy"
    np.save(str(output_file), feature_vector)

def load_feature_vectors(subject_ids: List[str]) -> Tuple[np.ndarray, List[str]]:
    """
    Load all feature vectors for a list of subject IDs.
    
    Args:
        subject_ids: List of subject identifiers
        
    Returns:
        Tuple of (feature_matrix, valid_subject_ids)
        feature_matrix: Shape (n_subjects, n_features)
    """
    paths = get_paths()
    features_list = []
    valid_ids = []
    
    for sid in subject_ids:
        file_path = paths['processed_dir'] / f"features_{sid}.npy"
        if file_path.exists():
            vec = np.load(str(file_path))
            features_list.append(vec)
            valid_ids.append(sid)
        else:
            # Log warning if file missing
            print(f"Warning: Feature file not found for {sid}")
            
    if len(features_list) == 0:
        raise ValueError("No feature vectors loaded. Check if preprocessing produced time series.")
        
    feature_matrix = np.vstack(features_list)
    return feature_matrix, valid_ids

def main(subject_ids: Optional[List[str]] = None) -> bool:
    """
    Main entry point for feature engineering.
    Processes all provided subject IDs and saves feature vectors.
    
    Args:
        subject_ids: List of subject IDs to process. If None, attempts to load from filtered list.
        
    Returns:
        True on success, False on failure
    """
    paths = get_paths()
    logger = setup_logging(paths['log_file'])
    
    if subject_ids is None:
        # Fallback: try to load from filtered behavioral file if exists
        behavioral_path = paths['processed_dir'] / "filtered_behavioral.csv"
        if not behavioral_path.exists():
            logger.error("No subject list provided and filtered_behavioral.csv not found.")
            return False
        
        df = pd.read_csv(behavioral_path)
        # Normalize column names
        df.columns = [col.strip() for col in df.columns]
        subject_col = None
        for col in ['SubjectID', 'Subject', 'SubjID', 'subject_id']:
            if col in df.columns:
                subject_col = col
                break
        if subject_col is None:
            subject_col = df.columns[0]
        subject_ids = df[subject_col].astype(str).tolist()
        
    logger.info(f"Starting feature engineering for {len(subject_ids)} subjects")
    
    success_count = 0
    for i, sid in enumerate(subject_ids):
        try:
            # Load preprocessed time series
            # Expected path: data/processed/ts_{subject_id}.npy
            ts_path = paths['processed_dir'] / f"ts_{sid}.npy"
            if not ts_path.exists():
                logger.warning(f"Time series file not found for {sid}, skipping.")
                continue
                
            time_series = np.load(str(ts_path))
            
            # Process
            feature_vec = process_subject_features(time_series)
            
            # Save
            save_feature_vector(sid, feature_vec, paths)
            success_count += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(subject_ids)} subjects")
                
        except Exception as e:
            logger.error(f"Error processing subject {sid}: {str(e)}")
            continue
            
    logger.info(f"Feature engineering complete. Processed {success_count}/{len(subject_ids)} subjects.")
    return success_count > 0

if __name__ == "__main__":
    # Allow running directly with optional subject list argument
    # For simplicity, we assume it's called via main.py with a list
    # If called directly, it will try to find the filtered list
    success = main()
    sys.exit(0 if success else 1)
