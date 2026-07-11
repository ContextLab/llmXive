from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from astropy.timeseries import LombScargle
from scipy import stats
import logging
from .utils import get_logger

# Bonferroni correction constant based on task requirements
# α = 0.0017 (typically 0.05 / 29 tests, or similar conservative estimate)
BONFERRONI_ALPHA = 0.0017

def bonferroni_corrected_pvalue(raw_pvalue: float, n_tests: int) -> float:
    """
    Apply Bonferroni correction to a raw p-value.
    
    Args:
        raw_pvalue: The uncorrected p-value from a statistical test.
        n_tests: The total number of independent tests performed.
    
    Returns:
        The Bonferroni-corrected p-value. 
        Note: If raw_pvalue * n_tests > 1.0, it is capped at 1.0.
    """
    if n_tests <= 0:
        raise ValueError("n_tests must be a positive integer")
    if not (0.0 <= raw_pvalue <= 1.0):
        raise ValueError("raw_pvalue must be between 0.0 and 1.0")
    
    corrected = raw_pvalue * n_tests
    return min(corrected, 1.0)

def is_significant_after_bonferroni(
    raw_pvalue: float, 
    n_tests: int, 
    alpha: float = BONFERRONI_ALPHA
) -> Tuple[bool, float]:
    """
    Determine if a result is statistically significant after Bonferroni correction.
    
    This function implements the logic required for T024:
    1. Calculates the corrected p-value.
    2. Compares it against the significance threshold (alpha).
    3. Returns a boolean flag indicating if the result is "positive" (significant).
    
    Args:
        raw_pvalue: The p-value obtained from the statistical test (e.g., FAP).
        n_tests: The number of tests performed (for correction factor).
        alpha: The significance threshold. Defaults to 0.0017.
    
    Returns:
        A tuple containing:
        - is_positive (bool): True if corrected p-value <= alpha.
        - corrected_pvalue (float): The Bonferroni-corrected p-value.
    """
    corrected_p = bonferroni_corrected_pvalue(raw_pvalue, n_tests)
    is_positive = corrected_p <= alpha
    return is_positive, corrected_p

