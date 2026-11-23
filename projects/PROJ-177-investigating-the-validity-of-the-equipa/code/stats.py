import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import hilbert
from typing import Dict, List, Tuple, Any, Optional
import logging
import os
from pathlib import Path

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def detect_non_stationary_segments(signal: np.ndarray, threshold: float = 0.1) -> np.ndarray:
    """
    Detect non-stationary segments in a driving signal using sliding window variance.
    
    Args:
        signal: 1D array of driving signal values
        threshold: Variance change threshold for non-stationarity detection
        
    Returns:
        Boolean mask where True indicates non-stationary segments
    """
    window_size = len(signal) // 20
    if window_size < 10:
        window_size = 10
    
    variances = []
    for i in range(0, len(signal) - window_size, window_size // 2):
        segment = signal[i:i+window_size]
        variances.append(np.var(segment))
    
    variances = np.array(variances)
    mean_var = np.mean(variances)
    non_stationary_mask = np.abs(variances - mean_var) > threshold * mean_var
    
    # Expand mask to full signal length
    full_mask = np.zeros(len(signal), dtype=bool)
    for i, is_non_stat in enumerate(non_stationary_mask):
        start_idx = i * (window_size // 2)
        end_idx = min(start_idx + window_size, len(signal))
        if is_non_stat:
            full_mask[start_idx:end_idx] = True
            
    return full_mask

def handle_non_stationary_segments(df: pd.DataFrame, signal_col: str, 
                                  strategy: str = 'exclude') -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Handle non-stationary segments based on specified strategy.
    
    Args:
        df: DataFrame containing the signal
        signal_col: Name of the signal column
        strategy: 'exclude' to mask segments, 'bin' to group by frequency
        
    Returns:
        Updated DataFrame and mask array
    """
    signal = df[signal_col].values
    mask = detect_non_stationary_segments(signal)
    
    if strategy == 'exclude':
        df['non_stationary_mask'] = mask
        logging.info(f"Marked {np.sum(mask)} samples as non-stationary for exclusion")
    elif strategy == 'bin':
        df['non_stationary_mask'] = mask
        logging.info(f"Non-stationary segments identified for binning strategy")
    else:
        raise StatsError(f"Unknown strategy: {strategy}")
        
    return df, mask

def bin_energy_data(df: pd.DataFrame, frequency_bins: Optional[List[float]] = None,
                   material_col: str = 'material_type', 
                   frequency_col: str = 'driving_frequency',
                   chirp_result_path: Optional[str] = None,
                   power_analysis_path: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Bin energy data by driving frequency and material type.
    
    Args:
        df: DataFrame with energy components (from energy_samples.csv)
        frequency_bins: Optional list of bin edges for frequency. If None, auto-detect.
        material_col: Column name for material type
        frequency_col: Column name for driving frequency
        chirp_result_path: Path to chirp_handling_result.csv (optional)
        power_analysis_path: Path to power_analysis_plan.json (optional)
        
    Returns:
        Dictionary mapping (frequency_bin, material) tuples to DataFrames
    """
    logger = logging.getLogger(__name__)
    
    # Validate input file is not a test file
    if 'test_' in str(df.columns).lower() or any('test_' in str(col) for col in df.columns):
        raise FileNotFoundError(
            "Input data appears to be test data (contains 'test_'). "
            "Real data is required for statistical analysis."
        )
    
    # Load chirp handling result if present
    exclusion_mask = None
    if chirp_result_path and os.path.exists(chirp_result_path):
        try:
            chirp_df = pd.read_csv(chirp_result_path)
            if 'mask_index' in chirp_df.columns and 'strategy' in chirp_df.columns:
                # Create boolean mask for exclusion
                excluded_indices = set(chirp_df[chirp_df['strategy'] == 'excluded']['mask_index'])
                exclusion_mask = df.index.isin(excluded_indices)
                logger.info(f"Loaded chirp exclusion mask: {exclusion_mask.sum()} samples excluded")
        except Exception as e:
            logger.warning(f"Could not load chirp handling result: {e}. Proceeding without exclusion.")
    
    # Load power analysis plan if present to inform binning strategy
    bin_strategy = 'auto'
    min_samples_per_bin = 50
    if power_analysis_path and os.path.exists(power_analysis_path):
        try:
            with open(power_analysis_path, 'r') as f:
                power_plan = json.load(f)
            if 'binning_strategy' in power_plan:
                bin_strategy = power_plan['binning_strategy']
            if 'min_samples_per_bin' in power_plan:
                min_samples_per_bin = power_plan['min_samples_per_bin']
            logger.info(f"Using power analysis plan: strategy={bin_strategy}, min_samples={min_samples_per_bin}")
        except Exception as e:
            logger.warning(f"Could not load power analysis plan: {e}. Using defaults.")
    
    # Apply exclusion mask if available
    if exclusion_mask is not None:
        df = df[~exclusion_mask].copy()
    
    # Determine frequency bins if not provided
    if frequency_bins is None:
        unique_freqs = df[frequency_col].unique()
        if len(unique_freqs) < 2:
            # If only one frequency, create a single bin
            min_freq = df[frequency_col].min()
            max_freq = df[frequency_col].max()
            frequency_bins = [min_freq - 0.1, max_freq + 0.1]
        else:
            # Create fixed intervals based on unique frequencies
            min_freq = df[frequency_col].min()
            max_freq = df[frequency_col].max()
            n_bins = max(5, len(unique_freqs) // 2)
            frequency_bins = np.linspace(min_freq, max_freq, n_bins + 1).tolist()
    
    # Assign frequency bins
    df['frequency_bin'] = pd.cut(df[frequency_col], bins=frequency_bins, include_lowest=True)
    
    # Group by frequency bin and material type
    binned_data = {}
    for (freq_bin, material), group in df.groupby(['frequency_bin', material_col]):
        # Check minimum sample size
        if len(group) < min_samples_per_bin:
            logger.warning(f"Bin ({freq_bin}, {material}) has only {len(group)} samples (< {min_samples_per_bin}). Flagging as insufficient_data.")
            # Still include but mark in metadata
            group['insufficient_data'] = True
        else:
            group['insufficient_data'] = False
        
        binned_data[(str(freq_bin), material)] = group
    
    logger.info(f"Created {len(binned_data)} bins for statistical analysis")
    return binned_data

def calculate_maxwell_boltzmann_pdf(energies: np.ndarray, T: float, dof: int = 3) -> np.ndarray:
    """
    Calculate theoretical Maxwell-Boltzmann PDF for given energies.
    
    Args:
        energies: Array of energy values
        T: Temperature parameter (from config.yaml)
        dof: Degrees of freedom (default 3 for translational)
        
    Returns:
        PDF values at energy points
    """
    if T <= 0:
        raise StatsError("Temperature T must be positive")
    
    k_B = 1.380649e-23  # Boltzmann constant in J/K
    beta = 1.0 / (k_B * T)
    
    # Maxwell-Boltzmann distribution for energy: f(E) = (beta^(dof/2) / Gamma(dof/2)) * E^(dof/2 - 1) * exp(-beta * E)
    # For simplicity, we use the chi-squared distribution form
    scale = k_B * T
    pdf_vals = stats.gamma.pdf(energies, a=dof/2, scale=scale)
    
    return pdf_vals

def perform_ks_test(empirical_data: np.ndarray, T: float, dof: int = 3,
                   lilliefors: bool = False) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test against theoretical Maxwell-Boltzmann distribution.
    
    Args:
        empirical_data: Array of observed energy values
        T: Temperature parameter (from config.yaml)
        dof: Degrees of freedom
        lilliefors: If True, use Lilliefors correction (parameters estimated from data)
        
    Returns:
        Dictionary with statistic, p-value, and rejection flag
    """
    if len(empirical_data) < 3:
        raise StatsError("Insufficient data points for KS test")
    
    k_B = 1.380649e-23
    scale = k_B * T
    
    if lilliefors:
        # Estimate T from sample mean for robustness check
        # For MB distribution, mean = (dof/2) * k_B * T
        estimated_T = np.mean(empirical_data) / (dof/2 * k_B)
        scale = k_B * estimated_T
        logging.info(f"Lilliefors correction: estimated T={estimated_T:.6e} K from sample mean")
    
    # Theoretical CDF
    cdf_theoretical = stats.gamma.cdf(empirical_data, a=dof/2, scale=scale)
    
    # Empirical CDF
    sorted_data = np.sort(empirical_data)
    n = len(sorted_data)
    empirical_cdf = np.arange(1, n+1) / n
    
    # KS statistic
    d_stat = np.max(np.abs(empirical_cdf - cdf_theoretical[np.searchsorted(sorted_data, sorted_data)]))
    
    # P-value calculation (approximation)
    # For large n, use asymptotic distribution
    if n > 100:
        lambda_val = (np.sqrt(n) + 0.12 + 0.11/np.sqrt(n)) * d_stat
        p_value = 2 * np.exp(-2 * lambda_val**2)
    else:
        # Use exact KS distribution for small n
        p_value = stats.ks_1samp(sorted_data, 'gamma', args=(dof/2, scale))[1]
    
    # Rejection flag at alpha=0.05
    alpha = 0.05
    reject_null = p_value < alpha
    
    return {
        'statistic': float(d_stat),
        'p_value': float(p_value),
        'reject_null': bool(reject_null),
        'method': 'lilliefors' if lilliefors else 'theoretical',
        'n_samples': int(n)
    }

def perform_chisquared_test(empirical_data: np.ndarray, T: float, dof: int = 3,
                            n_bins: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform Chi-squared goodness-of-fit test against Maxwell-Boltzmann distribution.
    
    Args:
        empirical_data: Array of observed energy values
        T: Temperature parameter
        dof: Degrees of freedom
        n_bins: Number of bins (auto-selected if None)
        
    Returns:
        Dictionary with statistic, p-value, and rejection flag
    """
    if len(empirical_data) < 10:
        raise StatsError("Insufficient data points for Chi-squared test")
    
    # Auto-select bin count using Freedman-Diaconis rule
    if n_bins is None:
        iqr = np.subtract(*np.percentile(empirical_data, [75, 25]))
        bin_width = 2 * iqr / (len(empirical_data) ** (1/3))
        if bin_width > 0:
            n_bins = int(np.ceil((np.max(empirical_data) - np.min(empirical_data)) / bin_width))
        else:
            n_bins = 10
        n_bins = max(5, min(n_bins, 20))  # Ensure reasonable range
    
    # Create bins
    hist, bin_edges = np.histogram(empirical_data, bins=n_bins)
    
    # Calculate expected counts from MB distribution
    k_B = 1.380649e-23
    scale = k_B * T
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # PDF values at bin centers
    pdf_vals = stats.gamma.pdf(bin_centers, a=dof/2, scale=scale)
    # Normalize to match total count
    total_count = len(empirical_data)
    expected_counts = pdf_vals * np.diff(bin_edges) * total_count / np.sum(pdf_vals * np.diff(bin_edges))
    
    # Chi-squared statistic
    chi2_stat = np.sum((hist - expected_counts)**2 / expected_counts)
    df = n_bins - 1 - 1  # -1 for estimated parameter (if any), -1 for constraint
    
    # P-value
    p_value = 1 - stats.chi2.cdf(chi2_stat, df)
    
    # Rejection flag
    alpha = 0.05
    reject_null = p_value < alpha
    
    return {
        'statistic': float(chi2_stat),
        'p_value': float(p_value),
        'reject_null': bool(reject_null),
        'n_bins': int(n_bins),
        'df': int(df),
        'n_samples': int(len(empirical_data))
    }

def apply_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
        
    Returns:
        List of boolean rejection flags (True = reject null)
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate critical values
    critical_values = (np.arange(1, n+1) / n) * alpha
    
    # Find largest k such that p_(k) <= critical_k
    reject_mask = sorted_p <= critical_values
    if np.any(reject_mask):
        k = np.argmax(reject_mask[::-1]) + 1  # Find largest k
    else:
        k = 0
    
    # Rejection decision for original order
    decisions = np.zeros(n, dtype=bool)
    decisions[sorted_indices[:k]] = True
    
    return decisions.tolist()

def calculate_effective_bins(n_samples: int, expected_min: int = 5) -> int:
    """
    Calculate effective number of bins ensuring expected count >= 5 per bin.
    
    Args:
        n_samples: Total number of samples
        expected_min: Minimum expected count per bin
        
    Returns:
        Recommended number of bins
    """
    max_bins = n_samples // expected_min
    return max(5, min(max_bins, 20))

def run_statistical_analysis(binned_data: Dict[str, pd.DataFrame], 
                            config: Dict[str, Any],
                            chirp_result_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Run full statistical analysis on binned data.
    
    Args:
        binned_data: Dictionary of binned energy data
        config: Configuration dictionary with temperature T
        chirp_result_path: Path to chirp handling result
        
    Returns:
        List of result dictionaries for each bin
    """
    results = []
    T = config.get('temperature', 300.0)  # Default 300K if not specified
    
    for (freq_bin, material), group in binned_data.items():
        # Extract energy component (e.g., E_trans)
        energies = group['E_trans'].values
        
        if len(energies) < 10:
            logging.warning(f"Skipping bin ({freq_bin}, {material}): insufficient samples ({len(energies)})")
            continue
        
        # Perform KS test (theoretical)
        try:
            ks_result = perform_ks_test(energies, T, dof=3, lilliefors=False)
            ks_result['bin'] = f"{freq_bin}-{material}"
            ks_result['test_type'] = 'KS_theoretical'
            results.append(ks_result)
        except Exception as e:
            logging.error(f"KS test failed for bin ({freq_bin}, {material}): {e}")
        
        # Perform KS test (Lilliefors)
        try:
            ks_lillie_result = perform_ks_test(energies, T, dof=3, lilliefors=True)
            ks_lillie_result['bin'] = f"{freq_bin}-{material}"
            ks_lillie_result['test_type'] = 'KS_lilliefors'
            results.append(ks_lillie_result)
        except Exception as e:
            logging.error(f"Lilliefors KS test failed for bin ({freq_bin}, {material}): {e}")
        
        # Perform Chi-squared test
        try:
            chi2_result = perform_chisquared_test(energies, T, dof=3)
            chi2_result['bin'] = f"{freq_bin}-{material}"
            chi2_result['test_type'] = 'Chi-squared'
            results.append(chi2_result)
        except Exception as e:
            logging.error(f"Chi-squared test failed for bin ({freq_bin}, {material}): {e}")
    
    return results

def main():
    """Main entry point for statistical analysis."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Statistical analysis of granular system energy data')
    parser.add_argument('--input', type=str, required=True, help='Path to energy_samples.csv')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    parser.add_argument('--chirp', type=str, default=None, help='Path to chirp_handling_result.csv')
    parser.add_argument('--power-plan', type=str, default=None, help='Path to power_analysis_plan.json')
    parser.add_argument('--output', type=str, default='artifacts/statistical_results.json', help='Output JSON path')
    
    args = parser.parse_args()
    
    # Load data
    df = pd.read_csv(args.input)
    
    # Load config
    import yaml
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Bin data
    frequency_bins = config.get('frequency_bins', None)
    binned_data = bin_energy_data(
        df, 
        frequency_bins=frequency_bins,
        chirp_result_path=args.chirp,
        power_analysis_path=args.power_plan
    )
    
    # Run analysis
    results = run_statistical_analysis(binned_data, config, args.chirp)
    
    # Apply FDR correction
    if results:
        p_values = [r['p_value'] for r in results if 'p_value' in r]
        if p_values:
            decisions = apply_benjamini_hochberg(p_values)
            for i, r in enumerate(results):
                if 'p_value' in r and i < len(decisions):
                    r['corrected_reject'] = decisions[i]
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Statistical analysis complete. Results saved to {args.output}")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    main()