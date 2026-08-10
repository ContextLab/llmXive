"""
Split module for generating K-Fold Split Indices using Greedy Maximal Dissimilarity.

This module implements the K-Fold Splitter (T018c) which generates K-Fold Split Indices
using Greedy Maximal Dissimilarity per fold.

Algorithm:
1. Load fingerprints from data/processed/fingerprints.pkl
2. For each fold k (0 to K-1):
   a. Identify the test fold (1/K of data) using Greedy Maximal Dissimilarity (Tanimoto < 0.85)
   b. Verify NO compound in the test fold has Tanimoto similarity >= 0.85 to ANY compound in the training fold
   c. If any fold fails the Tanimoto constraint, set status: INVALID
3. If VALID, write data/processed/kfold_split_indices.json
4. If INVALID, write data/processed/kfold_split_error.log and data/processed/kfold_split_invalid_report.md
"""

import numpy as np
import pandas as pd
import logging
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from rdkit import DataStructs
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import Chem
import pickle

from constants import TANIMOTO_THRESHOLD, N_FOLDS
from utils import setup_logging, init_random_seed, get_logger

logger = None

def load_fingerprints(fingerprint_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load fingerprints from pickle file.
    
    Args:
        fingerprint_path: Path to fingerprints.pkl
        
    Returns:
        Tuple of (morgan_fingerprints, maccs_fingerprints) as numpy arrays
    """
    if not os.path.exists(fingerprint_path):
        raise FileNotFoundError(f"Fingerprints file not found: {fingerprint_path}")
        
    with open(fingerprint_path, 'rb') as f:
        data = pickle.load(f)
        
    morgan_fps = data['morgan']
    maccs_fps = data['maccs']
    
    logger.info(f"Loaded {len(morgan_fps)} Morgan fingerprints")
    logger.info(f"Loaded {len(maccs_fps)} MACCS fingerprints")
    
    return morgan_fps, maccs_fps

def calculate_tanimoto_distance(fp1, fp2) -> float:
    """
    Calculate Tanimoto distance (1 - Tanimoto similarity) between two fingerprints.
    
    Args:
        fp1: First fingerprint (RDKit ExplicitBitVect or SparseBitVect)
        fp2: Second fingerprint
        
    Returns:
        Tanimoto distance (float)
    """
    similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
    return 1.0 - similarity

def greedy_maximal_dissimilarity_split(
    fingerprints: List,
    test_ratio: float,
    tanimoto_threshold: float,
    seed: int = 42
) -> Tuple[List[int], List[int], bool, str]:
    """
    Perform Greedy Maximal Dissimilarity Split.
    
    Algorithm:
    1. Initialize test set with the compound furthest from the mean of all compounds.
    2. Iterate through remaining compounds, selecting the one with max min-distance to current test set.
    3. Add to test set if distance > threshold and test set size < target size.
    
    Args:
        fingerprints: List of RDKit fingerprints
        test_ratio: Ratio of data to use for test set
        tanimoto_threshold: Maximum allowed Tanimoto similarity (distance >= 1 - threshold)
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (test_indices, train_indices, is_valid, error_message)
    """
    init_random_seed(seed)
    n_samples = len(fingerprints)
    target_test_size = int(n_samples * test_ratio)
    
    if target_test_size < 1:
        return [], list(range(n_samples)), False, "Target test size is 0"
    
    # Calculate distances to mean (using first fingerprint as proxy for mean)
    # Actually, we need to compute a "mean" fingerprint or use a different approach
    # For simplicity, we'll start with a random seed and then greedily select
    
    available_indices = list(range(n_samples))
    np.random.shuffle(available_indices)
    
    test_indices = []
    train_indices = []
    
    # Step 1: Initialize test set with the compound furthest from the mean
    # We'll use the first compound as a starting point and find the one furthest from it
    first_idx = available_indices.pop(0)
    test_indices.append(first_idx)
    
    # Step 2: Greedily select compounds with max min-distance to current test set
    while len(test_indices) < target_test_size and available_indices:
        best_idx = None
        best_min_distance = -1
        
        for idx in available_indices:
            fp = fingerprints[idx]
            min_distance = float('inf')
            
            for test_idx in test_indices:
                dist = calculate_tanimoto_distance(fp, fingerprints[test_idx])
                if dist < min_distance:
                    min_distance = dist
            
            if min_distance > best_min_distance:
                best_min_distance = min_distance
                best_idx = idx
        
        if best_idx is None:
            break
        
        # Check if distance meets threshold (distance >= 1 - tanimoto_threshold)
        if best_min_distance >= (1.0 - tanimoto_threshold):
            test_indices.append(best_idx)
            available_indices.remove(best_idx)
        else:
            # If no compound meets the threshold, we still need to fill the test set
            # Take the one with the best (highest) minimum distance even if below threshold
            test_indices.append(best_idx)
            available_indices.remove(best_idx)
    
    train_indices = available_indices
    
    # Verification: Check that no compound in test set has Tanimoto >= threshold to any in train set
    tanimoto_max = 0.0
    for test_idx in test_indices:
        for train_idx in train_indices:
            similarity = DataStructs.TanimotoSimilarity(
                fingerprints[test_idx], 
                fingerprints[train_idx]
            )
            if similarity > tanimoto_max:
                tanimoto_max = similarity
    
    is_valid = tanimoto_max < tanimoto_threshold
    error_message = ""
    
    if not is_valid:
        error_message = f"Tanimoto threshold violated: max similarity {tanimoto_max:.4f} >= {tanimoto_threshold}"
    
    return test_indices, train_indices, is_valid, error_message, tanimoto_max

def verify_split_summary(
    fingerprints: List,
    test_indices: List[int],
    train_indices: List[int],
    tanimoto_threshold: float
) -> Tuple[bool, str, float, float]:
    """
    Verify that the split satisfies the Tanimoto constraint.
    
    Args:
        fingerprints: List of RDKit fingerprints
        test_indices: Indices of test set
        train_indices: Indices of training set
        tanimoto_threshold: Maximum allowed Tanimoto similarity
        
    Returns:
        Tuple of (is_valid, error_message, min_distance, max_similarity)
    """
    tanimoto_min = float('inf')
    tanimoto_max = 0.0
    
    for test_idx in test_indices:
        for train_idx in train_indices:
            similarity = DataStructs.TanimotoSimilarity(
                fingerprints[test_idx], 
                fingerprints[train_idx]
            )
            tanimoto_max = max(tanimoto_max, similarity)
            tanimoto_min = min(tanimoto_min, 1.0 - similarity)  # Distance
    
    is_valid = tanimoto_max < tanimoto_threshold
    error_message = "" if is_valid else f"Tanimoto threshold violated: max similarity {tanimoto_max:.4f} >= {tanimoto_threshold}"
    
    return is_valid, error_message, tanimoto_min, tanimoto_max

def handle_invalid_split(error_reason: str, output_dir: str):
    """
    Handle invalid split by writing error log and invalid report.
    
    Args:
        error_reason: Reason for invalid split
        output_dir: Directory to write error files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write error log
    error_log_path = output_path / "kfold_split_error.log"
    with open(error_log_path, 'w') as f:
        f.write(f"K-Fold Split Invalid: {error_reason}\n")
    
    # Write invalid report
    report_path = output_path / "kfold_split_invalid_report.md"
    with open(report_path, 'w') as f:
        f.write("# K-Fold Split Invalid Report\n\n")
        f.write(f"**Status**: INVALID\n\n")
        f.write(f"**Reason**: {error_reason}\n\n")
        f.write("The K-Fold split failed to satisfy the Tanimoto < 0.85 constraint.\n")
        f.write("This violates Constitution VII requirements for structural diversity.\n")
    
    logger.error(f"K-Fold split invalid: {error_reason}")
    logger.error(f"Error log written to: {error_log_path}")
    logger.error(f"Invalid report written to: {report_path}")

def run_kfold_greedy_split(
    fingerprints: List,
    n_folds: int,
    tanimoto_threshold: float,
    seed: int = 42
) -> Tuple[Dict[str, Any], bool, str]:
    """
    Run K-Fold Greedy Maximal Dissimilarity Split.
    
    Args:
        fingerprints: List of RDKit fingerprints
        n_folds: Number of folds
        tanimoto_threshold: Maximum allowed Tanimoto similarity
        seed: Random seed
        
    Returns:
        Tuple of (split_data, is_valid, error_message)
    """
    n_samples = len(fingerprints)
    test_ratio = 1.0 / n_folds
    
    folds = []
    all_train_indices = set(range(n_samples))
    remaining_indices = list(range(n_samples))
    
    for fold_id in range(n_folds):
        logger.info(f"Generating fold {fold_id + 1}/{n_folds}")
        
        # Calculate target test size for this fold
        target_test_size = max(1, int(len(remaining_indices) * test_ratio))
        
        # Perform greedy split on remaining data
        test_indices, train_indices, is_valid, error_message, tanimoto_max = greedy_maximal_dissimilarity_split(
            [fingerprints[i] for i in remaining_indices],
            test_ratio,
            tanimoto_threshold,
            seed + fold_id
        )
        
        # Map indices back to original dataset
        original_test_indices = [remaining_indices[i] for i in test_indices]
        original_train_indices = [remaining_indices[i] for i in train_indices]
        
        # Verify the split
        subset_fps = [fingerprints[i] for i in remaining_indices]
        is_valid, error_message, tanimoto_min, tanimoto_max = verify_split_summary(
            subset_fps,
            test_indices,
            train_indices,
            tanimoto_threshold
        )
        
        if not is_valid:
            return {}, False, f"Fold {fold_id} failed: {error_message}"
        
        folds.append({
            "fold_id": fold_id,
            "train_indices": original_train_indices,
            "test_indices": original_test_indices,
            "tanimoto_min": float(tanimoto_min),
            "tanimoto_max": float(tanimoto_max)
        })
        
        # Remove test indices from remaining for next fold
        remaining_indices = [i for i in remaining_indices if i not in original_test_indices]
        
        logger.info(f"  Test set size: {len(original_test_indices)}")
        logger.info(f"  Train set size: {len(original_train_indices)}")
        logger.info(f"  Max Tanimoto similarity: {tanimoto_max:.4f}")
    
    split_data = {
        "status": "VALID",
        "folds": folds,
        "tanimoto_min": min(f["tanimoto_min"] for f in folds),
        "tanimoto_max": max(f["tanimoto_max"] for f in folds)
    }
    
    return split_data, True, ""

def main():
    """Main function to execute K-Fold Splitter."""
    global logger
    logger = setup_logging()
    init_random_seed(42)
    
    logger.info("Starting K-Fold Greedy Maximal Dissimilarity Split")
    
    # Paths
    project_root = Path(__file__).parent.parent
    fingerprints_path = project_root / "data" / "processed" / "fingerprints.pkl"
    output_dir = project_root / "data" / "processed"
    
    # Load fingerprints
    try:
        logger.info(f"Loading fingerprints from {fingerprints_path}")
        morgan_fps, maccs_fps = load_fingerprints(str(fingerprints_path))
        fingerprints = morgan_fps  # Using Morgan fingerprints for split
    except FileNotFoundError as e:
        logger.error(str(e))
        handle_invalid_split(str(e), str(output_dir))
        return
    
    # Run K-Fold split
    n_folds = N_FOLDS
    tanimoto_threshold = TANIMOTO_THRESHOLD
    
    logger.info(f"Running K-Fold split with K={n_folds}, Tanimoto threshold={tanimoto_threshold}")
    
    split_data, is_valid, error_message = run_kfold_greedy_split(
        fingerprints,
        n_folds,
        tanimoto_threshold,
        seed=42
    )
    
    if not is_valid:
        logger.error(f"K-Fold split failed: {error_message}")
        handle_invalid_split(error_message, str(output_dir))
        return
    
    # Write valid split
    output_path = output_dir / "kfold_split_indices.json"
    with open(output_path, 'w') as f:
        json.dump(split_data, f, indent=2)
    
    logger.info(f"K-Fold split successful!")
    logger.info(f"  Total folds: {len(split_data['folds'])}")
    logger.info(f"  Min Tanimoto distance: {split_data['tanimoto_min']:.4f}")
    logger.info(f"  Max Tanimoto similarity: {split_data['tanimoto_max']:.4f}")
    logger.info(f"Output written to: {output_path}")
    
    # Verify output
    with open(output_path, 'r') as f:
        verify_data = json.load(f)
        assert verify_data['status'] == 'VALID'
        assert len(verify_data['folds']) == n_folds
        
    logger.info("Verification passed!")

if __name__ == "__main__":
    main()