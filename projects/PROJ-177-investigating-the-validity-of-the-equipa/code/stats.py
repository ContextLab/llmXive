"""
Statistical analysis module for granular system energy distributions.

Implements hypothesis testing (KS, Chi-squared), binning, and handling
of non-stationary segments (chirped signals).
"""
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from scipy import stats
from scipy.stats import chi2, kstest
import warnings

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def bin_energy_data(df: pd.DataFrame, bin_columns: List[str]) -> pd.DataFrame:
    """
    Bin energy data by driving frequency and material type.
    
    Args:
        df: DataFrame with energy columns and metadata
        bin_columns: List of columns to use for binning (e.g., ['frequency', 'material'])
        
    Returns:
        DataFrame with bin assignments
    """
    if not all(col in df.columns for col in bin_columns):
        missing = [col for col in bin_columns if col not in df.columns]
        raise StatsError(f"Missing required columns for binning: {missing}")
    
    # Create a unique bin identifier
    df = df.copy()
    df['bin_id'] = df[bin_columns].astype(str).agg('-'.join, axis=1)
    return df

def calculate_maxwell_boltzmann_pdf(energies: np.ndarray, kT: float) -> np.ndarray:
    """
    Calculate the Maxwell-Boltzmann probability density function.
    
    For a 3D system, the energy distribution follows:
    P(E) = (2/sqrt(pi)) * (1/(kT)^(3/2)) * sqrt(E) * exp(-E/kT)
    
    Args:
        energies: Array of energy values
        kT: Thermal energy scale parameter
        
    Returns:
        PDF values for the given energies
    """
    if kT <= 0:
        raise StatsError("kT must be positive")
    
    # Avoid division by zero and negative energies
    energies = np.maximum(energies, 1e-10)
    
    prefactor = 2.0 / np.sqrt(np.pi)
    scale_factor = 1.0 / (kT ** 1.5)
    pdf = prefactor * scale_factor * np.sqrt(energies) * np.exp(-energies / kT)
    return pdf

def perform_ks_test(energies: np.ndarray, kT: float) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov test against Maxwell-Boltzmann distribution.
    
    Args:
        energies: Array of observed energy values
        kT: Thermal energy scale parameter for the theoretical distribution
        
    Returns:
        Tuple of (KS statistic, p-value)
    """
    if len(energies) == 0:
        raise StatsError("Cannot perform KS test on empty data")
    
    # Define the theoretical CDF for MB distribution
    def mb_cdf(x):
        # CDF for Maxwell-Boltzmann: erf(sqrt(x/kT)) - (2/sqrt(pi)) * sqrt(x/kT) * exp(-x/kT)
        x = np.array(x)
        if np.any(x < 0):
            raise StatsError("Energy values must be non-negative")
        sqrt_xt = np.sqrt(x / kT)
        from scipy.special import erf
        return erf(sqrt_xt) - (2.0 / np.sqrt(np.pi)) * sqrt_xt * np.exp(-x / kT)
    
    # Perform KS test
    statistic, pvalue = kstest(energies, mb_cdf)
    return statistic, pvalue

def perform_chisquared_test(energies: np.ndarray, kT: float, n_bins: int = 20) -> Tuple[float, float, List[int], List[float]]:
    """
    Perform Chi-squared goodness-of-fit test against Maxwell-Boltzmann distribution.
    
    Args:
        energies: Array of observed energy values
        kT: Thermal energy scale parameter
        n_bins: Number of bins for histogram (default 20)
        
    Returns:
        Tuple of (Chi-squared statistic, p-value, observed counts, expected counts)
    """
    if len(energies) == 0:
        raise StatsError("Cannot perform Chi-squared test on empty data")
    
    # Create bins using quantiles to ensure sufficient counts per bin
    # or use standard rules if data allows
    try:
        bin_edges = np.histogram_bin_edges(energies, bins=n_bins)
    except ValueError:
        # Fallback to equal width if standard binning fails
        bin_edges = np.linspace(energies.min(), energies.max(), n_bins + 1)
    
    # Ensure last bin covers max value
    bin_edges[-1] = bin_edges[-1] + 1e-10
    
    # Calculate observed counts
    observed_counts, _ = np.histogram(energies, bins=bin_edges)
    
    # Calculate expected counts by integrating PDF over bins
    expected_counts = []
    for i in range(len(bin_edges) - 1):
        left, right = bin_edges[i], bin_edges[i+1]
        # Integrate PDF from left to right
        # For MB: integral of sqrt(E)*exp(-E/kT) dE
        # Use numerical integration for accuracy
        from scipy.integrate import quad
        integral, _ = quad(lambda x: calculate_maxwell_boltzmann_pdf(np.array([x]), kT)[0], left, right)
        expected_counts.append(integral * len(energies))
    
    expected_counts = np.array(expected_counts)
    
    # Avoid division by zero
    mask = expected_counts > 0
    if not np.all(mask):
        warnings.warn(f"Some expected counts are zero. {np.sum(~mask)} bins excluded.")
    
    # Calculate Chi-squared statistic
    chi2_stat = np.sum((observed_counts[mask] - expected_counts[mask])**2 / expected_counts[mask])
    
    # Degrees of freedom: number of bins - 1 - number of estimated parameters
    # Here kT is given, so df = n_bins - 1
    df = np.sum(mask) - 1
    if df <= 0:
        raise StatsError("Insufficient bins for Chi-squared test")
    
    pvalue = 1 - chi2.cdf(chi2_stat, df)
    
    return chi2_stat, pvalue, observed_counts.tolist(), expected_counts.tolist()

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction.
    
    Args:
        p_values: List of p-values from multiple tests
        
    Returns:
        List of adjusted p-values
    """
    if len(p_values) == 0:
        return []
    
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        adjusted_p[sorted_indices[i]] = sorted_p[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n-2, -1, -1):
        adjusted_p[sorted_indices[i]] = min(adjusted_p[sorted_indices[i]], adjusted_p[sorted_indices[i+1]])
    
    # Clip to [0, 1]
    adjusted_p = np.clip(adjusted_p, 0, 1)
    
    return adjusted_p.tolist()

