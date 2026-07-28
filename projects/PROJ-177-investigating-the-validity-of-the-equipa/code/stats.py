import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from scipy import stats
from scipy.special import gamma

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def bin_energy_data(df: pd.DataFrame, bin_columns: List[str] = ['frequency_bin', 'material_type']) -> Dict[str, pd.DataFrame]:
    """
    Bin energy data by driving frequency and material type.

    Args:
        df: DataFrame containing energy data with columns for frequency, material, and energies.
        bin_columns: List of columns to group by.

    Returns:
        Dictionary mapping bin keys to DataFrames.
    """
    if not all(col in df.columns for col in bin_columns):
        raise StatsError(f"Missing required columns for binning: {bin_columns}")

    groups = df.groupby(bin_columns)
    bins = {}
    for name, group in groups:
        # Handle tuple names from multi-level groupby
        if isinstance(name, tuple):
            key = "_".join(str(x) for x in name)
        else:
            key = str(name)
        bins[key] = group.copy()
    return bins

def calculate_maxwell_boltzmann_pdf(x: np.ndarray, kT: float) -> np.ndarray:
    """
    Calculate the Maxwell-Boltzmann probability density function for energy.
    For 3D translational motion, f(E) ~ sqrt(E) * exp(-E/kT).
    For rotational/vibrational, the degrees of freedom change, but we assume
    the standard form for equipartition testing (3 degrees of freedom).

    Args:
        x: Array of energy values.
        kT: Thermal energy scale (Boltzmann constant * Temperature).

    Returns:
        Array of PDF values.
    """
    if kT <= 0:
        raise StatsError("kT must be positive")
    
    # Avoid division by zero or log of zero
    x = np.array(x, dtype=float)
    x = np.maximum(x, 1e-10)
    
    # Normalization constant for 3D: (2/sqrt(pi)) * (1/kT)^(3/2) * sqrt(E)
    # PDF(E) = (2 / (sqrt(pi) * (kT)^(3/2))) * sqrt(E) * exp(-E / kT)
    const = 2.0 / (np.sqrt(np.pi) * (kT ** 1.5))
    pdf = const * np.sqrt(x) * np.exp(-x / kT)
    return pdf

def perform_ks_test(energy_data: pd.DataFrame, kT: float, energy_col: str = 'E_trans') -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test against the theoretical Maxwell-Boltzmann distribution.

    Args:
        energy_data: DataFrame with energy column.
        kT: Thermal energy scale.
        energy_col: Name of the energy column to test.

    Returns:
        Dictionary with statistic, p-value, and rejection flag.
    """
    if energy_col not in energy_data.columns:
        raise StatsError(f"Column {energy_col} not found in data")
    
    data = energy_data[energy_col].dropna().values
    if len(data) == 0:
        raise StatsError("No valid data points for KS test")

    # Define the CDF of the Maxwell-Boltzmann distribution
    # CDF(x) = erf(sqrt(x/kT)) - 2/sqrt(pi) * sqrt(x/kT) * exp(-x/kT)
    def mb_cdf(x, kT_val):
        x = np.array(x, dtype=float)
        x = np.maximum(x, 1e-10)
        sqrt_x_kT = np.sqrt(x / kT_val)
        # Use scipy's erf
        from scipy.special import erf
        cdf_val = erf(sqrt_x_kT) - (2.0 / np.sqrt(np.pi)) * sqrt_x_kT * np.exp(-x / kT_val)
        return np.clip(cdf_val, 0.0, 1.0)

    # Perform KS test
    statistic, pvalue = stats.kstest(data, lambda x: mb_cdf(x, kT))

    return {
        "test": "Kolmogorov-Smirnov",
        "statistic": float(statistic),
        "pvalue": float(pvalue),
        "rejection": pvalue < 0.05  # Default alpha
    }

def perform_chisquared_test(energy_data: pd.DataFrame, kT: float, energy_col: str = 'E_trans', bins: int = 10) -> Dict[str, Any]:
    """
    Perform Chi-squared goodness-of-fit test against Maxwell-Boltzmann.

    Args:
        energy_data: DataFrame with energy column.
        kT: Thermal energy scale.
        energy_col: Name of the energy column to test.
        bins: Number of bins for histogram.

    Returns:
        Dictionary with statistic, p-value, and rejection flag.
    """
    if energy_col not in energy_data.columns:
        raise StatsError(f"Column {energy_col} not found in data")

    data = energy_data[energy_col].dropna().values
    if len(data) == 0:
        raise StatsError("No valid data points for Chi-squared test")

    # Create bins
    min_val, max_val = np.min(data), np.max(data)
    if min_val == max_val:
        max_val = min_val + 1.0
    bin_edges = np.linspace(min_val, max_val, bins + 1)
    
    # Observed counts
    observed, _ = np.histogram(data, bins=bin_edges)
    
    # Expected counts from MB distribution
    # Integrate PDF over each bin
    expected_counts = []
    for i in range(bins):
        low, high = bin_edges[i], bin_edges[i+1]
        # Numerical integration of PDF
        x_fine = np.linspace(low, high, 100)
        pdf_vals = calculate_maxwell_boltzmann_pdf(x_fine, kT)
        # Simple trapezoidal integration
        integral = np.trapz(pdf_vals, x_fine)
        expected_counts.append(integral * len(data))
    
    expected = np.array(expected_counts)
    
    # Avoid division by zero in Chi-squared
    mask = expected > 0
    if not np.all(mask):
        # Merge empty bins if necessary (simplified: just filter)
        if np.sum(expected) == 0:
            raise StatsError("Expected counts are zero; cannot perform Chi-squared test")
        observed = observed[mask]
        expected = expected[mask]

    statistic, pvalue = stats.chisquare(observed, expected)

    return {
        "test": "Chi-squared",
        "statistic": float(statistic),
        "pvalue": float(pvalue),
        "rejection": pvalue < 0.05
    }

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg procedure for False Discovery Rate (FDR) correction.

    Args:
        p_values: List of raw p-values from multiple hypothesis tests.
        alpha: Desired FDR level.

    Returns:
        Tuple of (rejection_flags, adjusted_p_values).
        rejection_flags: Boolean list indicating if the hypothesis is rejected after correction.
        adjusted_p_values: The adjusted p-values.
    """
    if not p_values:
        return [], []

    if any(not isinstance(p, (int, float)) or p < 0 or p > 1 for p in p_values):
        raise StatsError("All p-values must be floats between 0 and 1")

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate adjusted p-values
    # Formula: p_adj(i) = min( (n/i) * p(i), p_adj(i+1) ) for i = n-1 down to 1
    # And p_adj(n) = n * p(n)
    adjusted = np.zeros(n)
    adjusted[-1] = sorted_p[-1] * n
    
    for i in range(n - 2, -1, -1):
        # Rank is i+1 (1-based)
        rank = i + 1
        current_adj = sorted_p[i] * n / rank
        # Ensure monotonicity
        adjusted[i] = min(current_adj, adjusted[i+1])
    
    # Clip to 1.0
    adjusted = np.clip(adjusted, 0.0, 1.0)
    
    # Map back to original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted
    
    # Determine rejections
    rejections = final_adjusted < alpha

    return list(rejections), list(final_adjusted)

