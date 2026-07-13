"""
Feature engineering script for sleep quality prediction.
Computes pairwise correlations, Fisher-z transforms, and extracts upper triangular vectors.
"""
import os
import sys
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, setup_logging

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def compute_pairwise_correlation(ts: np.ndarray) -> np.ndarray:
    """
    Computes the Pearson correlation matrix for a time series.
    ts shape: (n_timepoints, n_rois)
    Returns: (n_rois, n_rois) correlation matrix
    """
    # Normalize
    ts_norm = ts - np.mean(ts, axis=0)
    ts_std = ts_norm / (np.std(ts_norm, axis=0) + 1e-8)
    
    corr_matrix = np.dot(ts_std.T, ts_std) / (ts_std.shape[0] - 1)
    return corr_matrix

def fisher_z_transform(r_matrix: np.ndarray) -> np.ndarray:
    """
    Applies Fisher-z transformation to correlation values.
    z = 0.5 * ln((1+r)/(1-r))
    """
    # Clip to avoid log(0)
    r_clipped = np.clip(r_matrix, -0.9999, 0.9999)
    z_matrix = 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))
    return z_matrix

def extract_upper_triangular_vector(z_matrix: np.ndarray) -> np.ndarray:
    """
    Extracts the upper triangular part of the symmetric matrix (excluding diagonal).
    """
    n = z_matrix.shape[0]
    # Create a mask for upper triangle
    mask = np.triu(np.ones((n, n)), k=1).astype(bool)
    vector = z_matrix[mask]
    return vector

def process_subject_features(subject_id: str, input_dir: str, output_dir: str) -> bool:
    """
    Processes features for a single subject.
    """
    input_path = os.path.join(input_dir, f"{subject_id}_processed.npy")
    output_path = os.path.join(output_dir, f"{subject_id}_features.npy")
    
    try:
        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}")
            return False
        
        # Load time series
        ts = np.load(input_path)
        
        # Compute correlation
        corr = compute_pairwise_correlation(ts)
        
        # Fisher-z transform
        z = fisher_z_transform(corr)
        
        # Extract upper triangle
        vec = extract_upper_triangular_vector(z)
        
        # Save
        np.save(output_path, vec)
        print(f"Features saved: {subject_id}")
        return True
        
    except Exception as e:
        print(f"Error processing {subject_id}: {e}")
        return False

def save_feature_vector(vec: np.ndarray, path: str) -> None:
    np.save(path, vec)

def load_feature_vectors(subjects: List[str], input_dir: str) -> Tuple[np.ndarray, List[str]]:
    """
    Loads feature vectors for a list of subjects.
    """
    features = []
    valid_subjects = []
    for sid in subjects:
        path = os.path.join(input_dir, f"{sid}_features.npy")
        if os.path.exists(path):
            features.append(np.load(path))
            valid_subjects.append(sid)
    return np.array(features), valid_subjects

def main() -> int:
    """
    Main entry point for feature engineering.
    """
    paths = get_paths()
    ensure_dirs(paths)
    
    input_dir = paths["data_processed"]
    output_dir = paths["data_processed"] # Save to same dir or a specific features dir
    subjects_file = paths["data_raw"] / "filtered_subjects.txt"
    
    ensure_dirs({"data_processed": output_dir})
    
    if not os.path.exists(subjects_file):
        print("No filtered subjects file found.")
        return 1
    
    with open(subjects_file, 'r') as f:
        subjects = [line.strip() for line in f if line.strip()]
    
    success_count = 0
    for sid in subjects:
        if process_subject_features(sid, str(input_dir), str(output_dir)):
            success_count += 1
    
    print(f"Feature engineering complete. {success_count}/{len(subjects)} subjects processed.")
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
