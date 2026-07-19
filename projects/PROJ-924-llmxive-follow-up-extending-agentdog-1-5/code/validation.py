"""
validation.py

Implements statistical validation logic for US-01 Independent Test verification.
Calculates p-values and Cohen's d to verify that drift scores for benign logs
are statistically distinguishable from novel attack logs.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from config import get_path, ensure_directories
from utils import load_json_file, save_json_file


def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values (e.g., benign logs)
        group2: Second group of values (e.g., attack logs)
        
    Returns:
        Cohen's d value (positive if group2 > group1)
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Handle edge case where variance is 0
    if var1 == 0 and var2 == 0:
        return 0.0
        
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    mean_diff = np.mean(group2) - np.mean(group1)
    return float(mean_diff / pooled_std)


def perform_statistical_tests(
    benign_scores: np.ndarray,
    attack_scores: np.ndarray
) -> Dict[str, Any]:
    """
    Perform statistical validation tests for US-01 Independent Test.
    
    Calculates:
    - Mann-Whitney U test p-value (non-parametric test for distribution difference)
    - Cohen's d effect size
    
    Args:
        benign_scores: Array of drift scores for benign logs
        attack_scores: Array of drift scores for attack logs
        
    Returns:
        Dictionary containing statistical test results
    """
    # Mann-Whitney U test (non-parametric, robust to non-normal distributions)
    u_statistic, p_value = stats.mannwhitneyu(
        benign_scores, 
        attack_scores, 
        alternative='less'  # Expecting attack scores > benign scores
    )
    
    # Cohen's d effect size
    cohen_d = calculate_cohen_d(benign_scores, attack_scores)
    
    # T-test for additional validation (parametric, assumes normality)
    t_statistic, t_p_value = stats.ttest_ind(
        benign_scores, 
        attack_scores, 
        equal_var=False  # Welch's t-test
    )
    
    return {
        "mann_whitney": {
            "statistic": float(u_statistic),
            "p_value": float(p_value),
            "alternative": "less",
            "significant_at_0.05": p_value < 0.05
        },
        "cohens_d": {
            "value": cohen_d,
            "magnitude": "large" if abs(cohen_d) >= 0.8 else 
                         "medium" if abs(cohen_d) >= 0.5 else 
                         "small",
            "threshold_met": abs(cohen_d) >= 0.5
        },
        "t_test": {
            "statistic": float(t_statistic),
            "p_value": float(t_p_value),
            "significant_at_0.05": t_p_value < 0.05
        },
        "sample_sizes": {
            "benign": int(len(benign_scores)),
            "attack": int(len(attack_scores))
        },
        "summary": {
            "p_value_lt_0.05": p_value < 0.05,
            "cohens_d_ge_0.5": abs(cohen_d) >= 0.5,
            "us01_validation_passed": (p_value < 0.05) and (abs(cohen_d) >= 0.5)
        }
    }


def load_test_static_logs(filepath: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load static test logs and separate them by label.
    
    Args:
        filepath: Path to test_static_logs.json
        
    Returns:
        Tuple of (benign_scores, attack_scores) as numpy arrays
    """
    data = load_json_file(filepath)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of logs in {filepath}, got {type(data)}")
    
    benign_scores = []
    attack_scores = []
    
    for item in data:
        if not isinstance(item, dict):
            continue
            
        score = item.get("drift_score")
        label = item.get("label", "").lower()
        
        if score is None:
            continue
            
        score = float(score)
        
        # Assume 'benign' or 'safe' labels are benign, others are attacks
        if label in ["benign", "safe", "normal", "0"]:
            benign_scores.append(score)
        else:
            attack_scores.append(score)
    
    if len(benign_scores) == 0:
        raise ValueError("No benign logs found in test fixture")
    if len(attack_scores) == 0:
        raise ValueError("No attack logs found in test fixture")
        
    return np.array(benign_scores), np.array(attack_scores)


def main():
    """
    Main entry point for statistical validation.
    
    Reads static test fixtures, performs statistical tests,
    and outputs results to data/processed/us01_stats.json
    """
    # Ensure directories exist
    ensure_directories()
    
    # Define paths
    input_path = get_path("data/test_static_logs.json")
    output_path = get_path("data/processed/us01_stats.json")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please run T005c to generate the test fixture first."
        )
    
    print(f"Loading test fixtures from {input_path}...")
    benign_scores, attack_scores = load_test_static_logs(input_path)
    
    print(f"Loaded {len(benign_scores)} benign logs and {len(attack_scores)} attack logs")
    print(f"Benign scores: mean={np.mean(benign_scores):.3f}, std={np.std(benign_scores):.3f}")
    print(f"Attack scores: mean={np.mean(attack_scores):.3f}, std={np.std(attack_scores):.3f}")
    
    print("Performing statistical tests...")
    results = perform_statistical_tests(benign_scores, attack_scores)
    
    # Save results
    save_json_file(results, output_path)
    
    print(f"Results saved to {output_path}")
    print(f"US-01 Validation Passed: {results['summary']['us01_validation_passed']}")
    print(f"  - p-value < 0.05: {results['summary']['p_value_lt_0.05']} (p={results['mann_whitney']['p_value']:.4f})")
    print(f"  - Cohen's d >= 0.5: {results['summary']['cohens_d_ge_0.5']} (d={results['cohens_d']['value']:.3f})")
    
    return results


if __name__ == "__main__":
    main()