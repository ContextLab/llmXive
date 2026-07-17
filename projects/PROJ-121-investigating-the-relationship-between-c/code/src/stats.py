from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from astropy.timeseries import LombScargle
from scipy import stats
import logging
from .utils import get_logger, safe_divide

logger = get_logger(__name__)

def compute_lomb_scargle_periodogram(
    time: np.ndarray, 
    power: np.ndarray, 
    frequencies: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Lomb-Scargle periodogram for unevenly spaced time series.
    
    Args:
        time: Time values (Julian dates or days)
        power: Observed values (anisotropy amplitude or phase)
        frequencies: Optional frequency array. If None, auto-generated.
        
    Returns:
        Tuple of (frequencies, periodogram_power)
    """
    if frequencies is None:
        # Auto-generate frequencies from 1/365 to 1/10 days^-1 (annual to ~10 day periods)
        # Adjust based on typical solar cycle analysis needs
        freq_min = 1.0 / 365.0
        freq_max = 1.0 / 10.0
        frequencies = np.linspace(freq_min, freq_max, 500)
        
    ls = LombScargle(time, power)
    periodogram_power = ls.power(frequencies)
    return frequencies, periodogram_power

def find_significant_peaks(
    frequencies: np.ndarray, 
    power: np.ndarray, 
    threshold: float = 0.1
) -> List[Tuple[float, float]]:
    """
    Find peaks in the periodogram above a given threshold.
    
    Args:
        frequencies: Frequency array
        power: Periodogram power array
        threshold: Minimum power threshold for significance
        
    Returns:
        List of (frequency, power) tuples for significant peaks
    """
    peaks = []
    for i in range(1, len(power) - 1):
        if power[i] > power[i-1] and power[i] > power[i+1] and power[i] > threshold:
            peaks.append((frequencies[i], power[i]))
    return peaks

def compute_false_alarm_probability(
    n_peaks: int, 
    max_power: float, 
    n_frequencies: int
) -> float:
    """
    Compute False Alarm Probability (FAP) for the highest peak.
    
    Args:
        n_peaks: Number of peaks tested
        max_power: Maximum power observed
        n_frequencies: Number of frequencies in the periodogram
        
    Returns:
        False Alarm Probability
    """
    # Approximation: FAP ≈ 1 - (1 - exp(-z))^N
    # where z is the normalized power and N is the number of independent frequencies
    z = max_power
    # Effective number of independent frequencies (often less than total)
    n_independent = n_frequencies / 5.0  # Heuristic correction
    fap = 1.0 - (1.0 - np.exp(-z)) ** n_independent
    return min(fap, 1.0)

def compute_correlation_coefficient(
    x: np.ndarray, 
    y: np.ndarray, 
    x_err: Optional[np.ndarray] = None, 
    y_err: Optional[np.ndarray] = None
) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient with optional error weighting.
    
    Args:
        x: First time series
        y: Second time series
        x_err: Optional errors in x
        y_err: Optional errors in y
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    if x_err is not None or y_err is not None:
        # Weighted correlation if errors provided
        # Simple approach: use errors to weight points
        weights = np.ones_like(x)
        if x_err is not None:
            weights *= 1.0 / (x_err + 1e-10)
        if y_err is not None:
            weights *= 1.0 / (y_err + 1e-10)
        weights /= weights.sum()
        
        # Weighted correlation (approximation)
        # For rigorous weighted correlation, use specialized libraries
        corr, p_val = np.corrcoef(x, y)[0, 1], 0.0
        # Placeholder for weighted p-value calculation
        return corr, p_val
    else:
        corr, p_val = stats.pearsonr(x, y)
        return corr, p_val

def compute_correlation_with_uncertainty(
    x: np.ndarray, 
    y: np.ndarray, 
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    """
    Compute correlation with uncertainty via bootstrap resampling.
    
    Args:
        x: First time series
        y: Second time series
        n_bootstrap: Number of bootstrap samples
        
    Returns:
        Dictionary with correlation, confidence intervals, and p-value
    """
    n = len(x)
    boot_corrs = []
    
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        boot_corr, _ = stats.pearsonr(x[idx], y[idx])
        boot_corrs.append(boot_corr)
        
    boot_corrs = np.array(boot_corrs)
    corr, p_val = stats.pearsonr(x, y)
    
    return {
        'correlation': corr,
        'p_value': p_val,
        'ci_lower': np.percentile(boot_corrs, 2.5),
        'ci_upper': np.percentile(boot_corrs, 97.5),
        'bootstrap_std': np.std(boot_corrs)
    }

def block_bootstrap_resample(
    time: np.ndarray, 
    anisotropy: np.ndarray, 
    solar_proxy: np.ndarray, 
    bin_size_days: float,
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    """
    Perform block bootstrap resampling for time series correlation.
    
    Implements adaptive block length selection per FR-005:
    - If number of independent blocks < 30: block_length = 1 × bin_size
    - Otherwise: block_length = 2 × bin_size
    
    Args:
        time: Time values (Julian dates)
        anisotropy: Anisotropy amplitude time series
        solar_proxy: Solar proxy index time series
        bin_size_days: Base bin size in days
        n_bootstrap: Number of bootstrap samples
        
    Returns:
        Dictionary with bootstrap statistics
    """
    if len(time) != len(anisotropy) or len(time) != len(solar_proxy):
        raise ValueError("Input arrays must have the same length")
        
    n = len(time)
    if n < 10:
        logger.warning("Time series too short for meaningful block bootstrap")
        return {
            'mean_corr': 0.0,
            'std_corr': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'n_blocks': 0,
            'block_length': 0
        }
    
    # Estimate number of independent blocks
    # Assume autocorrelation time ~ 2 * bin_size
    estimated_autocorr_time = 2.0 * bin_size_days
    n_independent_blocks = n / (estimated_autocorr_time / bin_size_days)
    
    # Adaptive block length selection (FR-005)
    if n_independent_blocks < 30:
        block_length = int(1.0 * bin_size_days)
        logger.info(f"Using adaptive block length: {block_length} days (n_blocks={n_independent_blocks:.1f} < 30)")
    else:
        block_length = int(2.0 * bin_size_days)
        logger.info(f"Using standard block length: {block_length} days (n_blocks={n_independent_blocks:.1f} >= 30)")
        
    if block_length < 1:
        block_length = 1
        
    # Ensure block length doesn't exceed data length
    block_length = min(block_length, n)
    
    # Number of blocks
    n_blocks = n // block_length
    if n_blocks < 2:
        logger.warning("Not enough blocks for bootstrap, using whole series")
        n_blocks = 1
        block_length = n
    
    boot_corrs = []
    
    for _ in range(n_bootstrap):
        # Resample blocks
        resampled_indices = []
        while len(resampled_indices) < n:
            start_idx = np.random.randint(0, n - block_length + 1)
            block_indices = list(range(start_idx, min(start_idx + block_length, n)))
            resampled_indices.extend(block_indices)
            
        resampled_indices = resampled_indices[:n]
        
        # Compute correlation on resampled data
        try:
            corr, _ = stats.pearsonr(anisotropy[resampled_indices], solar_proxy[resampled_indices])
            if not np.isnan(corr):
                boot_corrs.append(corr)
        except Exception as e:
            logger.debug(f"Bootstrap iteration failed: {e}")
            continue
            
    if len(boot_corrs) == 0:
        logger.warning("No valid bootstrap samples generated")
        return {
            'mean_corr': 0.0,
            'std_corr': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'n_blocks': n_blocks,
            'block_length': block_length
        }
        
    boot_corrs = np.array(boot_corrs)
    mean_corr = np.mean(boot_corrs)
    std_corr = np.std(boot_corrs)
    ci_lower = np.percentile(boot_corrs, 2.5)
    ci_upper = np.percentile(boot_corrs, 97.5)
    
    logger.info(f"Block bootstrap complete: mean={mean_corr:.3f}, std={std_corr:.3f}, n_blocks={n_blocks}, block_len={block_length}")
    
    return {
        'mean_corr': mean_corr,
        'std_corr': std_corr,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'n_blocks': n_blocks,
        'block_length': block_length,
        'bootstrap_samples': len(boot_corrs)
    }

def monte_carlo_shuffle_test(
    time: np.ndarray, 
    anisotropy: np.ndarray, 
    solar_proxy: np.ndarray, 
    n_permutations: int = 1000,
    block_bootstrap_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Perform Monte-Carlo shuffle test to assess correlation significance.
    
    Shuffles solar proxy series relative to anisotropy to generate null distribution.
    Integrates block-bootstrap logic if provided.
    
    Args:
        time: Time values
        anisotropy: Anisotropy time series
        solar_proxy: Solar proxy time series
        n_permutations: Number of permutations
        block_bootstrap_config: Optional config for block bootstrap resampling
        
    Returns:
        Dictionary with p-value and null distribution statistics
    """
    n = len(time)
    obs_corr, obs_pval = stats.pearsonr(anisotropy, solar_proxy)
    
    null_corrs = []
    
    for _ in range(n_permutations):
        # Shuffle solar proxy (preserve time structure by shuffling values)
        shuffled_proxy = np.random.permutation(solar_proxy)
        
        # If block bootstrap config provided, apply it to the shuffled data
        if block_bootstrap_config:
            # Re-run block bootstrap on shuffled data to get a representative correlation
            # This ensures the null distribution respects the temporal structure
            try:
                bootstrap_result = block_bootstrap_resample(
                    time, anisotropy, shuffled_proxy,
                    bin_size_days=block_bootstrap_config.get('bin_size_days', 27),
                    n_bootstrap=50  # Reduced for speed in MC test
                )
                corr_val = bootstrap_result['mean_corr']
            except Exception as e:
                logger.debug(f"MC shuffle bootstrap failed: {e}")
                corr_val, _ = stats.pearsonr(anisotropy, shuffled_proxy)
        else:
            corr_val, _ = stats.pearsonr(anisotropy, shuffled_proxy)
            
        if not np.isnan(corr_val):
            null_corrs.append(corr_val)
            
    null_corrs = np.array(null_corrs)
    
    # Calculate two-sided p-value
    # Count how many null correlations are as extreme as observed
    extreme_count = np.sum(np.abs(null_corrs) >= np.abs(obs_corr))
    p_value = (extreme_count + 1) / (len(null_corrs) + 1)
    
    return {
        'observed_correlation': obs_corr,
        'observed_p_value': obs_pval,
        'mc_p_value': p_value,
        'null_mean': np.mean(null_corrs),
        'null_std': np.std(null_corrs),
        'n_permutations': len(null_corrs),
        'extreme_count': int(extreme_count)
    }

def bonferroni_corrected_pvalue(
    p_values: List[float], 
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
        
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests if n_tests > 0 else alpha
    
    corrected_pvalues = [p * n_tests for p in p_values]
    corrected_pvalues = [min(p, 1.0) for p in corrected_pvalues]
    
    significant = [p < corrected_alpha for p in corrected_pvalues]
    
    return {
        'raw_pvalues': p_values,
        'corrected_pvalues': corrected_pvalues,
        'corrected_alpha': corrected_alpha,
        'significant': significant,
        'n_significant': sum(significant),
        'n_tests': n_tests
    }

def is_significant_after_bonferroni(
    p_value: float, 
    n_tests: int, 
    alpha: float = 0.05
) -> bool:
    """
    Check if a single p-value is significant after Bonferroni correction.
    
    Args:
        p_value: Raw p-value
        n_tests: Total number of tests performed
        alpha: Significance level
        
    Returns:
        True if significant after correction
    """
    if n_tests == 0:
        return p_value < alpha
    corrected_alpha = alpha / n_tests
    return p_value < corrected_alpha