def detect_non_stationary_segments(df: pd.DataFrame, time_col: str = 'timestamp', 
                                   signal_col: str = 'driving_frequency', 
                                   threshold: float = 0.05) -> pd.DataFrame:
    """
    Detect non-stationary segments (chirped signals) in the data.
    
    A segment is considered non-stationary if the rate of change in driving frequency
    exceeds a threshold relative to the mean frequency.
    
    Args:
        df: DataFrame with timestamp and signal columns
        time_col: Name of the timestamp column
        signal_col: Name of the driving frequency column
        threshold: Threshold for detecting significant changes (default 0.05)
        
    Returns:
        DataFrame with a 'is_stationary' boolean column
    """
    if time_col not in df.columns or signal_col not in df.columns:
        raise StatsError(f"Required columns '{time_col}' and/or '{signal_col}' not found in DataFrame")
    
    df = df.copy()
    
    # Sort by timestamp
    df = df.sort_values(time_col).reset_index(drop=True)
    
    # Calculate the rate of change in frequency
    freq_diff = df[signal_col].diff()
    time_diff = df[time_col].diff()
    
    # Avoid division by zero
    time_diff = time_diff.replace(0, np.nan)
    rate_of_change = freq_diff / time_diff
    
    # Calculate the mean frequency and its standard deviation
    mean_freq = df[signal_col].mean()
    if mean_freq == 0:
        mean_freq = 1e-10
    
    # Normalize rate of change by mean frequency
    normalized_rate = rate_of_change / mean_freq
    
    # Identify non-stationary segments
    # A segment is non-stationary if the normalized rate exceeds the threshold
    df['is_stationary'] = np.abs(normalized_rate) <= threshold
    
    # Fill NaN values (first row) as stationary if the rate is not extreme
    df['is_stationary'] = df['is_stationary'].fillna(True)
    
    return df

def handle_non_stationary_segments(df: pd.DataFrame, strategy: str = 'exclude', 
                                   time_col: str = 'timestamp',
                                   signal_col: str = 'driving_frequency') -> pd.DataFrame:
    """
    Handle non-stationary segments (chirped signals) by binning or exclusion.
    
    Args:
        df: Input DataFrame with energy and signal data
        strategy: Strategy to handle non-stationary segments ('exclude' or 'bin')
        time_col: Name of the timestamp column
        signal_col: Name of the driving frequency column
        
    Returns:
        Processed DataFrame with non-stationary segments handled
    """
    if strategy not in ['exclude', 'bin']:
        raise StatsError(f"Invalid strategy '{strategy}'. Must be 'exclude' or 'bin'.")
    
    # Detect non-stationary segments
    df_processed = detect_non_stationary_segments(df, time_col, signal_col)
    
    if strategy == 'exclude':
        # Exclude non-stationary segments
        df_final = df_processed[df_processed['is_stationary']].copy()
        excluded_count = len(df_processed) - len(df_final)
        if excluded_count > 0:
            warnings.warn(f"Excluded {excluded_count} rows ({excluded_count/len(df_processed)*100:.2f}%) due to non-stationary segments (chirped signals).")
    else:  # strategy == 'bin'
        # Bin non-stationary segments separately
        # Create a separate bin for non-stationary data
        df_final = df_processed.copy()
        df_final['bin_id'] = df_final.apply(
            lambda row: f"non_stationary" if not row['is_stationary'] else row.get('bin_id', 'unknown'),
            axis=1
        )
        warnings.warn(f"Non-stationary segments ({len(df_final[~df_final['is_stationary']])} rows) binned separately.")
    
    return df_final

