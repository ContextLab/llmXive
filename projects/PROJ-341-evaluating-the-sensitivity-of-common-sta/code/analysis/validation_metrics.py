"""
Validation Metrics Module (T034)

Calculates and saves validation metrics and Kolmogorov-Smirnov (KS) statistics
to data/simulation/validation_metrics.json.

This module:
1. Loads simulated p-values (from p_values_raw.csv)
2. Loads real data p-values (from real_data_pvalues.csv)
3. Calculates real data power estimates
4. Calculates KS distance between simulated and real distributions
5. Saves comprehensive validation metrics to JSON
"""

import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats
import pandas as pd

# Import from sibling modules using the exact API surface provided
from code.simulation.output_writer import load_p_values_raw_safe
from code.analysis.bootstrapper import load_real_data_pvalues, calculate_ks_distance


def load_simulated_pvalues_for_comparison(
    p_values_path: str = "data/simulation/p_values_raw.csv",
    test_type: Optional[str] = None,
    sample_size: Optional[int] = None
) -> List[float]:
    """
    Load simulated p-values for comparison with real data.

    Args:
        p_values_path: Path to the raw p-values CSV file.
        test_type: Optional filter for specific test type (t-test, anova, chi-squared).
        sample_size: Optional filter for specific sample size.

    Returns:
        List of p-values matching the filters.
    """
    try:
        df = load_p_values_raw_safe(p_values_path)
        if df is None or df.empty:
            return []

        # Filter by test type if specified
        if test_type:
            df = df[df['test_type'].str.lower() == test_type.lower()]

        # Filter by sample size if specified
        if sample_size:
            df = df[df['sample_size'] == sample_size]

        return df['p_value'].dropna().tolist()
    except Exception as e:
        print(f"Warning: Could not load simulated p-values: {e}")
        return []


