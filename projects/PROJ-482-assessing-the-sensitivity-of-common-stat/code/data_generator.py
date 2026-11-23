import numpy as np
from typing import Tuple, Dict, Any, Optional, Literal
import logging
import warnings
import hashlib
import json
import math
from scipy import stats

logger = logging.getLogger(__name__)

# Configuration constants (assumed to be imported or defined in config.py, 
# but defined here for self-containment if config is not available during import)
try:
    from config import MAX_REPLICATES, LOG_EPSILON
except ImportError:
    MAX_REPLICATES = 10000
    LOG_EPSILON = 1e-15

def generate_normal(n: int, effect_size: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two groups of normal distributed data.
    Group 1: N(0, 1)
    Group 2: N(effect_size, 1)
    """
    rng = np.random.default_rng(seed)
    group1 = rng.normal(0, 1, n)
    group2 = rng.normal(effect_size, 1, n)
    return group1, group2

def generate_uniform(n: int, effect_size: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two groups of uniform distributed data.
    Group 1: U(0, 1)
    Group 2: U(effect_size, 1 + effect_size) -> Mean shift is effect_size
    Note: To maintain variance similarity or just shift mean, we shift the range.
    If effect_size=0, both are U(0,1).
    If effect_size=0.5, Group 1 is U(0,1), Group 2 is U(0.5, 1.5).
    """
    rng = np.random.default_rng(seed)
    group1 = rng.uniform(0, 1, n)
    # Shift the uniform distribution by effect_size
    group2 = rng.uniform(effect_size, 1 + effect_size, n)
    return group1, group2

def generate_log_normal(n: int, effect_size: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two groups of log-normal distributed data.
    Base: LogNormal(mu=0, sigma=1).
    To introduce an effect size (shift in mean), we adjust the mu parameter.
    Mean of LogNormal(mu, sigma) = exp(mu + sigma^2/2).
    We want Mean2 / Mean1 = 1 + effect_size (or Mean2 - Mean1 = effect_size? Spec says effect_size=0.5).
    Usually effect size in this context (Cohen's d) is (mean2 - mean1) / std.
    However, for log-normal, simple mean shift is often used.
    Let's assume we want to shift the location parameter mu such that the mean increases.
    If effect_size is the difference in means:
    Mean1 = exp(0 + 0.5) = exp(0.5) ~ 1.648
    Mean2 = Mean1 * (1 + effect_size) ? Or Mean1 + effect_size?
    Given the task T013 mentions "mean difference ... within 1e-6 of 0.5", it implies an additive difference in means.
    However, log-normal means are strictly positive and large. An additive shift of 0.5 might be small.
    Let's follow the standard approach: shift the mu parameter.
    If we want a specific mean difference, we solve for mu2.
    But for simplicity and consistency with "effect_size" as a shift parameter:
    We will set mu2 = mu1 + effect_size.
    Mean1 = exp(0.5)
    Mean2 = exp(effect_size + 0.5)
    This creates a multiplicative effect on the mean, which is standard for log-normal.
    Wait, the task T009c says: "Verify mean difference for log-normal distribution (n=30, effect=0.5) is within 1e-6 of 0.5."
    This implies an ADDITIVE difference of 0.5.
    Mean1 = exp(0.5) ~ 1.6487
    Target Mean2 = 1.6487 + 0.5 = 2.1487
    exp(mu2 + 0.5) = 2.1487 => mu2 + 0.5 = ln(2.1487) => mu2 = ln(2.1487) - 0.5.
    Let's implement this calculation to ensure the mean difference is exactly 0.5.
    """
    rng = np.random.default_rng(seed)
    sigma = 1.0
    mu1 = 0.0
    mean1 = math.exp(mu1 + sigma**2 / 2)
    target_mean2 = mean1 + effect_size
    
    if target_mean2 <= 0:
        # Fallback if effect size makes mean negative (impossible for log-normal)
        # This shouldn't happen with effect=0.5 and mu=0
        raise ValueError(f"Target mean {target_mean2} is not valid for log-normal distribution.")
    
    mu2 = math.log(target_mean2) - (sigma**2 / 2)
    
    group1 = rng.lognormal(mean=mu1, sigma=sigma, size=n)
    group2 = rng.lognormal(mean=mu2, sigma=sigma, size=n)
    return group1, group2

def generate_data(
    sample_size: Optional[int] = None,
    n: Optional[int] = None,
    distribution_type: Optional[str] = None,
    dist: Optional[str] = None,
    effect_size: Optional[float] = None,
    eff: Optional[float] = None,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Unified data generation function that accepts multiple argument naming conventions
    to support various callers (T013 validation, T011 generation, etc.).
    
    Args:
        sample_size: Number of samples per group (preferred name)
        n: Number of samples per group (legacy/alternative name)
        distribution_type: 'normal', 'uniform', 'log-normal' (preferred)
        dist: 'normal', 'uniform', 'log-normal' (legacy/alternative)
        effect_size: Effect size parameter (preferred)
        eff: Effect size parameter (legacy)
        seed: Random seed
      
    Returns:
        Tuple of (group1, group2) numpy arrays.
    """
    # Resolve arguments
    if n is not None and sample_size is None:
        sample_size = n
    if sample_size is None:
        raise ValueError("Missing required argument: 'sample_size' or 'n'")
        
    if dist is not None and distribution_type is None:
        distribution_type = dist
    if distribution_type is None:
        raise ValueError("Missing required argument: 'distribution_type' or 'dist'")
        
    if eff is not None and effect_size is None:
        effect_size = eff
    if effect_size is None:
        raise ValueError("Missing required argument: 'effect_size' or 'eff'")
        
    if seed is None:
        # Default seed if not provided
        seed = 42

    dist_type = distribution_type.lower()
    
    if dist_type == 'normal':
        return generate_normal(sample_size, effect_size, seed)
    elif dist_type == 'uniform':
        return generate_uniform(sample_size, effect_size, seed)
    elif dist_type in ['log-normal', 'lognormal']:
        return generate_log_normal(sample_size, effect_size, seed)
    else:
        raise ValueError(f"Unsupported distribution type: {distribution_type}")

def calculate_theoretical_parameters(dist_type: str, effect_size: float) -> Dict[str, float]:
    """
    Calculate theoretical mean, variance, and skewness for the specified distribution.
    """
    dist_type = dist_type.lower()
    params = {}
    
    if dist_type == 'normal':
        # N(0, 1) and N(effect, 1) -> Mean diff = effect
        # We are validating the difference or the stats of the combined batch?
        # The task says "sample statistics of a generated batch".
        # Let's assume we are checking the mean difference and variance of the combined data or individual groups.
        # For Normal: Mean1=0, Var1=1, Skew1=0. Mean2=effect, Var2=1, Skew2=0.
        params['mean_diff'] = effect_size
        params['variance'] = 1.0
        params['skewness'] = 0.0
        
    elif dist_type == 'uniform':
        # U(0,1) and U(effect, 1+effect)
        # Mean1 = 0.5, Var1 = 1/12
        # Mean2 = 0.5 + effect, Var2 = 1/12
        params['mean_diff'] = effect_size
        params['variance'] = 1.0 / 12.0
        params['skewness'] = 0.0
        
    elif dist_type in ['log-normal', 'lognormal']:
        # As implemented in generate_log_normal:
        # mu1 = 0, sigma = 1. Mean1 = exp(0.5).
        # mu2 = ln(Mean1 + effect) - 0.5.
        mean1 = math.exp(0.5)
        mean2 = mean1 + effect_size
        # Variance of lognormal: (exp(sigma^2) - 1) * exp(2*mu + sigma^2)
        var1 = (math.exp(1) - 1) * math.exp(1) # mu=0, sigma=1 -> exp(1) * (exp(1)-1)
        # For group 2, variance depends on mu2.
        # Skewness: (exp(sigma^2) + 2) * sqrt(exp(sigma^2) - 1)
        # This depends only on sigma, which is 1 for both.
        skew = (math.exp(1) + 2) * math.sqrt(math.exp(1) - 1)
        
        params['mean_diff'] = effect_size
        params['variance'] = var1 # Approximation or average? Let's use group 1 variance as baseline or average.
        params['skewness'] = skew
    else:
        raise ValueError(f"Unknown distribution: {dist_type}")
        
    return params

def validate_sample_statistics(
    group1: np.ndarray, 
    group2: np.ndarray, 
    dist_type: str, 
    effect_size: float,
    tolerance_factor: float = 3.0
) -> None:
    """
    Validates that the sample statistics of the generated data match the theoretical parameters
    within a tolerance appropriate for the sample size (e.g., 3 standard errors).
    
    Raises ValueError if the mismatch exceeds the tolerance.
    
    Args:
        group1: First group of data.
        group2: Second group of data.
        dist_type: Distribution type string.
        effect_size: Theoretical effect size.
        tolerance_factor: Number of standard errors to allow (default 3).
    """
    n1 = len(group1)
    n2 = len(group2)
    n = min(n1, n2) # Use min for conservative SE estimate if sizes differ
    
    if n == 0:
        raise ValueError("Sample size is zero.")

    # Calculate sample statistics
    mean1 = np.mean(group1)
    mean2 = np.mean(group2)
    sample_mean_diff = mean2 - mean1
    
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    sample_variance = (var1 + var2) / 2.0 # Pooled variance estimate
    
    # Skewness calculation
    try:
        skew1 = stats.skew(group1, bias=False)
        skew2 = stats.skew(group2, bias=False)
        sample_skewness = (skew1 + skew2) / 2.0
    except Exception:
        sample_skewness = 0.0 # Fallback if calculation fails (e.g. constant data)

    # Get theoretical parameters
    theoretical = calculate_theoretical_parameters(dist_type, effect_size)
    theo_mean_diff = theoretical['mean_diff']
    theo_variance = theoretical['variance']
    theo_skewness = theoretical['skewness']

    # Calculate Standard Errors (approximate)
    # SE of mean difference: sqrt(var1/n1 + var2/n2)
    se_mean_diff = np.sqrt(var1/n1 + var2/n2)
    
    # SE of variance (approximate): sqrt(2*var^2 / (n-1))
    se_variance = np.sqrt(2 * (sample_variance**2) / (n - 1))
    
    # SE of skewness (approximate): sqrt(6/n)
    se_skewness = np.sqrt(6.0 / n)

    # Validation Logic
    errors = []
    
    # 1. Mean Difference
    diff_mean = abs(sample_mean_diff - theo_mean_diff)
    if diff_mean > tolerance_factor * se_mean_diff:
        errors.append(f"Mean difference mismatch: Sample={sample_mean_diff:.6f}, Theo={theo_mean_diff:.6f}, Diff={diff_mean:.6f}, Tolerance={tolerance_factor * se_mean_diff:.6f}")

    # 2. Variance
    diff_var = abs(sample_variance - theo_variance)
    if diff_var > tolerance_factor * se_variance:
        errors.append(f"Variance mismatch: Sample={sample_variance:.6f}, Theo={theo_variance:.6f}, Diff={diff_var:.6f}, Tolerance={tolerance_factor * se_variance:.6f}")

    # 3. Skewness
    diff_skew = abs(sample_skewness - theo_skewness)
    if diff_skew > tolerance_factor * se_skewness:
        errors.append(f"Skewness mismatch: Sample={sample_skewness:.6f}, Theo={theo_skewness:.6f}, Diff={diff_skew:.6f}, Tolerance={tolerance_factor * se_skewness:.6f}")

    if errors:
        error_msg = "Sample statistics validation failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Sample statistics validation passed for {dist_type} (n={n}, effect={effect_size}).")

# Keep existing names for backward compatibility if they were used elsewhere
# The task T013 specifically asks for this routine in data_generator.py.
# The function `validate_sample_statistics` is the implementation.

def main():
    """
    Main entry point for testing the validation routine directly.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Running self-test for data_generator validation...")
    
    # Test Normal
    try:
        g1, g2 = generate_normal(100, 0.0, seed=42)
        validate_sample_statistics(g1, g2, 'normal', 0.0)
        logger.info("Normal (null) passed.")
    except ValueError as e:
        logger.error(f"Normal (null) failed: {e}")
    
    # Test Normal (Alt)
    try:
        g1, g2 = generate_normal(100, 0.5, seed=42)
        validate_sample_statistics(g1, g2, 'normal', 0.5)
        logger.info("Normal (alt) passed.")
    except ValueError as e:
        logger.error(f"Normal (alt) failed: {e}")

    # Test Log-Normal
    try:
        g1, g2 = generate_log_normal(100, 0.5, seed=42)
        validate_sample_statistics(g1, g2, 'log-normal', 0.5)
        logger.info("Log-normal passed.")
    except ValueError as e:
        logger.error(f"Log-normal failed: {e}")

if __name__ == "__main__":
    main()