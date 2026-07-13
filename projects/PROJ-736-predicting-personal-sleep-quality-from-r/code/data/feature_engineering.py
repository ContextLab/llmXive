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
from data.download_hcp import filter_subjects

def compute_pairwise_correlation(ts: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Pearson correlation matrix for a time series.
    ts: (n_timepoints, n_regions)
    Returns: (n_regions, n_regions) correlation matrix.
    """
    # Center the data
    ts_centered = ts - np.mean(ts, axis=0)
    # Correlation = cov(x, y) / (std(x) * std(y))
    # Using numpy corrcoef
    try:
        corr_matrix = np.corrcoef(ts, rowvar=False)
        # Handle NaNs (constant regions)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        return corr_matrix
    except Exception as e:
        log_stage_error("Correlation", str(e))
        return np.zeros((ts.shape[1], ts.shape[1]))

def fisher_z_transform(r_matrix: np.ndarray) -> np.ndarray:
    """
    Apply Fisher-z transformation to correlation matrix.
    z = 0.5 * ln((1+r)/(1-r))
    """
    # Clip values to avoid log(0) or log(negative)
    r = np.clip(corr_matrix, -0.9999, 0.9999)
    z = 0.5 * np.log((1 + r) / (1 - r))
    return z

def extract_upper_triangular_vector(z_matrix: np.ndarray) -> np.ndarray:
    """
    Extract upper triangular part (excluding diagonal) as a 1D vector.
    """
    n = z_matrix.shape[0]
    # indices of upper triangle
    iu = np.triu_indices(n, k=1)
    return z_matrix[iu]

def process_subject_features(subject_id: str) -> Optional[np.ndarray]:
    """
    Load preprocessed time series, compute connectivity, transform, and vectorize.
    """
    paths = get_paths()
    ts_path = os.path.join(paths['processed_timeseries'], f"sub-{subject_id}_ts.npy")
    
    if not os.path.exists(ts_path):
        log_stage_error("Feature Engineering", f"Time series not found for {subject_id}")
        return None
    
    ts = np.load(ts_path)
    
    # 1. Correlation
    corr = compute_pairwise_correlation(ts)
    
    # 2. Fisher Z
    z = fisher_z_transform(corr)
    
    # 3. Vectorize
    vec = extract_upper_triangular_vector(z)
    
    return vec

def save_feature_vector(subject_id: str, vector: np.ndarray):
    """Save feature vector to disk."""
    paths = get_paths()
    out_path = os.path.join(paths['processed_features'], f"sub-{subject_id}_features.npy")
    np.save(out_path, vector)

def load_feature_vectors(subject_ids: List[str]) -> Tuple[np.ndarray, List[str]]:
    """Load all feature vectors for a list of subjects."""
    paths = get_paths()
    vectors = []
    valid_ids = []
    
    for sid in subject_ids:
        path = os.path.join(paths['processed_features'], f"sub-{sid}_features.npy")
        if os.path.exists(path):
            vectors.append(np.load(path))
            valid_ids.append(sid)
    
    if not vectors:
        return np.array([]), []
    
    return np.vstack(vectors), valid_ids

def main():
    """
    Main entry point for feature engineering.
    Processes all valid subjects and saves feature vectors.
    """
    paths = get_paths()
    ensure_dirs()
    
    # Get valid subjects
    behavioral_path = paths['raw_behavioral']
    valid_subjects = filter_subjects(behavioral_path)
    
    if not valid_subjects:
        log_stage_error("Feature Engineering", "No valid subjects found.")
        return
    
    processed_count = 0
    for subject_id in valid_subjects:
        try:
            vec = process_subject_features(subject_id)
            if vec is not None:
                save_feature_vector(subject_id, vec)
                processed_count += 1
        except Exception as e:
            log_stage_error("Feature Engineering", f"Failed for {subject_id}: {e}")
            continue
    
    log_stage_complete("Feature Engineering", f"Processed {processed_count} subjects.")

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
