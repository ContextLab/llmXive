import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def bin_energy_data(data: pd.DataFrame, bin_column: str = 'frequency_bin') -> pd.DataFrame:
    """
    Bin energy data by driving frequency and material type.
    
    Args:
        data: DataFrame with energy columns and metadata
        bin_column: Column name to use for binning (default: 'frequency_bin')
        
    Returns:
        DataFrame grouped by bins
    """
    if bin_column not in data.columns:
        # Create a default bin if not present
        data = data.copy()
        data[bin_column] = 'default'
    
    return data.groupby([bin_column, 'material_type'])

def calculate_maxwell_boltzmann_pdf(energies: np.ndarray, kT: float) -> np.ndarray:
    """
    Calculate Maxwell-Boltzmann probability density function values.
    
    Args:
        energies: Array of energy values
        kT: Thermal energy scale parameter
        
    Returns:
        Array of PDF values
    """
    if kT <= 0:
        raise StatsError("kT must be positive")
    
    # MB distribution for 3D: f(E) = 2 * sqrt(E / pi) * (1/kT)^(3/2) * exp(-E/kT)
    # Simplified for energy distribution
    pdf = (2.0 / np.sqrt(np.pi)) * (1.0 / kT**1.5) * np.sqrt(energies) * np.exp(-energies / kT)
    return pdf

def perform_ks_test(observed: np.ndarray, theoretical_cdf: callable) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov test against theoretical distribution.
    
    Args:
        observed: Observed energy values
        theoretical_cdf: CDF function of theoretical distribution
        
    Returns:
        Tuple of (statistic, p-value)
    """
    statistic, pvalue = stats.kstest(observed, theoretical_cdf)
    return statistic, pvalue

def perform_chisquared_test(observed_counts: np.ndarray, expected_counts: np.ndarray) -> Tuple[float, float]:
    """
    Perform Chi-squared goodness-of-fit test.
    
    Args:
        observed_counts: Observed bin counts
        expected_counts: Expected bin counts under null hypothesis
        
    Returns:
        Tuple of (statistic, p-value)
    """
    statistic, pvalue = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)
    return statistic, pvalue

def apply_benjamini_hochberg(pvalues: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        pvalues: List of p-values
        alpha: Significance level
        
    Returns:
        List of booleans indicating rejection
    """
    n = len(pvalues)
    if n == 0:
        return []
    
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = np.array(pvalues)[sorted_indices]
    
    # Calculate critical values
    critical_values = (np.arange(1, n + 1) / n) * alpha
    
    # Find largest k where p_k <= critical_value
    reject = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_pvalues[i] <= critical_values[i]:
            reject[:i+1] = True
            break
    
    # Map back to original order
    result = np.zeros(n, dtype=bool)
    result[sorted_indices] = reject
    
    return result.tolist()

def detect_non_stationary_segments(df: pd.DataFrame, time_col: str = 'timestamp', 
                                  signal_col: str = 'driving_amplitude', 
                                  window_size: int = 100) -> pd.Series:
    """
    Detect non-stationary segments (e.g., chirped signals) by analyzing 
    local statistics over sliding windows.
    
    Args:
        df: DataFrame with time series data
        time_col: Column name for timestamps
        signal_col: Column name for the driving signal to analyze
        window_size: Number of samples per window for local statistics
        
    Returns:
        Series indicating which rows belong to non-stationary segments
    """
    if signal_col not in df.columns:
        logger.warning(f"Signal column '{signal_col}' not found. Assuming stationary.")
        return pd.Series([False] * len(df), index=df.index)
    
    signal = df[signal_col].values
    n = len(signal)
    
    if n < window_size:
        logger.warning(f"Data length ({n}) less than window size ({window_size}). Assuming stationary.")
        return pd.Series([False] * n, index=df.index)
    
    # Calculate local statistics in sliding windows
    local_mean = pd.Series(signal).rolling(window=window_size, center=True).mean()
    local_std = pd.Series(signal).rolling(window=window_size, center=True).std()
    
    # Drop NaN from rolling operations
    local_mean = local_mean.dropna()
    local_std = local_std.dropna()
    
    # Detect non-stationarity: significant trend in mean or large variance in std
    # Criterion 1: Slope of local mean > threshold (detecting chirp/ramp)
    if len(local_mean) > 1:
        x = np.arange(len(local_mean))
        slope, _, _, _, _ = stats.linregress(x, local_mean.values)
        mean_trend_threshold = np.std(signal) / window_size
        has_mean_trend = abs(slope) > mean_trend_threshold
    else:
        has_mean_trend = False
    
    # Criterion 2: High variance in local standard deviation
    if len(local_std) > 1:
        std_variance = np.var(local_std.values)
        std_threshold = (np.std(signal) / np.sqrt(window_size)) ** 2
        has_varying_variance = std_variance > std_threshold
    else:
        has_varying_variance = False
    
    # Identify segments: if global test detects non-stationarity, mark all as non-stationary
    # OR use a more granular approach: mark windows that deviate significantly
    is_non_stationary = has_mean_trend or has_varying_variance
    
    if is_non_stationary:
        logger.info("Non-stationary segments detected (chirped signal or varying statistics).")
        # Mark all points as non-stationary for exclusion, or could implement window-based marking
        # For simplicity in this implementation, we flag the entire dataset if non-stationarity is detected
        # A more refined approach would mark specific time windows
        result = pd.Series([True] * len(df), index=df.index)
    else:
        result = pd.Series([False] * len(df), index=df.index)
        
    return result

