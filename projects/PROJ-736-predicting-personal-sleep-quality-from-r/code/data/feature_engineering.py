"""Feature engineering module for computing connectivity vectors."""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error

def compute_pairwise_correlation(time_series: np.ndarray) -> np.ndarray:
    """Compute pairwise Pearson correlation matrix.
    
    Args:
        time_series: Time series matrix (ROIs x time)
        
    Returns:
        Correlation matrix (ROIs x ROIs)
    """
    # Normalize time series
    normalized = (time_series - np.mean(time_series, axis=1, keepdims=True)) / \
                (np.std(time_series, axis=1, keepdims=True) + 1e-8)
    
    # Compute correlation matrix
    corr_matrix = np.dot(normalized.T, normalized) / (normalized.shape[1] - 1)
    
    return corr_matrix

def fisher_z_transform(corr_matrix: np.ndarray) -> np.ndarray:
    """Apply Fisher-z transformation to correlation matrix.
    
    Args:
        corr_matrix: Correlation matrix
        
    Returns:
        Fisher-z transformed matrix
    """
    # Clip values to avoid log(0)
    corr_matrix = np.clip(corr_matrix, -0.9999, 0.9999)
    
    # Fisher-z transformation
    z_matrix = 0.5 * np.log((1 + corr_matrix) / (1 - corr_matrix))
    
    return z_matrix

def extract_upper_triangular_vector(z_matrix: np.ndarray) -> np.ndarray:
    """Extract upper triangular vector from correlation matrix.
    
    Args:
        z_matrix: Fisher-z transformed matrix
        
    Returns:
        Upper triangular vector (excluding diagonal)
    """
    n = z_matrix.shape[0]
    # Number of upper triangular elements (excluding diagonal)
    n_features = n * (n - 1) // 2
    
    features = np.zeros(n_features)
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            features[idx] = z_matrix[i, j]
            idx += 1
            
    return features

def process_subject_features(subject_id: str) -> bool:
    """Process features for a single subject.
    
    Args:
        subject_id: HCP subject ID
        
    Returns:
        True if successful, False otherwise
    """
    paths = get_paths()
    processed_dir = paths.get("processed", "data/processed")
    features_dir = paths.get("features", "data/processed/features")
    
    # Input and output paths
    input_path = os.path.join(processed_dir, f"sub-{subject_id}_time_series.npy")
    output_path = os.path.join(features_dir, f"sub-{subject_id}_connectivity.npy")
    
    log_stage_start("Process Subject Features", {"subject_id": subject_id})
    
    try:
        # Load preprocessed time series
        if not os.path.exists(input_path):
            log_stage_error("Process Subject Features", f"Time series file not found: {input_path}")
            return False
            
        time_series = np.load(input_path)
        
        # Compute pairwise correlation
        log_stage_start("Compute Pairwise Correlation", {"shape": list(time_series.shape)})
        corr_matrix = compute_pairwise_correlation(time_series)
        
        # Apply Fisher-z transform
        log_stage_start("Fisher-z Transform")
        z_matrix = fisher_z_transform(corr_matrix)
        
        # Extract upper triangular vector
        log_stage_start("Extract Upper Triangular Vector")
        features = extract_upper_triangular_vector(z_matrix)
        
        # Save features
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        np.save(output_path, features)
        
        log_stage_complete("Process Subject Features")
        return True
        
    except Exception as e:
        log_stage_error("Process Subject Features", f"Exception: {str(e)}")
        return False

def process_all_subjects() -> bool:
    """Process features for all filtered subjects.
    
    Returns:
        True if all subjects processed successfully, False otherwise
    """
    paths = get_paths()
    
    log_stage_start("Feature Engineering", {"count": "all filtered subjects"})
    
    # Load filtered subjects list
    filtered_subjects_file = paths.get("filtered_subjects", "data/processed/filtered_subjects.json")
    
    if not os.path.exists(filtered_subjects_file):
        log_stage_error("Feature Engineering", "Filtered subjects file not found")
        return False
        
    with open(filtered_subjects_file, 'r') as f:
        filtered_subjects = json.load(f)
    
    if not filtered_subjects:
        log_stage_error("Feature Engineering", "No subjects to process")
        return False
    
    success_count = 0
    for subject_id in filtered_subjects:
        if process_subject_features(subject_id):
            success_count += 1
    
    success_rate = success_count / len(filtered_subjects)
    if success_rate < 0.8:
        log_stage_error("Feature Engineering", f"Success rate {success_rate:.2%} < 80%")
        return False
        
    log_stage_complete("Feature Engineering", {"processed": success_count, "total": len(filtered_subjects)})
    return True

def main() -> bool:
    """Main entry point for feature engineering."""
    return process_all_subjects()
