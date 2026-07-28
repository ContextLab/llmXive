import numpy as np
import pandas as pd
import logging
import os
import json
from pathlib import Path
from rdkit import DataStructs
from rdkit.Chem import AllChem
from utils import setup_logging, init_random_seed, get_logger

logger = get_logger(__name__)

def load_fingerprints(input_path: str) -> tuple:
    """Load fingerprints and labels from the processed CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Expect columns: 'morgan_fp', 'maccs_fp', 'labels' (or specific endpoint columns)
    # We assume the CSV stores fingerprints as lists or strings that need conversion
    # For this implementation, we assume they are stored as lists of integers (0/1)
    
    morgan_fps = []
    maccs_fps = []
    
    for _, row in df.iterrows():
        # Convert list string or list to RDKit ExplicitBitVect
        morgan_list = eval(row['morgan_fp']) if isinstance(row['morgan_fp'], str) else row['morgan_fp']
        maccs_list = eval(row['maccs_fp']) if isinstance(row['maccs_fp'], str) else row['maccs_fp']
        
        morgan_fp = DataStructs.ExplicitBitVect(len(morgan_list))
        maccs_fp = DataStructs.ExplicitBitVect(len(maccs_list))
        
        for i, bit in enumerate(morgan_list):
            if bit:
                morgan_fp.SetBit(i)
        for i, bit in enumerate(maccs_list):
            if bit:
                maccs_fp.SetBit(i)
        
        morgan_fps.append(morgan_fp)
        maccs_fps.append(maccs_fp)
    
    labels = df.iloc[:, -1].values  # Assume last column is the target label
    return morgan_fps, maccs_fps, labels

def calculate_tanimoto_distance(fp1, fp2) -> float:
    """Calculate Tanimoto distance (1 - similarity)."""
    sim = DataStructs.TanimotoSimilarity(fp1, fp2)
    return 1.0 - sim

def greedy_maximal_dissimilarity_split(morgan_fps, tanimoto_threshold=0.85, test_ratio=0.2):
    """
    Perform a Single Greedy Maximal Dissimilarity Split.
    Algorithm:
    1. Initialize test set with the compound furthest from the mean of all compounds.
    2. Iterate through remaining compounds, selecting the one with max min-distance to current test set.
    3. Add to test set if distance > threshold and test set size < 20% of total.
    """
    n_total = len(morgan_fps)
    n_test_target = max(20, int(n_total * test_ratio))
    
    # Calculate mean fingerprint (approximate by averaging bit vectors)
    # Since we can't easily average bit vectors, we pick a random seed or the first one
    # A better approach: find the compound with the maximum average distance to all others
    distances_matrix = np.zeros((n_total, n_total))
    for i in range(n_total):
        for j in range(i + 1, n_total):
            dist = calculate_tanimoto_distance(morgan_fps[i], morgan_fps[j])
            distances_matrix[i, j] = dist
            distances_matrix[j, i] = dist
    
    # Find the compound furthest from the mean (max average distance)
    avg_distances = distances_matrix.mean(axis=1)
    initial_idx = np.argmax(avg_distances)
    
    test_indices = [initial_idx]
    remaining_indices = list(range(n_total))
    remaining_indices.remove(initial_idx)
    
    while len(test_indices) < n_test_target and remaining_indices:
        best_idx = None
        max_min_dist = -1.0
        
        for idx in remaining_indices:
            # Calculate min distance to current test set
            min_dist = min(calculate_tanimoto_distance(morgan_fps[idx], morgan_fps[t_idx]) for t_idx in test_indices)
            
            if min_dist > max_min_dist:
                max_min_dist = min_dist
                best_idx = idx
        
        if best_idx is not None and max_min_dist > (1 - tanimoto_threshold):
            # Add to test set if distance > threshold (1 - similarity > 1 - 0.85 => similarity < 0.85)
            # Wait, the condition is: Add if distance > threshold?
            # Tanimoto distance = 1 - Tanimoto similarity.
            # We want Tanimoto similarity < 0.85, so Tanimoto distance > 0.15.
            # The task says: "Add to test set if distance > threshold".
            # If threshold is 0.85 (similarity), then distance > 0.15.
            # But the variable name `tanimoto_threshold` usually refers to similarity.
            # Let's re-read: "Tanimoto < 0.85". So similarity < 0.85.
            # Distance = 1 - similarity > 0.15.
            # The code above checks `max_min_dist > (1 - tanimoto_threshold)`.
            # If tanimoto_threshold=0.85, then 1-0.85=0.15. Correct.
            
            test_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        else:
            # If no compound satisfies the distance threshold, we stop or pick the best anyway?
            # The task says: "Add to test set if distance > threshold".
            # If we can't find one, we might stop.
            break
    
    train_indices = [i for i in range(n_total) if i not in test_indices]
    
    return train_indices, test_indices

def verify_split_summary(morgan_fps, train_indices, test_indices, tanimoto_threshold=0.85):
    """
    Verify the split:
    1. Test set size >= 20.
    2. NO compound in test set has Tanimoto similarity >= 0.85 to ANY compound in training set.
    """
    if len(test_indices) < 20:
        return False, "Test set size < 20"
    
    for t_idx in test_indices:
        for tr_idx in train_indices:
            sim = DataStructs.TanimotoSimilarity(morgan_fps[t_idx], morgan_fps[tr_idx])
            if sim >= tanimoto_threshold:
                return False, f"Similarity {sim} >= {tanimoto_threshold} found between test {t_idx} and train {tr_idx}"
    
    return True, "Valid split"

def handle_invalid_split(output_dir: str):
    """
    If split is invalid, write invalid_split_report.md and research_results.md.
    Then exit with code 0.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    invalid_report_path = output_path / "invalid_split_report.md"
    research_results_path = output_path / "research_results.md"
    
    message = "Statistical comparison is invalid due to insufficient structural diversity."
    
    # Write invalid_split_report.md
    with open(invalid_report_path, 'w') as f:
        f.write(f"# Invalid Split Report\n\n")
        f.write(f"{message}\n")
    
    # Write research_results.md
    with open(research_results_path, 'w') as f:
        f.write(f"# Research Results\n\n")
        f.write(f"## STATISTICAL COMPARISON INVALID\n\n")
        f.write(f"{message}\n")
    
    logger.info(f"Invalid split handled. Reports written to {invalid_report_path} and {research_results_path}")

