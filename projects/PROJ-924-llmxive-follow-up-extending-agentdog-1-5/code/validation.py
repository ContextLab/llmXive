import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from config import get_path, ensure_directories, RANDOM_SEED
from config import set_seed

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
    
    Returns:
        Cohen's d effect size.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def perform_statistical_test(group1: np.ndarray, group2: np.ndarray) -> Dict[str, Any]:
    """
    Perform statistical tests between two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
    
    Returns:
        Dictionary containing test results.
    """
    # Mann-Whitney U test
    u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
    
    # Cohen's d
    cohens_d = calculate_cohen_d(group1, group2)
    
    return {
        "p_value": p_value,
        "u_statistic": u_stat,
        "cohens_d": cohens_d,
        "group1_mean": np.mean(group1),
        "group2_mean": np.mean(group2),
        "group1_std": np.std(group1),
        "group2_std": np.std(group2),
        "group1_size": len(group1),
        "group2_size": len(group2)
    }

def load_ground_truth_for_validation() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load ground truth data for validation.
    
    Returns:
        Tuple of (drift_scores, ground_truth) DataFrames.
    """
    drift_scores_path = get_path("processed", "drift_scores.csv")
    ground_truth_path = get_path("processed", "gold_standard_proxy.csv")
    
    drift_scores = pd.read_csv(drift_scores_path)
    ground_truth = pd.read_csv(ground_truth_path)
    
    return drift_scores, ground_truth

def run_us01_validation() -> Dict[str, Any]:
    """
    Run US-01 validation: statistical validation of drift detection.
    
    Returns:
        Dictionary containing validation results.
    """
    # Load data
    drift_scores, ground_truth = load_ground_truth_for_validation()
    
    # Merge on log_id
    merged = pd.merge(drift_scores, ground_truth, on="log_id", how="inner")
    
    if len(merged) == 0:
        raise ValueError("No matching records found between drift scores and ground truth.")
    
    # Split by label
    novel_scores = merged[merged["mapped_label"] == "novel"]["drift_score"].values
    benign_scores = merged[merged["mapped_label"] == "benign"]["drift_score"].values
    
    if len(novel_scores) == 0 or len(benign_scores) == 0:
        raise ValueError("Insufficient samples for statistical testing.")
    
    # Perform tests
    results = perform_statistical_test(novel_scores, benign_scores)
    
    return results

def save_validation_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save validation results to a JSON file.
    
    Args:
        results: Validation results dictionary.
        output_path: Path to save the results.
    """
    ensure_directories([str(output_path.parent)])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def check_acceptance_criteria(results: Dict[str, Any]) -> bool:
    """
    Check if validation meets acceptance criteria.
    
    Args:
        results: Validation results dictionary.
    
    Returns:
        True if criteria are met, False otherwise.
    """
    p_value = results.get("p_value", 1.0)
    cohens_d = results.get("cohens_d", 0.0)
    
    return p_value < 0.05 and abs(cohens_d) >= 0.5

def main():
    """Main entry point for validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run validation for drift detection")
    parser.add_argument("--drift", type=str, help="Drift scores file")
    parser.add_argument("--ground_truth", type=str, help="Ground truth file")
    parser.add_argument("--annotations", type=str, help="Annotations file")
    parser.add_argument("--output", type=str, help="Output file for validation results")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(RANDOM_SEED)
    
    # Run validation
    print("Starting US-01 validation...")
    results = run_us01_validation()
    
    # Check acceptance criteria
    print("Checking acceptance criteria...")
    meets_criteria = check_acceptance_criteria(results)
    
    results["meets_criteria"] = meets_criteria
    
    # Save results
    output = Path(args.output) if args.output else get_path("processed", "us01_final_stats.json")
    save_validation_results(results, output)
    
    print(f"Saved validation results to {output}")
    
    if not meets_criteria:
        print("Validation FAILED: Acceptance criteria not met.")
        sys.exit(1)
    else:
        print("Validation PASSED: Acceptance criteria met.")

if __name__ == "__main__":
    main()
