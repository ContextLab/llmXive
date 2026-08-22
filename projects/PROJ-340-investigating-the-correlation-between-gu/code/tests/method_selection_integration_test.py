"""
Integration Test: Method Selection Logic (T112)

This script runs the pipeline on three distinct datasets (normal, zero-inflated, non-normal)
and verifies that `data/metadata/method_selection_log.json` correctly identifies the method
used for each.

It generates synthetic data ONLY for the purpose of testing the selection logic (as per T112
requirements for "distinct datasets" to trigger different branches), then runs the analysis
pipeline to measure the actual method selection.

The data generation here is strictly controlled to trigger specific distribution checks
(Normal, Zero-Inflated, Heavy-Tailed) to validate the `select_correlation_method` logic.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import argparse
from pathlib import Path
from scipy import stats

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import select_correlation_method, check_distribution, save_method_selection_log, set_analysis_seed
from config import load_config

def generate_normal_data(n_samples=100, n_features=5):
    """
    Generates data that should pass normality checks (Shapiro-Wilk p > 0.05).
    Expected method: Pearson.
    """
    set_analysis_seed(42)
    data = {}
    for i in range(n_features):
        # Normal distribution
        data[f'var_{i}'] = np.random.normal(loc=0, scale=1, size=n_samples)
    df = pd.DataFrame(data)
    return df, "normal"

def generate_zero_inflated_data(n_samples=100, n_features=5, zero_ratio=0.4):
    """
    Generates data with a high proportion of zeros.
    Expected method: Spearman or ZINB (depending on implementation logic in analysis.py).
    Based on T119, >30% zeros triggers ZINB/Hurdle or non-parametric fallback.
    """
    set_analysis_seed(42)
    data = {}
    for i in range(n_features):
        values = np.random.normal(loc=0, scale=1, size=n_samples)
        # Inject zeros
        num_zeros = int(n_samples * zero_ratio)
        zero_indices = np.random.choice(n_samples, num_zeros, replace=False)
        values[zero_indices] = 0
        data[f'var_{i}'] = values
    df = pd.DataFrame(data)
    return df, "zero_inflated"

def generate_heavy_tailed_data(n_samples=100, n_features=5):
    """
    Generates data with heavy tails (e.g., Cauchy or LogNormal) that fails normality.
    Expected method: Spearman (non-parametric).
    """
    set_analysis_seed(42)
    data = {}
    for i in range(n_features):
        # Log-normal creates heavy right tail
        data[f'var_{i}'] = np.random.lognormal(mean=0, sigma=1.5, size=n_samples)
    df = pd.DataFrame(data)
    return df, "heavy_tailed"

def run_test_case(df, case_name, output_dir):
    """
    Runs the distribution check and method selection for a given dataframe.
    Writes the result to the metadata log.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Check distribution (This populates internal state or returns flags)
    # The function check_distribution in analysis.py is expected to return a dict of stats
    dist_stats = check_distribution(df)

    # 2. Select method based on stats
    # We simulate the logic by calling the function that would be used in the pipeline
    # Note: In a real pipeline, this might be called inside run_correlation_analysis
    # Here we call it directly to verify the selection logic
    selected_method = select_correlation_method(df, dist_stats)

    # 3. Log the result
    log_entry = {
        "dataset": case_name,
        "sample_size": len(df),
        "feature_count": len(df.columns),
        "distribution_stats_summary": {
            "shapiro_p_min": min(dist_stats.get('shapiro_p_values', [1.0])),
            "zero_ratio_max": max(dist_stats.get('zero_ratios', [0.0])),
            "kurtosis_max": max(dist_stats.get('kurtosis_values', [0.0]))
        },
        "selected_method": selected_method,
        "reason": f"Triggered by distribution properties: Shapiro p={dist_stats.get('shapiro_p_values', [])[:3]}, Zeros={dist_stats.get('zero_ratios', [])[:3]}"
    }

    # Save to the specific file required by T112
    log_file = os.path.join(output_dir, "method_selection_log.json")

    # Load existing log if it exists (append mode for multiple test cases)
    existing_log = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                existing_log = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_log = []

    existing_log.append(log_entry)

    with open(log_file, 'w') as f:
        json.dump(existing_log, f, indent=2)

    print(f"[{case_name}] Selected Method: {selected_method}")
    return selected_method

def main():
    parser = argparse.ArgumentParser(description="Integration Test for Method Selection Logic (T112)")
    parser.add_argument('--output-dir', type=str, default='data/metadata', help='Directory to write logs')
    args = parser.parse_args()

    output_dir = args.output_dir
    results = {}

    print("Starting Method Selection Integration Test (T112)...")

    # Test Case 1: Normal Data
    print("\n1. Generating Normal Data...")
    df_normal, name_normal = generate_normal_data()
    results[name_normal] = run_test_case(df_normal, name_normal, output_dir)

    # Test Case 2: Zero-Inflated Data
    print("\n2. Generating Zero-Inflated Data...")
    df_zero, name_zero = generate_zero_inflated_data()
    results[name_zero] = run_test_case(df_zero, name_zero, output_dir)

    # Test Case 3: Heavy-Tailed (Non-Normal) Data
    print("\n3. Generating Heavy-Tailed Data...")
    df_heavy, name_heavy = generate_heavy_tailed_data()
    results[name_heavy] = run_test_case(df_heavy, name_heavy, output_dir)

    # Verification
    print("\n--- Verification Summary ---")
    # We expect specific methods for specific data types based on standard statistical logic
    # implemented in analysis.py (T021/T119)
    # Normal -> Pearson
    # Zero-Inflated -> ZINB or Spearman (depending on specific thresholds in code)
    # Heavy-Tailed -> Spearman

    expected_map = {
        "normal": ["pearson"],
        "zero_inflated": ["zinb", "spearman"], # T119 logic: >30% zeros -> ZINB or fallback
        "heavy_tailed": ["spearman"]
    }

    all_passed = True
    for case, selected in results.items():
        expected = expected_map.get(case, [])
        if selected in expected:
            print(f"PASS: {case} -> {selected} (Expected one of: {expected})")
        else:
            print(f"FAIL: {case} -> {selected} (Expected one of: {expected})")
            all_passed = False

    # Final status
    if all_passed:
        print("\n[T112] INTEGRATION TEST PASSED: Method selection logic correctly identified methods for all datasets.")
        print(f"Log written to: {os.path.join(output_dir, 'method_selection_log.json')}")
    else:
        print("\n[T112] INTEGRATION TEST FAILED: Method selection did not match expected logic.")
        sys.exit(1)

if __name__ == "__main__":
    main()