def run_statistical_analysis(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.
    
    Args:
        df: DataFrame with energy data and metadata
        config: Configuration dictionary with parameters
        
    Returns:
        Dictionary containing all statistical results
    """
    results = {
        'bins': [],
        'tests': [],
        'summary': {}
    }
    
    # Handle non-stationary segments
    strategy = config.get('non_stationary_strategy', 'exclude')
    df_processed = handle_non_stationary_segments(
        df, 
        strategy=strategy,
        time_col=config.get('time_col', 'timestamp'),
        signal_col=config.get('signal_col', 'driving_frequency')
    )
    
    # Bin the data
    bin_columns = config.get('bin_columns', ['frequency', 'material'])
    df_binned = bin_energy_data(df_processed, bin_columns)
    
    # Group by bins and perform tests
    p_values = []
    test_results = []
    
    for bin_id, group in df_binned.groupby('bin_id'):
        # Calculate kT from the mean energy (equipartition: E = kT for 1D, 3/2 kT for 3D)
        # Assuming 3D system: kT = 2/3 * mean(E_trans)
        mean_energy = group['E_trans'].mean()
        kT = (2.0/3.0) * mean_energy if mean_energy > 0 else 1.0
        
        # Perform KS test
        try:
            ks_stat, ks_p = perform_ks_test(group['E_trans'].values, kT)
        except Exception as e:
            ks_stat, ks_p = None, None
        
        # Perform Chi-squared test
        try:
            chi2_stat, chi2_p, obs_counts, exp_counts = perform_chisquared_test(
                group['E_trans'].values, kT, n_bins=config.get('n_bins', 20)
            )
        except Exception as e:
            chi2_stat, chi2_p, obs_counts, exp_counts = None, None, [], []
        
        # Store results
        test_result = {
            'bin_id': bin_id,
            'n_samples': len(group),
            'mean_energy': float(mean_energy),
            'estimated_kT': float(kT),
            'ks_test': {
                'statistic': float(ks_stat) if ks_stat is not None else None,
                'p_value': float(ks_p) if ks_p is not None else None
            },
            'chisquared_test': {
                'statistic': float(chi2_stat) if chi2_stat is not None else None,
                'p_value': float(chi2_p) if chi2_p is not None else None,
                'observed_counts': obs_counts,
                'expected_counts': exp_counts
            },
            'non_stationary_excluded': not group['is_stationary'].all()
        }
        
        test_results.append(test_result)
        
        if ks_p is not None:
            p_values.append(ks_p)
        if chi2_p is not None:
            p_values.append(chi2_p)
    
    # Apply FDR correction
    if p_values:
        adjusted_p_values = apply_benjamini_hochberg(p_values)
        # Map adjusted p-values back to tests (simplified: assume 2 tests per bin)
        # This is a rough mapping; in practice, you'd track which p-value belongs to which test
        idx = 0
        for i, result in enumerate(test_results):
            if result['ks_test']['p_value'] is not None:
                result['ks_test']['adjusted_p_value'] = float(adjusted_p_values[idx])
                idx += 1
            if result['chisquared_test']['p_value'] is not None:
                result['chisquared_test']['adjusted_p_value'] = float(adjusted_p_values[idx])
                idx += 1
    
    results['tests'] = test_results
    
    # Summary
    total_bins = len(test_results)
    significant_bins = sum(1 for t in test_results 
                          if (t['ks_test']['p_value'] is not None and t['ks_test']['p_value'] < 0.05) or
                             (t['chisquared_test']['p_value'] is not None and t['chisquared_test']['p_value'] < 0.05))
    
    results['summary'] = {
        'total_bins': total_bins,
        'significant_bins': significant_bins,
        'rejection_rate': significant_bins / total_bins if total_bins > 0 else 0.0,
        'non_stationary_handling': strategy
    }
    
    return results

def main():
    """Main entry point for statistical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical analysis on granular energy data')
    parser.add_argument('--input', type=str, required=True, help='Path to energy_samples.csv')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    # Load config
    import yaml
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load data
    df = pd.read_csv(args.input)
    
    # Run analysis
    results = run_statistical_analysis(df, config)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Statistical analysis complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()