def compute_lomb_scargle_periodogram(
    times: np.ndarray,
    values: np.ndarray,
    frequency: Optional[np.ndarray] = None,
    nperseg: int = 256
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Lomb-Scargle periodogram for unevenly spaced data.
    
    Args:
        times: Array of time values.
        values: Array of observed values.
        frequency: Optional array of frequencies to evaluate.
        nperseg: Number of segments for frequency estimation if frequency is None.
    
    Returns:
        Tuple of (frequencies, power).
    """
    logger = get_logger()
    if len(times) != len(values):
        raise ValueError("times and values must have the same length")
    
    if frequency is None:
        # Automatic frequency selection
        model = LombScargle(times, values)
        frequency, power = model.autofrequency(nperseg=nperseg)
    else:
        model = LombScargle(times, values)
        power = model.power(frequency)
    
    return frequency, power

def find_significant_peaks(
    frequencies: np.ndarray,
    powers: np.ndarray,
    threshold: float
) -> List[Tuple[float, float]]:
    """
    Identify peaks in the periodogram that exceed a given power threshold.
    
    Args:
        frequencies: Array of frequencies.
        powers: Array of periodogram powers.
        threshold: Minimum power required to be considered a peak.
    
    Returns:
        List of (frequency, power) tuples for significant peaks.
    """
    significant = []
    for f, p in zip(frequencies, powers):
        if p > threshold:
            significant.append((f, p))
    return significant

def compute_false_alarm_probability(
    periodogram_power: float,
    n_independent: int
) -> float:
    """
    Compute the False Alarm Probability (FAP) for a given periodogram power.
    
    Uses the approximation FAP = (1 - (1 - p)^N) where p is the single-trial
    probability. For high powers, p ~ exp(-z) where z is normalized power.
    
    Args:
        periodogram_power: The observed power value.
        n_independent: Number of independent frequencies tested.
    
    Returns:
        The FAP value (0.0 to 1.0).
    """
    # Single trial probability approximation for high powers
    # p_single = exp(-periodogram_power) is a common approximation for normalized power
    # However, standard astropy LombScargle returns normalized power where
    # FAP = (1 - (1 - exp(-z))^N)
    
    if periodogram_power < 0:
        return 1.0
    
    p_single = np.exp(-periodogram_power)
    fap = 1.0 - (1.0 - p_single) ** n_independent
    return min(max(fap, 0.0), 1.0)

def compute_correlation_coefficient(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and p-value.
    
    Args:
        x: First variable.
        y: Second variable.
    
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    
    corr, p_value = stats.pearsonr(x, y)
    return float(corr), float(p_value)

def block_bootstrap_resample(
    data: np.ndarray,
    block_size: int,
    n_iterations: int = 1000
) -> np.ndarray:
    """
    Perform block bootstrap resampling on the data.
    
    Args:
        data: Input data array.
        block_size: Size of blocks to resample.
        n_iterations: Number of bootstrap iterations.
    
    Returns:
        Array of bootstrap statistics (e.g., correlation coefficients).
    """
    n = len(data)
    n_blocks = int(np.ceil(n / block_size))
    stats_list = []
    
    for _ in range(n_iterations):
        # Resample blocks with replacement
        indices = np.random.randint(0, n_blocks, size=n_blocks)
        block_starts = indices * block_size
        # Flatten and trim to original size
        resampled = np.concatenate([data[s:s+block_size] for s in block_starts])
        resampled = resampled[:n]
        # Example statistic: mean (can be replaced with correlation logic in caller)
        stats_list.append(np.mean(resampled))
    
    return np.array(stats_list)

def monte_carlo_shuffle_test(
    times: np.ndarray,
    anisotropy: np.ndarray,
    solar_proxy: np.ndarray,
    n_permutations: int = 1000
) -> float:
    """
    Perform a Monte Carlo shuffle test to assess correlation significance.
    
    Shuffles the solar proxy series relative to the anisotropy series to create
    a null distribution, then compares the observed correlation to this distribution.
    
    Args:
        times: Time stamps (used for alignment).
        anisotropy: Anisotropy measurements.
        solar_proxy: Solar proxy measurements.
        n_permutations: Number of random shuffles.
    
    Returns:
        The p-value (fraction of shuffled correlations >= observed correlation).
    """
    if len(anisotropy) != len(solar_proxy):
        raise ValueError("anisotropy and solar_proxy must have the same length")
    
    observed_corr, _ = compute_correlation_coefficient(anisotropy, solar_proxy)
    
    count = 0
    for _ in range(n_permutations):
        shuffled_proxy = np.random.permutation(solar_proxy)
        shuffled_corr, _ = compute_correlation_coefficient(anisotropy, shuffled_proxy)
        if np.abs(shuffled_corr) >= np.abs(observed_corr):
            count += 1
    
    return count / n_permutations

def compute_correlation_with_uncertainty(
    times: np.ndarray,
    anisotropy: np.ndarray,
    solar_proxy: np.ndarray,
    block_size: int,
    n_bootstrap: int = 1000
) -> Dict[str, float]:
    """
    Compute correlation with uncertainty estimates using block bootstrap.
    
    Args:
        times: Time stamps.
        anisotropy: Anisotropy data.
        solar_proxy: Solar proxy data.
        block_size: Block size for bootstrap.
        n_bootstrap: Number of bootstrap iterations.
    
    Returns:
        Dictionary with 'correlation', 'p_value', 'std_error', 'ci_lower', 'ci_upper'.
    """
    corr, p_val = compute_correlation_coefficient(anisotropy, solar_proxy)
    
    # Block bootstrap for uncertainty
    # Combine data into a single array of pairs to preserve structure during block resampling
    # We resample indices
    n = len(times)
    indices = np.arange(n)
    n_blocks = int(np.ceil(n / block_size))
    
    bootstrap_corrs = []
    for _ in range(n_bootstrap):
        # Resample block indices
        block_indices = np.random.randint(0, n_blocks, size=n_blocks)
        selected_indices = np.concatenate([np.arange(i*block_size, (i+1)*block_size) for i in block_indices])
        selected_indices = selected_indices[selected_indices < n]
        
        if len(selected_indices) == 0:
            continue
            
        boot_aniso = anisotropy[selected_indices]
        boot_proxy = solar_proxy[selected_indices]
        
        if len(boot_aniso) > 1:
            c, _ = compute_correlation_coefficient(boot_aniso, boot_proxy)
            bootstrap_corrs.append(c)
    
    if len(bootstrap_corrs) > 0:
        std_err = np.std(bootstrap_corrs)
        ci_lower = np.percentile(bootstrap_corrs, 2.5)
        ci_upper = np.percentile(bootstrap_corrs, 97.5)
    else:
        std_err = np.nan
        ci_lower = np.nan
        ci_upper = np.nan
    
    return {
        'correlation': float(corr),
        'p_value': float(p_val),
        'std_error': float(std_err),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper)
    }