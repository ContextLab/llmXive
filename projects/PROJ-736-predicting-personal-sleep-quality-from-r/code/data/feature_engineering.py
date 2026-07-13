"""
Script for feature engineering on preprocessed fMRI data.
Computes pairwise correlations, applies Fisher-z transform, and extracts upper-triangular vectors.
"""
import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error

def compute_pairwise_correlation(time_series: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Pearson correlation matrix from time series.
    ts: shape (time, nodes)
    Returns: shape (nodes, nodes) correlation matrix
    """
    # Center the data
    ts_centered = ts - np.mean(ts, axis=0)
    # Compute correlation
    corr_matrix = np.corrcoef(ts_centered, rowvar=False)
    return corr_matrix

def fisher_z_transform(r: np.ndarray) -> np.ndarray:
    """
    Apply Fisher-z transformation to correlation values.
    z = 0.5 * ln((1+r)/(1-r))
    """
    # Clip to avoid log(0) or log(negative)
    r_clipped = np.clip(r, -0.9999, 0.9999)
    z = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
    return z

def extract_upper_triangular_vector(corr_matrix: np.ndarray) -> np.ndarray:
    """
    Extract the upper triangular part of the correlation matrix (excluding diagonal).
    Returns a 1D vector of length n*(n-1)/2
    """
    n = corr_matrix.shape[0]
    # Get indices of upper triangle
    i, j = np.triu_indices(n, k=1)
    return corr_matrix[i, j]

def process_subject_features(subject_id: str, paths: Dict) -> np.ndarray:
    """
    Process a single subject's time series into a feature vector.
    """
    ts_path = paths['processed_dir'] / f"{subject_id}_ts.npy"
    if not ts_path.exists():
        raise FileNotFoundError(f"Time series file not found for {subject_id}")
    
    ts = np.load(ts_path)
    
    # Compute correlation
    corr = compute_pairwise_correlation(ts)
    
    # Fisher-z transform
    z = fisher_z_transform(corr)
    
    # Extract upper triangle
    vec = extract_upper_triangular_vector(z)
    
    return vec

def save_feature_vector(subject_id: str, vec: np.ndarray, paths: Dict):
    """Save feature vector to disk."""
    out_path = paths['processed_dir'] / f"{subject_id}_features.npy"
    np.save(out_path, vec)

def main(subject_ids: Optional[List[str]] = None) -> bool:
    """
    Load feature vectors for all subjects and stack into a matrix.
    Returns: (matrix, list_of_subject_ids)
    """
    paths = get_paths()
    vectors = []
    valid_subjects = []
    
    for subj in subjects:
        vec_path = paths['processed_dir'] / f"{subj}_features.npy"
        if vec_path.exists():
            vec = np.load(vec_path)
            vectors.append(vec)
            valid_subjects.append(subj)
        else:
            logging.warning(f"Feature vector not found for {subj}")
    
    if not vectors:
        raise ValueError("No feature vectors loaded.")
    
    matrix = np.vstack(vectors)
    return matrix, valid_subjects

def main(subjects: List[str]):
    """
    Main entry point for feature engineering.
    Processes all specified subjects.
    """
    paths = get_paths()
    ensure_dirs()
    
    logger = setup_logging(paths['log_file'])
    log_stage_start(logger, "Feature Engineering")
    
    for subj in subjects:
        try:
            logger.info(f"Computing features for {subj}")
            vec = process_subject_features(subj, paths)
            save_feature_vector(subj, vec, paths)
        except Exception as e:
            logger.error(f"Failed to compute features for {subj}: {e}")
            continue
    
    log_stage_complete(logger, "Feature Engineering")
    return True

if __name__ == "__main__":
    sys.exit(0 if main([]) else 1)