def calculate_real_data_power(
    real_p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate power estimates from real data p-values.

    Power is estimated as the proportion of tests where p < alpha.
    For real data, this is an empirical estimate of the test's ability
    to detect effects present in the real dataset.

    Args:
        real_p_values: List of p-values from real data tests.
        alpha: Significance level (default 0.05).

    Returns:
        Dictionary with power estimates and related statistics.
    """
    if not real_p_values:
        return {
            "power_estimate": None,
            "total_tests": 0,
            "significant_tests": 0,
            "proportion_significant": None,
            "mean_p_value": None,
            "median_p_value": None
        }

    total_tests = len(real_p_values)
    significant_tests = sum(1 for p in real_p_values if p < alpha)
    proportion_significant = significant_tests / total_tests if total_tests > 0 else 0

    return {
        "power_estimate": proportion_significant,
        "total_tests": total_tests,
        "significant_tests": significant_tests,
        "proportion_significant": proportion_significant,
        "mean_p_value": float(np.mean(real_p_values)),
        "median_p_value": float(np.median(real_p_values))
    }


def calculate_validation_metrics(
    simulated_p_values: List[float],
    real_p_values: List[float],
    alpha: float = 0.05,
    test_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive validation metrics comparing simulated and real data.

    This function computes:
    1. KS distance between simulated and real p-value distributions
    2. Power estimates for both simulated and real data
    3. Type I error rates (when appropriate)
    4. Statistical similarity measures

    Args:
        simulated_p_values: List of p-values from simulation.
        real_p_values: List of p-values from real data.
        alpha: Significance level.
        test_type: Name of the statistical test being validated.

    Returns:
        Dictionary containing all validation metrics.
    """
    metrics = {
        "test_type": test_type,
        "alpha": alpha,
        "sample_sizes": {
            "simulated_count": len(simulated_p_values),
            "real_count": len(real_p_values)
        }
    }

    # Handle empty data cases
    if not simulated_p_values or not real_p_values:
        metrics["status"] = "incomplete"
        metrics["reason"] = "Missing data for comparison"
        metrics["ks_distance"] = None
        metrics["ks_p_value"] = None
        metrics["simulated_power"] = None
        metrics["real_power"] = None
        return metrics

    # Calculate KS distance
    ks_stat, ks_pvalue = stats.ks_2samp(simulated_p_values, real_p_values)

    metrics["ks_distance"] = float(ks_stat)
    metrics["ks_p_value"] = float(ks_pvalue)
    metrics["ks_significant"] = ks_pvalue < alpha

    # Calculate power estimates
    simulated_power = calculate_real_data_power(simulated_p_values, alpha)
    real_power = calculate_real_data_power(real_p_values, alpha)

    metrics["simulated_power"] = simulated_power
    metrics["real_power"] = real_power

    # Calculate additional similarity metrics
    metrics["mean_p_difference"] = abs(
        simulated_power["mean_p_value"] - real_power["mean_p_value"]
    ) if simulated_power["mean_p_value"] is not None and real_power["mean_p_value"] is not None else None

    metrics["power_difference"] = abs(
        simulated_power["power_estimate"] - real_power["power_estimate"]
    ) if simulated_power["power_estimate"] is not None and real_power["power_estimate"] is not None else None

    # Validation status
    # Pass if KS distance <= 0.10 (as per FR-006, SC-003)
    validation_passed = metrics["ks_distance"] is not None and metrics["ks_distance"] <= 0.10
    metrics["validation_passed"] = validation_passed
    metrics["validation_threshold"] = 0.10

    if validation_passed:
        metrics["status"] = "passed"
        metrics["conclusion"] = "Real data p-value distribution is statistically similar to simulated distribution (KS <= 0.10)"
    else:
        metrics["status"] = "failed"
        metrics["conclusion"] = f"Real data p-value distribution differs significantly from simulated (KS = {metrics['ks_distance']:.4f} > 0.10)"

    return metrics


def save_validation_metrics(
    metrics: Dict[str, Any],
    output_path: str = "data/simulation/validation_metrics.json"
) -> bool:
    """
    Save validation metrics to a JSON file.

    Args:
        metrics: Dictionary of metrics to save.
        output_path: Path to the output JSON file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Add metadata
        from datetime import datetime
        metrics["generated_at"] = datetime.utcnow().isoformat()
        metrics["output_file"] = output_path

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, default=str)

        print(f"Validation metrics saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving validation metrics: {e}")
        return False


def main():
    """
    Main entry point for T034: Save validation metrics and KS statistics.

    This function:
    1. Loads simulated p-values from data/simulation/p_values_raw.csv
    2. Loads real data p-values from data/simulation/real_data_pvalues.csv
    3. Calculates validation metrics for each test type
    4. Saves comprehensive results to data/simulation/validation_metrics.json
    """
    print("Starting validation metrics calculation (T034)...")

    # Define file paths
    simulated_pvalues_path = "data/simulation/p_values_raw.csv"
    real_pvalues_path = "data/simulation/real_data_pvalues.csv"
    output_path = "data/simulation/validation_metrics.json"

    # Check if input files exist
    if not os.path.exists(simulated_pvalues_path):
        print(f"Error: Simulated p-values file not found: {simulated_pvalues_path}")
        print("Please run the simulation first to generate p_values_raw.csv")
        return False

    if not os.path.exists(real_pvalues_path):
        print(f"Error: Real data p-values file not found: {real_pvalues_path}")
        print("Please run the validation step first to generate real_data_pvalues.csv")
        return False

    # Load data
    print("Loading simulated p-values...")
    simulated_df = load_p_values_raw_safe(simulated_pvalues_path)
    if simulated_df is None or simulated_df.empty:
        print("Error: No simulated p-values found")
        return False

    print("Loading real data p-values...")
    real_pvalues = load_real_data_pvalues(real_pvalues_path)
    if not real_pvalues:
        print("Error: No real data p-values found")
        return False

    # Group simulated data by test type for detailed comparison
    test_types = simulated_df['test_type'].unique()
    all_metrics = []

    for test_type in test_types:
        print(f"Calculating metrics for {test_type}...")

        # Get simulated p-values for this test type
        sim_pvals = simulated_df[simulated_df['test_type'] == test_type]['p_value'].dropna().tolist()

        # Filter real p-values by test type if the structure allows
        # Assuming real_pvalues is a list of dicts or similar structure with test_type
        if isinstance(real_pvalues, list) and len(real_pvalues) > 0 and isinstance(real_pvalues[0], dict):
            real_pvals_for_test = [
                p['p_value'] for p in real_pvalues
                if p.get('test_type') == test_type and 'p_value' in p
            ]
        else:
            # If real_pvalues is flat, we might need to map them differently
            # For now, use all real p-values if test_type matching isn't possible
            real_pvals_for_test = real_pvalues if real_pvalues else []

        if not sim_pvals or not real_pvals_for_test:
            print(f"  Skipping {test_type}: insufficient data")
            continue

        # Calculate metrics
        metrics = calculate_validation_metrics(
            simulated_p_values=sim_pvals,
            real_p_values=real_pvals_for_test,
            test_type=test_type
        )
        all_metrics.append(metrics)

        # Print summary
        status = "PASS" if metrics.get('validation_passed') else "FAIL"
        ks_dist = metrics.get('ks_distance', 'N/A')
        print(f"  {test_type}: {status} (KS = {ks_dist})")

    # Aggregate results
    final_output = {
        "validation_summary": {
            "total_test_types": len(all_metrics),
            "passed_count": sum(1 for m in all_metrics if m.get('validation_passed')),
            "failed_count": sum(1 for m in all_metrics if not m.get('validation_passed'))
        },
        "detailed_metrics": all_metrics
    }

    # Save results
    success = save_validation_metrics(final_output, output_path)

    if success:
        print(f"Validation metrics successfully saved to {output_path}")
        # Print overall conclusion
        passed = final_output['validation_summary']['passed_count']
        total = final_output['validation_summary']['total_test_types']
        if passed == total:
            print("OVERALL: All test types validated successfully against real data.")
        elif passed > 0:
            print(f"OVERALL: {passed}/{total} test types validated successfully.")
        else:
            print("OVERALL: No test types validated successfully.")
    else:
        print("Failed to save validation metrics.")

    return success


if __name__ == "__main__":
    exit(main())
