"""
Multiple comparison correction module for statistical analysis.

Implements Bonferroni and Holm-Bonferroni corrections for paired dataset comparisons.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats


def apply_bonferroni_correction(p_values: List[float], num_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values from statistical tests.
        num_tests: Total number of hypothesis tests performed.
    
    Returns:
        List of corrected p-values. Values exceeding 1.0 are capped at 1.0.
    """
    if not p_values:
        return []
    
    corrected = [min(p * num_tests, 1.0) for p in p_values]
    return corrected


def apply_holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction (step-down procedure) to a list of p-values.
    
    This method is more powerful than standard Bonferroni while controlling
    the family-wise error rate.
    
    Args:
        p_values: List of raw p-values from statistical tests.
    
    Returns:
        List of corrected p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    # Sort p-values with their original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Compute Holm-adjusted p-values
    # For the i-th smallest p-value (0-indexed), multiply by (n - i)
    # Then take the cumulative maximum to ensure monotonicity
    adjusted = sorted_p * (n - np.arange(n))
    adjusted = np.minimum(adjusted, 1.0)
    
    # Ensure monotonicity: each adjusted p-value should be >= the previous one
    for i in range(1, n):
        adjusted[i] = max(adjusted[i], adjusted[i-1])
    
    # Map back to original order
    corrected = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        corrected[idx] = float(adjusted[i])
    
    return corrected


def load_p_values_from_analysis(analysis_file: str) -> Dict[str, float]:
    """
    Load p-values from the statistical analysis results file.
    
    Args:
        analysis_file: Path to the JSON file containing analysis results.
    
    Returns:
        Dictionary mapping dataset names to their p-values.
    """
    path = Path(analysis_file)
    if not path.exists():
        raise FileNotFoundError(f"Analysis file not found: {analysis_file}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    p_values = {}
    for dataset_name, results in data.items():
        if isinstance(results, dict) and 'p_value' in results:
            p_values[dataset_name] = results['p_value']
        elif isinstance(results, (int, float)):
            p_values[dataset_name] = float(results)
    
    return p_values


def run_multiple_comparison_correction(
    p_values: Dict[str, float],
    correction_method: str = "holm-bonferroni"
) -> Dict[str, Dict[str, Any]]:
    """
    Run multiple comparison correction on a set of p-values.
    
    Args:
        p_values: Dictionary mapping dataset names to their p-values.
        correction_method: Either "bonferroni" or "holm-bonferroni".
    
    Returns:
        Dictionary with corrected results for each dataset.
    """
    if not p_values:
        return {}
    
    datasets = list(p_values.keys())
    raw_p = [p_values[ds] for ds in datasets]
    num_tests = len(datasets)
    
    if correction_method == "bonferroni":
        corrected_p = apply_bonferroni_correction(raw_p, num_tests)
    elif correction_method == "holm-bonferroni":
        corrected_p = apply_holm_bonferroni_correction(raw_p)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    results = {}
    for i, dataset in enumerate(datasets):
        results[dataset] = {
            "raw_p_value": raw_p[i],
            "corrected_p_value": corrected_p[i],
            "method": correction_method,
            "significant_at_0.05": corrected_p[i] < 0.05,
            "significant_at_0.01": corrected_p[i] < 0.01
        }
    
    return results


def main():
    """
    Main entry point for multiple comparison correction.
    
    Reads statistical analysis results, applies correction, and writes
    the corrected results to the statistical summary file.
    """
    project_root = Path(__file__).resolve().parents[2]
    analysis_file = project_root / "artifacts" / "results" / "statistical_analysis.json"
    output_file = project_root / "artifacts" / "results" / "statistical_summary.json"
    
    # Load existing analysis results
    try:
        p_values = load_p_values_from_analysis(str(analysis_file))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run the statistical analysis (T019) first to generate the input file.")
        return
    
    if not p_values:
        print("Warning: No p-values found in the analysis file.")
        return
    
    print(f"Found p-values for {len(p_values)} datasets: {list(p_values.keys())}")
    
    # Apply Holm-Bonferroni correction (preferred over standard Bonferroni)
    corrected_results = run_multiple_comparison_correction(
        p_values, 
        correction_method="holm-bonferroni"
    )
    
    # Write results to output file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(corrected_results, f, indent=2)
    
    print(f"Multiple comparison correction complete.")
    print(f"Results written to: {output_file}")
    
    # Print summary
    print("\nCorrection Summary (Holm-Bonferroni):")
    print("-" * 60)
    for dataset, res in corrected_results.items():
        sig_marker = "*" if res['significant_at_0.05'] else " "
        print(f"{dataset:15} | Raw: {res['raw_p_value']:.4f} | "
              f"Corrected: {res['corrected_p_value']:.4f} | {sig_marker} Sig")
    print("-" * 60)


if __name__ == "__main__":
    main()