import numpy as np
import pandas as pd
import logging
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

from fingerprints import load_compounds, generate_all_fingerprints, calculate_tanimoto_similarity
from utils import setup_logging, init_random_seed, get_logger

# Constants
TANIMOTO_THRESHOLD = 0.85
TEST_SET_FRACTION = 0.20
MIN_TEST_SIZE = 20

logger = get_logger(__name__)

def load_fingerprints(input_csv: str) -> Tuple[pd.DataFrame, List]:
    """
    Load compounds from CSV and generate fingerprints.
    Returns DataFrame and list of RDKit fingerprints.
    """
    df = load_compounds(input_csv)
    fps = generate_all_fingerprints(df)
    return df, fps

def calculate_tanimoto_distance(fp1, fp2) -> float:
    """Calculate Tanimoto distance (1 - similarity)."""
    sim = calculate_tanimoto_similarity(fp1, fp2)
    return 1.0 - sim

def greedy_maximal_dissimilarity_split(
    fingerprints: List,
    threshold: float,
    max_test_size_ratio: float,
    min_test_size: int
) -> Tuple[List[int], List[int]]:
    """
    Perform a Single Greedy Maximal Dissimilarity Split.
    
    Algorithm:
    1. Initialize test set with the compound furthest from the mean of all compounds.
    2. Iterate through remaining compounds, selecting the one with max min-distance to current test set.
    3. Add to test set if distance > threshold and test set size < 20% of total.
    """
    n = len(fingerprints)
    if n == 0:
        return [], []
    
    # Calculate mean fingerprint (approximation for initialization)
    # Since we can't easily average RDKit fingerprints, we pick a random seed or the first one
    # A better heuristic: pick the one furthest from the median index or just start with index 0
    # Per spec: "furthest from the mean" -> we approximate mean by averaging bit counts if possible,
    # but for RDKit fingerprints, we'll pick the one with max distance to a random reference or just start with 0.
    # Let's pick index 0 as initial candidate, then find the one furthest from it.
    
    initial_candidate = 0
    max_dist = -1
    for i in range(1, n):
        d = calculate_tanimoto_distance(fingerprints[0], fingerprints[i])
        if d > max_dist:
            max_dist = d
            initial_candidate = i
    
    test_set = [initial_candidate]
    remaining = [i for i in range(n) if i != initial_candidate]
    
    max_test_size = int(n * max_test_size_ratio)
    
    while len(test_set) < max_test_size and remaining:
        # Find compound in remaining with max min-distance to current test set
        best_candidate = None
        best_min_dist = -1
        
        for idx in remaining:
            min_dist_to_test = float('inf')
            for t_idx in test_set:
                d = calculate_tanimoto_distance(fingerprints[idx], fingerprints[t_idx])
                if d < min_dist_to_test:
                    min_dist_to_test = d
            
            if min_dist_to_test > best_min_dist:
                best_min_dist = min_dist_to_test
                best_candidate = idx
        
        if best_candidate is None:
            break
        
        # Check threshold
        if best_min_dist > (1.0 - threshold): # Distance > 1 - similarity threshold
            test_set.append(best_candidate)
            remaining.remove(best_candidate)
        else:
            # If the best candidate is not far enough, we stop adding to test set
            # because we can't find any more that satisfy the diversity requirement
            break
    
    train_set = remaining
    return train_set, test_set

def verify_split_summary(train_indices: List[int], test_indices: List[int], fingerprints: List) -> Dict[str, Any]:
    """
    Verify the split:
    1. Test set size >= 20.
    2. NO compound in test set has Tanimoto similarity >= 0.85 to ANY compound in training set.
    """
    status = "VALID"
    tanimoto_min = 1.0
    tanimoto_max = 0.0
    
    if len(test_indices) < MIN_TEST_SIZE:
        status = "INVALID"
        logger.error(f"Test set size {len(test_indices)} is less than minimum {MIN_TEST_SIZE}")
    else:
        # Check pairwise similarities
        for t_idx in test_indices:
            for tr_idx in train_indices:
                sim = calculate_tanimoto_similarity(fingerprints[t_idx], fingerprints[tr_idx])
                tanimoto_min = min(tanimoto_min, sim)
                tanimoto_max = max(tanimoto_max, sim)
                if sim >= TANIMOTO_THRESHOLD:
                    status = "INVALID"
                    logger.error(f"Found similarity {sim} >= {TANIMOTO_THRESHOLD} between test {t_idx} and train {tr_idx}")
                    break
            if status == "INVALID":
                break
    
    return {
        "status": status,
        "test_indices": test_indices,
        "train_indices": train_indices,
        "tanimoto_min": float(tanimoto_min) if tanimoto_min != 1.0 else 0.0,
        "tanimoto_max": float(tanimoto_max)
    }

def handle_invalid_split(output_path: Path, message: str):
    """
    If split is invalid, write the required report files and exit.
    """
    # Write invalid_split_report.md
    report_path = output_path.parent / "invalid_split_report.md"
    with open(report_path, "w") as f:
        f.write(f"# Invalid Split Report\n\n")
        f.write(f"{message}\n")
    
    # Write research_results.md with the specific header
    results_path = output_path.parent / "research_results.md"
    with open(results_path, "w") as f:
        f.write(f"# Research Results\n\n")
        f.write(f"## STATISTICAL COMPARISON INVALID\n\n")
        f.write(f"{message}\n")
    
    logger.info(f"Written invalid split report to {report_path}")
    logger.info(f"Written research results to {results_path}")
    return True

def main():
    setup_logging()
    init_random_seed(42)
    
    input_csv = "data/processed/organophosphates_filtered.csv"
    output_json = "data/processed/split_indices.json"
    
    logger.info(f"Starting Greedy Maximal Dissimilarity Split")
    
    # Check if input file exists
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        raise FileNotFoundError(f"Input file not found: {input_csv}")
    
    # Load data and fingerprints
    df, fps = load_fingerprints(input_csv)
    logger.info(f"Loaded {len(df)} compounds")
    
    # Perform split
    train_indices, test_indices = greedy_maximal_dissimilarity_split(
        fps, 
        TANIMOTO_THRESHOLD, 
        TEST_SET_FRACTION, 
        MIN_TEST_SIZE
    )
    
    logger.info(f"Split complete: Train={len(train_indices)}, Test={len(test_indices)}")
    
    # Verify split
    split_result = verify_split_summary(train_indices, test_indices, fps)
    
    # Write split indices
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(split_result, f, indent=2)
    
    logger.info(f"Written split indices to {output_json}")
    
    # Handle invalid path
    if split_result["status"] == "INVALID":
        message = "Statistical comparison is invalid due to insufficient structural diversity."
        handle_invalid_split(output_path, message)
        logger.info("Split verification failed. Pipeline halted at T018c.")
        # Exit with code 0 as per spec to allow pipeline to complete gracefully
        return
    
    logger.info(f"Split verification passed: {split_result['status']}")

if __name__ == "__main__":
    main()