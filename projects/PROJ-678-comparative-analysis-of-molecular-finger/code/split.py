import numpy as np
import pandas as pd
import logging
import os
import json
from pathlib import Path
from rdkit import DataStructs
from rdkit.Chem import AllChem
from typing import List, Dict, Any, Tuple
from utils import setup_logging, init_random_seed, get_logger

logger = get_logger(__name__)

def load_fingerprints(input_path: str) -> Tuple[pd.DataFrame, List]:
    """Load fingerprints from a CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    morgan_fps = []
    maccs_fps = []
    
    for idx, row in df.iterrows():
        morgan_fp = np.frombuffer(bytes.fromhex(row['morgan_fp']), dtype=np.uint8)
        maccs_fp = np.frombuffer(bytes.fromhex(row['maccs_fp']), dtype=np.uint8)
        morgan_fps.append(morgan_fp)
        maccs_fps.append(maccs_fp)
    
    return df, morgan_fps

def calculate_tanimoto_distance(fp1: np.ndarray, fp2: np.ndarray) -> float:
    """Calculate Tanimoto distance (1 - similarity)."""
    bitvec1 = DataStructs.ExplicitBitVect(len(fp1))
    bitvec2 = DataStructs.ExplicitBitVect(len(fp2))
    
    # Convert numpy array to bit vector
    for i, val in enumerate(fp1):
        if val > 0:
            bitvec1.SetBit(i)
    for i, val in enumerate(fp2):
        if val > 0:
            bitvec2.SetBit(i)
    
    sim = DataStructs.TanimotoSimilarity(bitvec1, bitvec2)
    return 1.0 - sim

def greedy_maximal_dissimilarity_split(
    fingerprints: List[np.ndarray],
    n_folds: int = 5,
    threshold: float = 0.85,
    min_test_size: int = 20
) -> List[Dict[str, Any]]:
    """
    Perform 5-Fold Greedy Maximal Dissimilarity Split.
    
    For each fold:
    1. Initialize test set with compound furthest from mean of remaining.
    2. Iterate through remaining, selecting max min-distance to current test set.
    3. Add to test set if distance > threshold.
    4. Verify test set size >= min_test_size.
    """
    n_samples = len(fingerprints)
    all_indices = list(range(n_samples))
    results = []
    
    for fold in range(n_folds):
        logger.info(f"Processing fold {fold + 1}/{n_folds}")
        
        # For this fold, we'll select a test set
        # In a true CV, we'd rotate, but here we do independent splits for diversity check
        remaining = all_indices.copy()
        test_set = []
        
        # Step 1: Initialize with furthest from mean
        # Calculate mean fingerprint
        mean_fp = np.mean(fingerprints, axis=0)
        
        # Find index furthest from mean
        max_dist = -1
        furthest_idx = -1
        for idx in remaining:
            dist = calculate_tanimoto_distance(fingerprints[idx], mean_fp)
            if dist > max_dist:
                max_dist = dist
                furthest_idx = idx
        
        if furthest_idx != -1:
            test_set.append(furthest_idx)
            remaining.remove(furthest_idx)
        
        # Step 2: Greedy selection
        while remaining:
            max_min_dist = -1
            best_idx = -1
            
            for idx in remaining:
                # Calculate min distance to any point in test set
                min_dist = float('inf')
                for test_idx in test_set:
                    dist = calculate_tanimoto_distance(fingerprints[idx], fingerprints[test_idx])
                    if dist < min_dist:
                        min_dist = dist
                
                if min_dist > max_min_dist:
                    max_min_dist = min_dist
                    best_idx = idx
            
            # Step 3: Add if distance > threshold
            if max_min_dist > threshold:
                test_set.append(best_idx)
                remaining.remove(best_idx)
            else:
                # No more points satisfy threshold, stop
                break
        
        # Step 4: Verify size
        status = "VALID" if len(test_set) >= min_test_size else "INVALID"
        
        fold_result = {
            "fold": fold,
            "status": status,
            "test_indices": test_set,
            "train_indices": remaining
        }
        results.append(fold_result)
        
        logger.info(f"Fold {fold}: Test size = {len(test_set)}, Status = {status}")
        
        if status == "INVALID":
            logger.warning(f"Fold {fold} is INVALID: Test set size {len(test_set)} < {min_test_size}")
    
    return results

def verify_split_summary(splits: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """
    Aggregate split results into split_summary.json.
    If ANY fold fails, status is INVALID.
    """
    total_folds = len(splits)
    valid_folds = sum(1 for s in splits if s["status"] == "VALID")
    invalid_folds = total_folds - valid_folds
    status = "VALID" if invalid_folds == 0 else "INVALID"
    
    summary = {
        "total_folds": total_folds,
        "valid_folds": valid_folds,
        "invalid_folds": invalid_folds,
        "status": status
    }
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Split summary written to {output_path}: {summary}")
    return summary

def handle_invalid_split(summary: Dict[str, Any]) -> None:
    """
    If status is INVALID, write invalid_split_report.md and research_results.md.
    Then exit with code 0.
    """
    if summary["status"] != "INVALID":
        return
    
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Write invalid_split_report.md
    report_path = processed_dir / "invalid_split_report.md"
    with open(report_path, 'w') as f:
        f.write("# Invalid Split Report\n\n")
        f.write("## Statistical comparison is invalid due to insufficient structural diversity.\n\n")
        f.write(f"### Details\n")
        f.write(f"- Total Folds: {summary['total_folds']}\n")
        f.write(f"- Valid Folds: {summary['valid_folds']}\n")
        f.write(f"- Invalid Folds: {summary['invalid_folds']}\n")
        f.write(f"\nThe greedy maximal dissimilarity split failed to produce test sets of size >= 20\n")
        f.write(f"while maintaining Tanimoto distance > 0.85. This indicates insufficient structural\n")
        f.write(f"diversity in the dataset to support the required statistical comparison.\n")
    
    logger.info(f"Written invalid split report: {report_path}")
    
    # Write research_results.md with INVALID header
    results_path = processed_dir / "research_results.md"
    with open(results_path, 'w') as f:
        f.write("# Research Results\n\n")
        f.write("## STATISTICAL COMPARISON INVALID\n\n")
        f.write("Statistical comparison is invalid due to insufficient structural diversity.\n\n")
        f.write("### Reason\n")
        f.write("The 5-Fold Greedy Maximal Dissimilarity Split could not generate valid test sets\n")
        f.write("that satisfy the Tanimoto threshold (> 0.85) and minimum size (>= 20) requirements.\n")
        f.write("This indicates the dataset lacks sufficient structural diversity for the planned\n")
        f.write("comparative analysis of molecular fingerprints.\n\n")
        f.write("### Next Steps\n")
        f.write("1. Review dataset composition and consider expanding the chemical space.\n")
        f.write("2. Adjust the Tanimoto threshold or minimum test size if scientifically justified.\n")
        f.write("3. Re-run the pipeline after modifications.\n")
    
    logger.info(f"Written research results (INVALID): {results_path}")
    logger.info("Exiting with code 0 (success) as per invalid path handler.")

def main():
    """Main entry point for split.py."""
    setup_logging()
    init_random_seed(42)
    
    # Paths
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "organophosphates_filtered.csv"
    summary_path = project_root / "data" / "processed" / "split_summary.json"
    
    logger.info("Starting Greedy Maximal Dissimilarity Split")
    
    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load fingerprints
    df, fingerprints = load_fingerprints(str(input_path))
    logger.info(f"Loaded {len(fingerprints)} fingerprints")
    
    # Perform split
    splits = greedy_maximal_dissimilarity_split(fingerprints, n_folds=5, threshold=0.85, min_test_size=20)
    
    # Verify and write summary
    summary = verify_split_summary(splits, str(summary_path))
    
    # Handle invalid path if needed
    if summary["status"] == "INVALID":
        handle_invalid_split(summary)
        # Exit with 0 to allow pipeline to complete
        return 0
    
    # If valid, write individual fold files (for downstream training)
    for split_data in splits:
        fold_path = project_root / "data" / "processed" / f"split_fold_{split_data['fold']}.json"
        with open(fold_path, 'w') as f:
            json.dump(split_data, f, indent=2)
        logger.info(f"Written fold data: {fold_path}")
    
    logger.info("Split completed successfully")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
