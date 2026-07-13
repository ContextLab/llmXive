"""
Feature engineering script for sleep quality prediction.
Computes pairwise correlations, Fisher-z transforms, and extracts upper triangular vectors.
"""
import os
import sys
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from scipy.stats import pearsonr

# Add project root to path for imports
import sys
from pathlib import Path as PPath
project_root = PPath(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, setup_logging

def compute_pairwise_correlation(ts: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Pearson correlation matrix for the time series.
    Input: (time, regions)
    Output: (regions, regions) correlation matrix
    """
    n_regions = ts.shape[1]
    corr_matrix = np.zeros((n_regions, n_regions))
    
    for i in range(n_regions):
        for j in range(i, n_regions):
            # Compute correlation
            corr, _ = pearsonr(ts[:, i], ts[:, j])
            corr_matrix[i, j] = corr
            corr_matrix[j, i] = corr
    
    corr_matrix = np.dot(ts_std.T, ts_std) / (ts_std.shape[0] - 1)
    return corr_matrix

def fisher_z_transform(r_matrix: np.ndarray) -> np.ndarray:
    """
    Apply Fisher-z transformation to the correlation matrix.
    z = 0.5 * ln((1+r)/(1-r))
    """
    # Clip values to avoid division by zero or log of negative
    r_clipped = np.clip(r_matrix, -0.9999, 0.9999)
    z_matrix = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
    return z_matrix

def extract_upper_triangular_vector(z_matrix: np.ndarray) -> np.ndarray:
    """
    Extract the upper triangular part of the matrix (excluding diagonal) as a vector.
    """
    n = z_matrix.shape[0]
    # Number of unique edges = n*(n-1)/2
    num_edges = n * (n - 1) // 2
    vector = np.zeros(num_edges)
    
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            vector[idx] = z_matrix[i, j]
            idx += 1
    
    return vector

def process_subject_features(subject_id: str) -> np.ndarray:
    """
    Process a single subject's time series into a connectivity vector.
    """
    paths = get_paths()
    processed_dir = paths['processed_dir']
    
    # Load preprocessed time series
    ts_path = processed_dir / f"sub-{subject_id}_ts.npy"
    if not ts_path.exists():
        raise FileNotFoundError(f"Preprocessed time series not found for {subject_id}")
    
    ts = np.load(ts_path)
    
    # Compute correlation
    corr_matrix = compute_pairwise_correlation(ts)
    
    # Fisher-z transform
    z_matrix = fisher_z_transform(corr_matrix)
    
    # Extract upper triangular vector
    feature_vector = extract_upper_triangular_vector(z_matrix)
    
    return feature_vector

def save_feature_vector(subject_id: str, vector: np.ndarray):
    """
    Save the feature vector to disk.
    """
    paths = get_paths()
    features_dir = paths['features_dir']
    features_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = features_dir / f"sub-{subject_id}_features.npy"
    np.save(output_path, vector)

def load_feature_vectors(subjects: List[str]) -> Tuple[np.ndarray, List[str]]:
    """
    Load all feature vectors for the given subjects.
    """
    paths = get_paths()
    features_dir = paths['features_dir']
    
    vectors = []
    valid_subjects = []
    
    for subject_id in subjects:
        fpath = features_dir / f"sub-{subject_id}_features.npy"
        if fpath.exists():
            vectors.append(np.load(fpath))
            valid_subjects.append(subject_id)
    
    if len(vectors) == 0:
        raise ValueError("No feature vectors found.")
    
    return np.array(vectors), valid_subjects

def main(subjects: List[str]):
    """
    Main function to compute features for all subjects.
    """
    logger = setup_logging(paths['log_file'])
    log_stage_start(logger, "Feature Engineering")
    
    paths = get_paths()
    ensure_dirs()
    
    for subject_id in subjects:
        try:
            logger.info(f"Computing features for {subject_id}")
            vector = process_subject_features(subject_id)
            save_feature_vector(subject_id, vector)
        except Exception as e:
            log_stage_error(logger, f"Feature Engineering {subject_id}", str(e))
            continue
    
    log_stage_complete(logger, "Feature Engineering", extra={"count": len(subjects)})
