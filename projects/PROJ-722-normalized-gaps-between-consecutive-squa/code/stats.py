import numpy as np
from scipy import stats
from code.logging_config import get_logger

logger = get_logger(__name__)

def lilliefors_ks(data: np.ndarray) -> float:
    """
    Perform a Lilliefors-style KS test for exponentiality.
    
    This function estimates the mean from the data, normalizes the data
    by dividing by the mean, and compares the empirical CDF against the
    standard exponential CDF (rate=1).
    
    Args:
        data: 1D numpy array of gap values.
        
    Returns:
        The KS statistic (D).
        
    Raises:
        ValueError: If data is empty or mean is zero.
    """
    if len(data) == 0:
        raise ValueError("Input data array is empty.")
    
    mu = np.mean(data)
    if mu == 0:
        raise ValueError("Mean of data is zero; cannot normalize.")
    
    # Normalize data to have mean 1 (standard exponential)
    normalized_data = data / mu
    
    # Sort data for CDF calculation
    sorted_data = np.sort(normalized_data)
    n = len(sorted_data)
    
    # Calculate empirical CDF values
    # F_n(x) = i/n for x in [x_i, x_{i+1})
    # We compare against the theoretical CDF of Exp(1): 1 - exp(-x)
    theoretical_cdf = 1 - np.exp(-sorted_data)
    empirical_cdf = np.arange(1, n + 1) / n
    
    # Calculate KS statistic (maximum absolute difference)
    # D = max(|F_n(x) - F(x)|, |F_n(x-) - F(x)|)
    # Since we use sorted data, we check both the jump and the value at the point
    diff_pos = np.abs(empirical_cdf - theoretical_cdf)
    diff_neg = np.abs((np.arange(0, n) / n) - theoretical_cdf)
    
    ks_stat = np.max(np.concatenate([diff_pos, diff_neg]))
    
    logger.debug(f"Lilliefors KS statistic calculated: {ks_stat:.6f}")
    return ks_stat

def monte_carlo_pvalue(ks_stat: float, data: np.ndarray, n_resamples: int = 10000) -> float:
    """
    Estimate p-value for the Lilliefors test via Monte Carlo simulation.
    
    This function resamples the data (with replacement) to generate a null
    distribution of KS statistics, assuming the data comes from an exponential
    distribution with unknown mean.
    
    Args:
        ks_stat: The observed KS statistic from lilliefors_ks().
        data: The original data array (used for resampling).
        n_resamples: Number of Monte Carlo resamples to generate.
        
    Returns:
        The estimated p-value (float in [0, 1]).
        
    Note:
        Handles edge cases where p-value is exactly 0.0 or 1.0 by applying
        a small correction to avoid division-by-zero or misleading perfect scores.
    """
    if len(data) == 0:
        raise ValueError("Input data array is empty for Monte Carlo simulation.")
    
    n = len(data)
    count_greater = 0
    
    logger.info(f"Starting Monte Carlo simulation with {n_resamples} resamples...")
    
    # Pre-calculate mean of original data for efficiency if needed, 
    # though we resample from data directly.
    # For the null hypothesis, we generate samples from an exponential distribution
    # with the same mean as the observed data.
    observed_mean = np.mean(data)
    
    for i in range(n_resamples):
        # Resample from the data to mimic the null distribution
        # Since we are testing against exponential, we should ideally
        # generate synthetic exponential data with the observed mean.
        # However, the standard Lilliefors Monte Carlo approach often
        # resamples the standardized residuals or generates new data.
        # Given the instruction to test against Exponential(1) after normalization,
        # we generate new exponential samples with mean=observed_mean.
        synthetic_sample = np.random.exponential(scale=observed_mean, size=n)
        
        # Calculate KS statistic for this synthetic sample
        # (This effectively tests if the synthetic sample comes from Exp(mean))
        # Note: The standard Lilliefors test for exponentiality involves
        # estimating the parameter from the sample and comparing to standard Exp(1).
        # Here we generate Exp(mean) and normalize it to Exp(1) implicitly by the test logic.
        
        # Re-implementing the logic inline for the synthetic sample
        synthetic_mean = np.mean(synthetic_sample)
        if synthetic_mean == 0:
            continue # Skip degenerate resamples
            
        synthetic_normalized = synthetic_sample / synthetic_mean
        sorted_syn = np.sort(synthetic_normalized)
        n_syn = len(sorted_syn)
        
        theo_cdf_syn = 1 - np.exp(-sorted_syn)
        emp_cdf_syn = np.arange(1, n_syn + 1) / n_syn
        emp_cdf_neg_syn = np.arange(0, n_syn) / n_syn
        
        diff_syn = np.maximum(np.abs(emp_cdf_syn - theo_cdf_syn), 
                              np.abs(emp_cdf_neg_syn - theo_cdf_syn))
        ks_syn = np.max(diff_syn)
        
        if ks_syn >= ks_stat:
            count_greater += 1
        
        # Optional: Log progress every 10%
        if (i + 1) % (n_resamples // 10) == 0:
            logger.debug(f"Monte Carlo progress: {i+1}/{n_resamples}")

    # Calculate raw p-value
    p_value = count_greater / n_resamples
    
    # Edge case handling:
    # If p_value is exactly 0.0, it implies the observed statistic is larger
    # than all simulated statistics. We return a small value (1/(n_resamples+1))
    # to indicate "very small" rather than "zero".
    # If p_value is exactly 1.0, it implies the observed statistic is smaller
    # than all simulated statistics. We return (n_resamples/(n_resamples+1))
    # to indicate "very large" rather than "perfect".
    # This prevents issues in downstream statistical interpretation.
    
    if p_value == 0.0:
        p_value = 1.0 / (n_resamples + 1)
        logger.warning(f"Raw p-value was 0.0. Adjusted to {p_value:.6f} to avoid zero.")
    elif p_value == 1.0:
        p_value = n_resamples / (n_resamples + 1)
        logger.warning(f"Raw p-value was 1.0. Adjusted to {p_value:.6f} to avoid one.")
    
    logger.info(f"Monte Carlo p-value calculated: {p_value:.6f}")
    return p_value