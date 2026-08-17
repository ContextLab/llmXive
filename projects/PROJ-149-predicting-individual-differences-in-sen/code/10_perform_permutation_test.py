"""
Permutation Test (Part 2): Calculate Significance.
Compares observed R² against the null distribution generated in T022a.
Appends results to data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import project utilities
from config import get_path, ensure_dirs, get_seed

# Constants
PERMUTATION_FILE = "data/interim/permutation_null_distribution.npy"
MODEL_RESULTS_FILE = "data/processed/model_results.json"
OUTPUT_FILE = "data/processed/model_results.json"

def load_observed_results() -> Dict[str, Any]:
    """Load the model results containing the observed R²."""
    results_path = get_path(MODEL_RESULTS_FILE)
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Model results file not found at {results_path}. "
                                "Run T017/T018/T019 first.")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_null_distribution() -> np.ndarray:
    """Load the null distribution generated in T022a."""
    null_path = get_path(PERMUTATION_FILE)
    if not os.path.exists(null_path):
        raise FileNotFoundError(f"Null distribution file not found at {null_path}. "
                                "Run T022a first.")
    
    return np.load(null_path)

def calculate_permutation_pvalue(observed_r2: float, null_dist: np.ndarray) -> float:
    """
    Calculate the two-tailed p-value by comparing observed R² to the null distribution.
    
    Args:
        observed_r2: The observed R² value from the real model.
        null_dist: The array of R² values from permuted data.
    
    Returns:
        The calculated p-value.
    """
    # Count how many permuted R² values are as extreme or more extreme than observed
    # For R², we typically look at the absolute difference from 0 (or mean of null)
    # However, standard permutation for R² usually tests if observed > null (one-tailed)
    # or if |observed| > |null| (two-tailed). Given R² is non-negative, we check
    # if observed is in the tail of the distribution.
    
    # One-tailed test: P(R²_null >= R²_observed)
    count_extreme = np.sum(null_dist >= observed_r2)
    p_value = count_extreme / len(null_dist)
    
    return p_value

def save_results(p_value: float, observed_r2: float, null_dist: np.ndarray) -> None:
    """Append permutation results to the model results JSON."""
    results_path = get_path(MODEL_RESULTS_FILE)
    
    # Load existing results
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # Prepare permutation results
    permutation_results = {
        "permutation_test": {
            "n_permutations": len(null_dist),
            "observed_r2": float(observed_r2),
            "p_value": float(p_value),
            "null_distribution_stats": {
                "mean": float(np.mean(null_dist)),
                "std": float(np.std(null_dist)),
                "min": float(np.min(null_dist)),
                "max": float(np.max(null_dist)),
                "median": float(np.median(null_dist))
            },
            "significant": p_value < 0.05
        }
    }
    
    # Update results
    results.update(permutation_results)
    
    # Ensure directory exists
    ensure_dirs(os.path.dirname(results_path))
    
    # Save updated results
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Permutation test results saved to {results_path}")
    print(f"Observed R²: {observed_r2:.4f}")
    print(f"P-value: {p_value:.4f}")
    print(f"Significant (p < 0.05): {p_value < 0.05}")

def main():
    parser = argparse.ArgumentParser(description="Permutation Test Part 2: Calculate Significance")
    parser.add_argument('--input-null', type=str, default=PERMUTATION_FILE,
                        help='Path to null distribution file')
    parser.add_argument('--input-results', type=str, default=MODEL_RESULTS_FILE,
                        help='Path to model results file')
    args = parser.parse_args()

    try:
        # Set seed for reproducibility (though not needed for this step)
        get_seed()

        print("Loading observed model results...")
        results = load_observed_results()
        
        # Extract observed R² (handle potential nested structure)
        if "model_results" in results:
            observed_r2 = results["model_results"].get("adjusted_r2") or results["model_results"].get("r2")
        else:
            observed_r2 = results.get("adjusted_r2") or results.get("r2")
        
        if observed_r2 is None:
            raise ValueError("Could not find R² value in model results.")

        print(f"Observed R²: {observed_r2:.4f}")

        print("Loading null distribution...")
        null_dist = load_null_distribution()
        print(f"Null distribution size: {len(null_dist)}")

        print("Calculating p-value...")
        p_value = calculate_permutation_pvalue(observed_r2, null_dist)

        print("Saving results...")
        save_results(p_value, observed_r2, null_dist)

        print("Permutation test complete.")

    except Exception as e:
        print(f"Error during permutation test: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()