def run_statistical_analysis(
    input_path: str,
    output_path: str,
    alpha: float = 0.05,
    energy_types: List[str] = ['E_trans', 'E_rot', 'E_pot', 'E_vib']
) -> Dict[str, Any]:
    """
    Main function to run the full statistical analysis pipeline:
    1. Load data
    2. Bin by frequency/material
    3. Perform KS and Chi-squared tests for each bin
    4. Apply Benjamini-Hochberg correction across all tests
    5. Save results

    Args:
        input_path: Path to energy_samples.csv
        output_path: Path to save statistical_results.json
        alpha: Significance level for FDR correction
        energy_types: List of energy columns to analyze
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise StatsError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_file)
    
    # Estimate kT from the data (assuming equipartition holds roughly for estimation)
    # E = 1/2 kT * f => kT = 2 * mean(E) / f
    # For 3D translation, f=3. We'll estimate kT from E_trans mean.
    if 'E_trans' in df.columns:
        mean_E_trans = df['E_trans'].mean()
        kT_est = 2.0 * mean_E_trans / 3.0
    else:
        # Fallback: use a default or raise error
        kT_est = 1.0 

    bins = bin_energy_data(df)
    
    all_p_values = []
    all_test_results = []
    test_id_counter = 0

    for bin_key, bin_df in bins.items():
        bin_results = {
            "bin_key": bin_key,
            "sample_size": len(bin_df),
            "tests": []
        }
        
        for energy_type in energy_types:
            if energy_type not in bin_df.columns:
                continue
            
            # Perform KS test
            try:
                ks_res = perform_ks_test(bin_df, kT_est, energy_type)
                ks_res['energy_type'] = energy_type
                ks_res['test_id'] = test_id_counter
                all_p_values.append(ks_res['pvalue'])
                bin_results['tests'].append(ks_res)
                test_id_counter += 1
            except Exception as e:
                bin_results['tests'].append({"test": "KS", "error": str(e), "energy_type": energy_type})

            # Perform Chi-squared test
            try:
                chi_res = perform_chisquared_test(bin_df, kT_est, energy_type)
                chi_res['energy_type'] = energy_type
                chi_res['test_id'] = test_id_counter
                all_p_values.append(chi_res['pvalue'])
                bin_results['tests'].append(chi_res)
                test_id_counter += 1
            except Exception as e:
                bin_results['tests'].append({"test": "Chi-squared", "error": str(e), "energy_type": energy_type})
        
        all_test_results.append(bin_results)

    # Apply Benjamini-Hochberg correction
    if all_p_values:
        rejections, adjusted_p = apply_benjamini_hochberg(all_p_values, alpha)
        
        # Map back to results
        test_idx = 0
        for bin_result in all_test_results:
            for test in bin_result['tests']:
                if 'pvalue' in test:
                    test['adjusted_pvalue'] = adjusted_p[test_idx]
                    test['rejected_fdr'] = rejections[test_idx]
                    test_idx += 1
    else:
        for bin_result in all_test_results:
            for test in bin_result['tests']:
                test['adjusted_pvalue'] = None
                test['rejected_fdr'] = None

    final_output = {
        "summary": {
            "total_bins": len(bins),
            "total_tests": len(all_p_values),
            "fdr_alpha": alpha,
            "estimated_kT": kT_est
        },
        "bins": all_test_results
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(final_output, f, indent=2)

    return final_output

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical analysis on granular energy data")
    parser.add_argument("--input", required=True, help="Path to energy_samples.csv")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    parser.add_argument("--alpha", type=float, default=0.05, help="FDR significance level")
    args = parser.parse_args()

    try:
        results = run_statistical_analysis(args.input, args.output, args.alpha)
        print(f"Analysis complete. Results saved to {args.output}")
        print(f"Total tests performed: {results['summary']['total_tests']}")
    except StatsError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()