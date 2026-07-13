"""Feature engineering module for connectivity matrices."""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, get_logger

def compute_pairwise_correlation(ts: np.ndarray) -> np.ndarray:
    """
    Compute pairwise Pearson correlation matrix.
    
    Args:
        ts: Time series (n_timepoints, n_rois).
        
    Returns:
        Correlation matrix (n_rois, n_rois).
    """
    logger = get_logger()
    logger.log("correlation_computed", shape=ts.shape)
    
    # Compute correlation matrix
    corr_matrix = np.corrcoef(ts.T)
    return corr_matrix

def fisher_z_transform(corr_matrix: np.ndarray) -> np.ndarray:
    """
    Apply Fisher-z transformation to correlation matrix.
    
    Args:
        corr_matrix: Correlation matrix.
        
    Returns:
        Fisher-z transformed matrix.
    """
    logger = get_logger()
    logger.log("fisher_z_applied", shape=corr_matrix.shape)
    
    # Fisher-z: z = 0.5 * ln((1+r)/(1-r))
    # Clip to avoid division by zero
    r = np.clip(corr_matrix, -0.999, 0.999)
    z = 0.5 * np.log((1 + r) / (1 - r))
    return z

def extract_upper_triangular_vector(z_matrix: np.ndarray) -> np.ndarray:
    """
    Extract upper triangular vector (excluding diagonal).
    
    Args:
        z_matrix: Fisher-z transformed matrix.
        
    Returns:
        Vector of upper triangular elements.
    """
    logger = get_logger()
    logger.log("upper_triangular_extracted", shape=z_matrix.shape)
    
    n = z_matrix.shape[0]
    # Indices for upper triangle (excluding diagonal)
    i, j = np.triu_indices(n, k=1)
    return z_matrix[i, j]

def process_subject_features(subject_id: str, processed_dir: Path, results_dir: Path) -> bool:
    """
    Process features for a single subject.
    
    Args:
        subject_id: Subject ID.
        processed_dir: Directory with preprocessed data.
        results_dir: Directory to save feature vectors.
        
    Returns:
        True if successful, False otherwise.
    """
    logger = get_logger()
    log_stage_start(f"Features {subject_id}")
    
    try:
        # Load preprocessed time series
        input_path = processed_dir / f"{subject_id}_preprocessed.npy"
        if not input_path.exists():
            logger.log("preprocessed_missing", subject=subject_id)
            return False
        
        ts = np.load(str(input_path))
        
        # Compute correlation matrix
        corr = compute_pairwise_correlation(ts)
        
        # Fisher-z transform
        z = fisher_z_transform(corr)
        
        # Extract upper triangular vector
        vec = extract_upper_triangular_vector(z)
        
        # Save feature vector
        output_path = results_dir / f"{subject_id}_features.npy"
        np.save(str(output_path), vec)
        
        logger.log("features_saved", path=str(output_path), shape=vec.shape)
        log_stage_complete(f"Features {subject_id}")
        return True
        
    except Exception as e:
        log_stage_error(f"Features {subject_id}", error=str(e))
        return False

def save_feature_vector(vec: np.ndarray, output_path: Path) -> None:
    """Save feature vector to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(output_path), vec)

def main() -> bool:
    """Main entry point for feature engineering."""
    logger = get_logger()
    log_stage_start("Feature Engineering")
    
    try:
        paths = get_paths()
        processed_dir = paths["processed"]
        results_dir = paths["results"]
        
        # Ensure results directory exists
        ensure_dirs(paths)
        
        # Load filtered subjects
        filtered_file = processed_dir / "filtered_subjects.json"
        if not filtered_file.exists():
            raise FileNotFoundError("Filtered subjects file not found.")
        
        with open(filtered_file, "r") as f:
            subjects = json.load(f)
        
        logger.log("subjects_to_process", count=len(subjects))
        
        success_count = 0
        for subject in subjects:
            if process_subject_features(subject, processed_dir, results_dir):
                success_count += 1
        
        logger.log("feature_engineering_complete", success=success_count, total=len(subjects))
        
        log_stage_complete("Feature Engineering")
        return True
        
    except Exception as e:
        log_stage_error("Feature Engineering", error=str(e))
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
