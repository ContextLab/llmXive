"""Feature Engineering: Compute connectivity matrices and extract vectors."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, log_operation

def compute_pairwise_correlation(time_series: np.ndarray) -> np.ndarray:
    """Compute pairwise Pearson correlation matrix."""
    log_stage_start("Compute Pairwise Correlation", {"shape": list(time_series.shape)})
    
    # time_series: (time, nodes)
    # correlation: (nodes, nodes)
    corr_matrix = np.corrcoef(time_series.T)
    
    # Handle NaNs (if constant signals)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
    
    log_stage_complete("Compute Pairwise Correlation")
    return corr_matrix

def fisher_z_transform(corr_matrix: np.ndarray) -> np.ndarray:
    """Apply Fisher-z transformation to correlation matrix."""
    log_stage_start("Fisher-z Transform")
    
    # z = 0.5 * ln((1+r)/(1-r))
    # Clip to avoid division by zero or log of negative
    r = np.clip(corr_matrix, -0.9999, 0.9999)
    z = 0.5 * np.log((1 + r) / (1 - r))
    
    log_stage_complete("Fisher-z Transform")
    return z

def extract_upper_triangular_vector(z_matrix: np.ndarray) -> np.ndarray:
    """Extract upper triangular vector (excluding diagonal) from matrix."""
    log_stage_start("Extract Upper Triangular Vector")
    
    n = z_matrix.shape[0]
    # Indices for upper triangle
    i, j = np.triu_indices(n, k=1)
    vector = z_matrix[i, j]
    
    log_stage_complete("Extract Upper Triangular Vector")
    return vector

def process_subject_features(subject_id: str, time_series_path: str, output_path: str) -> bool:
    """Process a single subject's time series into a feature vector."""
    log_stage_start("Process Subject Features", {"subject_id": subject_id})
    
    try:
        ts = np.load(time_series_path)
        
        corr = compute_pairwise_correlation(ts)
        z = fisher_z_transform(corr)
        vec = extract_upper_triangular_vector(z)
        
        np.save(output_path, vec)
        log_operation("Saved feature vector", subject=subject_id, path=output_path)
        log_stage_complete("Process Subject Features")
        return True
    except Exception as e:
        log_stage_error("Process Subject Features", str(e))
        return False

def process_all_subjects(subject_ids: List[str], processed_dir: str, features_dir: str) -> Dict[str, str]:
    """Process all subjects and save feature vectors."""
    log_stage_start("Feature Engineering", {"count": len(subject_ids)})
    
    ensure_dirs([features_dir])
    results = {}
    
    for sid in subject_ids:
        ts_path = os.path.join(processed_dir, f"{sid}_ts.npy")
        feat_path = os.path.join(features_dir, f"{sid}_features.npy")
        
        if os.path.exists(ts_path):
            success = process_subject_features(sid, ts_path, feat_path)
            if success:
                results[sid] = feat_path
        else:
            log_stage_error(f"Feature Engineering {sid}", "Time series not found")
    
    log_stage_complete("Feature Engineering")
    return results

def load_filtered_subjects(filtered_file: str) -> List[str]:
    """Load list of filtered subject IDs."""
    with open(filtered_file, "r") as f:
        return [line.strip() for line in f if line.strip()]

def main() -> bool:
    """CLI entry point."""
    paths = get_paths()
    processed_dir = str(paths["processed"])
    features_dir = str(paths["processed"] / "features") # Or data/processed/features
    ensure_dirs([features_dir])
    
    filtered_file = os.path.join(paths["raw"], "behavioral", "filtered_subjects.txt")
    if not os.path.exists(filtered_file):
        log_stage_error("Feature Engineering", "No filtered subjects found.")
        return False
    
    subject_ids = load_filtered_subjects(filtered_file)
    if not subject_ids:
        log_stage_error("Feature Engineering", "No subjects to process.")
        return False
    
    results = process_all_subjects(subject_ids, processed_dir, features_dir)
    return len(results) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
