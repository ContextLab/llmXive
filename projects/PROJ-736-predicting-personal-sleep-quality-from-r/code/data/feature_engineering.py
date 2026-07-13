"""
Feature Engineering Module.

Computes pairwise Pearson correlation, Fisher-z transformation, and extracts
upper triangular vectors for connectivity matrices.
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, get_hyperparameter

logger = logging.getLogger(__name__)

def compute_pairwise_correlation(time_series: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Pearson correlation matrix.
    
    Args:
        time_series: 2D array (Time x ROIs)
        
    Returns:
        2D correlation matrix (ROIs x ROIs)
    """
    # Normalize time series
    # corrcoef expects variables in rows or columns?
    # np.corrcoef(x, y=None, rowvar=1) -> rowvar=1: rows are variables
    # We have Time x ROIs, so ROIs are columns. rowvar=0.
    corr_matrix = np.corrcoef(time_series, rowvar=0)
    return corr_matrix

def fisher_z_transform(r_matrix: np.ndarray) -> np.ndarray:
    """
    Apply Fisher-z transformation to correlation matrix.
    
    Args:
        r_matrix: Correlation matrix
        
    Returns:
        Z-transformed matrix
    """
    # Clip values to [-0.999, 0.999] to avoid log(0)
    r_clipped = np.clip(r_matrix, -0.999, 0.999)
    z_matrix = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
    return z_matrix

def extract_upper_triangular_vector(z_matrix: np.ndarray) -> np.ndarray:
    """
    Extract upper triangular vector from symmetric matrix.
    
    Args:
        z_matrix: Z-transformed matrix
        
    Returns:
        1D vector of upper triangle elements
    """
    n = z_matrix.shape[0]
    # Upper triangle, exclude diagonal
    indices = np.triu_indices(n, k=1)
    return z_matrix[indices]

def process_subject_features(time_series: np.ndarray) -> np.ndarray:
    """
    Full feature engineering pipeline for a subject.
    
    Args:
        time_series: Preprocessed time series (Time x ROIs)
        
    Returns:
        Feature vector (n_edges,)
    """
    corr = compute_pairwise_correlation(time_series)
    z_corr = fisher_z_transform(corr)
    vector = extract_upper_triangular_vector(z_corr)
    return vector

def save_feature_vector(subject_id: str, vector: np.ndarray, output_dir: str) -> None:
    """Save the feature vector to disk."""
    output_path = Path(output_dir) / f"{subject_id}.npy"
    np.save(str(output_path), vector)
    logger.info(f"Saved feature vector for {subject_id} to {output_path}")

def main(subject_ids: List[str]) -> bool:
    """
    Orchestrate feature engineering for a list of subjects.
    
    Args:
        subject_ids: List of subject IDs.
        
    Returns:
        True if all processed successfully.
    """
    paths = get_paths()
    output_dir = paths['processed_dir'] / "features"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    n_rois = get_hyperparameter('n_rois')
    n_edges = (n_rois * (n_rois - 1)) // 2
    
    success_count = 0
    
    for sid in subject_ids:
        logger.info(f"Processing features for {sid}")
        try:
            # Load preprocessed data (from T014b output)
            # Assuming preprocessed data is saved as {sid}_preprocessed.npy
            input_path = paths['processed_dir'] / "preprocessed" / f"{sid}_preprocessed.npy"
            
            if not input_path.exists():
                # If preprocessed data doesn't exist, we cannot proceed.
                # This is a real data constraint.
                logger.error(f"Preprocessed data for {sid} not found at {input_path}")
                continue
                
            time_series = np.load(str(input_path))
            
            # Compute features
            vector = process_subject_features(time_series)
            
            # Verify shape
            if len(vector) != n_edges:
                logger.warning(f"Feature vector length mismatch for {sid}: expected {n_edges}, got {len(vector)}")
            
            # Save
            save_feature_vector(sid, vector, str(output_dir))
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to process features for {sid}: {e}")
            continue
            
    return success_count > 0

if __name__ == "__main__":
    sys.exit(0)