def main():
    setup_logging()
    init_random_seed(42)
    
    input_path = "data/processed/organophosphates_filtered.csv"
    output_dir = "data/processed"
    tanimoto_threshold = 0.85
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info("Starting Greedy Maximal Dissimilarity Split")
    
    try:
        morgan_fps, maccs_fps, labels = load_fingerprints(input_path)
    except Exception as e:
        logger.error(f"Failed to load fingerprints: {e}")
        raise
    
    train_indices, test_indices = greedy_maximal_dissimilarity_split(morgan_fps, tanimoto_threshold)
    
    logger.info(f"Split complete. Train: {len(train_indices)}, Test: {len(test_indices)}")
    
    # Verify split
    is_valid, message = verify_split_summary(morgan_fps, train_indices, test_indices, tanimoto_threshold)
    
    split_summary = {
        "status": "VALID" if is_valid else "INVALID",
        "test_indices": test_indices,
        "train_indices": train_indices,
        "tanimoto_min": 0.0, # Placeholder, calculate if needed
        "tanimoto_max": 0.0  # Placeholder, calculate if needed
    }
    
    # Calculate min/max tanimoto for verification report
    if is_valid:
        min_sim = 1.0
        max_sim = 0.0
        for t_idx in test_indices:
            for tr_idx in train_indices:
                sim = DataStructs.TanimotoSimilarity(morgan_fps[t_idx], morgan_fps[tr_idx])
                if sim < min_sim: min_sim = sim
                if sim > max_sim: max_sim = sim
        split_summary["tanimoto_min"] = min_sim
        split_summary["tanimoto_max"] = max_sim
    
    output_path = Path(output_dir) / "split_indices.json"
    with open(output_path, 'w') as f:
        json.dump(split_summary, f, indent=2)
    
    logger.info(f"Split indices written to {output_path}")
    
    if not is_valid:
        logger.error(f"Split Verification Failed: {message}")
        handle_invalid_split(output_dir)
        # Exit with code 0 as per task requirement
        import sys
        sys.exit(0)
    
    logger.info("Split verification passed.")

if __name__ == "__main__":
    main()