def handle_non_stationary_segments(df: pd.DataFrame, time_col: str = 'timestamp',
                                  signal_col: str = 'driving_amplitude',
                                  window_size: int = 100,
                                  strategy: str = 'exclude') -> pd.DataFrame:
    """
    Handle non-stationary segments (chirped signals) by either binning or exclusion.
    
    Args:
        df: Input DataFrame with energy and time series data
        time_col: Column name for timestamps
        signal_col: Column name for driving signal
        window_size: Window size for stationarity detection
        strategy: 'exclude' (drop non-stationary segments) or 'bin' (create separate bins)
        
    Returns:
        Processed DataFrame with non-stationary segments handled
    """
    if strategy not in ['exclude', 'bin']:
        raise StatsError(f"Unknown strategy: {strategy}. Must be 'exclude' or 'bin'.")
    
    # Detect non-stationary segments
    non_stationary_mask = detect_non_stationary_segments(
        df, time_col=time_col, signal_col=signal_col, window_size=window_size
    )
    
    if strategy == 'exclude':
        # Exclude non-stationary segments
        if non_stationary_mask.any():
            n_excluded = non_stationary_mask.sum()
            logger.info(f"Excluding {n_excluded} rows ({100*n_excluded/len(df):.1f}%) due to non-stationarity.")
            df_processed = df[~non_stationary_mask].reset_index(drop=True)
        else:
            df_processed = df.copy()
            logger.info("No non-stationary segments detected. Using all data.")
            
    elif strategy == 'bin':
        # Create a separate bin for non-stationary segments
        df_processed = df.copy()
        if 'stationary_segment' not in df_processed.columns:
            df_processed['stationary_segment'] = 'stationary'
        
        df_processed.loc[non_stationary_mask, 'stationary_segment'] = 'non_stationary'
        logger.info(f"Created separate bin for {non_stationary_mask.sum()} non-stationary rows.")
    
    return df_processed

def run_statistical_analysis(data_path: str, output_path: str, 
                            strategy: str = 'exclude') -> Dict[str, Any]:
    """
    Run full statistical analysis pipeline including non-stationary handling.
    
    Args:
        data_path: Path to energy_samples.csv
        output_path: Path to output JSON
        strategy: Strategy for handling non-stationary segments
        
    Returns:
        Dictionary of results
    """
    # Load data
    df = pd.read_csv(data_path)
    
    # Handle non-stationary segments
    df_clean = handle_non_stationary_segments(df, strategy=strategy)
    
    # If excluded, continue with cleaned data; if binned, proceed with binning
    if 'stationary_segment' in df_clean.columns:
        bins = df_clean.groupby(['stationary_segment', 'frequency_bin', 'material_type'])
    else:
        bins = df_clean.groupby(['frequency_bin', 'material_type'])
    
    results = {
        'summary': {
            'total_samples': len(df),
            'samples_after_processing': len(df_clean),
            'non_stationary_strategy': strategy
        },
        'bins': []
    }
    
    for name, group in bins:
        bin_name = str(name)
        
        # Extract energy data (assuming 'E_trans' or similar column exists)
        energy_col = 'E_trans' if 'E_trans' in group.columns else group.columns[0]
        energies = group[energy_col].dropna().values
        
        if len(energies) < 2:
            continue
        
        # Calculate theoretical parameters
        kT = np.mean(energies)  # Estimate from data
        
        # Perform KS test
        # Define CDF for MB distribution
        def mb_cdf(x):
            if x <= 0:
                return 0.0
            return stats.gamma.cdf(x, a=1.5, scale=kT)
        
        ks_stat, ks_pval = perform_ks_test(energies, mb_cdf)
        
        # Perform Chi-squared test
        # Bin data using standard rules
        n_bins = max(10, int(np.sqrt(len(energies))))
        observed_counts, bin_edges = np.histogram(energies, bins=n_bins)
        
        # Calculate expected counts
        expected_counts = np.zeros(len(observed_counts))
        for i in range(len(bin_edges) - 1):
            bin_lower = bin_edges[i]
            bin_upper = bin_edges[i+1]
            prob = mb_cdf(bin_upper) - mb_cdf(bin_lower)
            expected_counts[i] = prob * len(energies)
        
        # Avoid division by zero
        mask = expected_counts > 0
        if mask.sum() > 1:
            chi2_stat, chi2_pval = perform_chisquared_test(
                observed_counts[mask], expected_counts[mask]
            )
        else:
            chi2_stat, chi2_pval = 0.0, 1.0
        
        results['bins'].append({
            'bin_name': bin_name,
            'n_samples': len(energies),
            'ks_test': {'statistic': float(ks_stat), 'pvalue': float(ks_pval)},
            'chisquared_test': {'statistic': float(chi2_stat), 'pvalue': float(chi2_pval)}
        })
    
    # Apply FDR correction if multiple tests
    pvalues = [b['ks_test']['pvalue'] for b in results['bins']]
    if len(pvalues) > 1:
        rejections = apply_benjamini_hochberg(pvalues)
        for i, b in enumerate(results['bins']):
            b['fdr_rejected'] = rejections[i]
    
    # Save results
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    """CLI entry point for statistical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Statistical analysis of granular energy data')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file')
    parser.add_argument('--strategy', type=str, default='exclude', 
                      choices=['exclude', 'bin'],
                      help='Strategy for non-stationary segments')
    
    args = parser.parse_args()
    
    results = run_statistical_analysis(args.input, args.output, args.strategy)
    print(f"Analysis complete. Results written to {args.output}")
    print(f"Processed {results['summary']['samples_after_processing']} samples "
          f"from {results['summary']['total_samples']} original.")

if __name__ == '__main__':
    main()