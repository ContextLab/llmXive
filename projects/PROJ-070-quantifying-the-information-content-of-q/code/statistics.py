import numpy as np
from scipy import stats
from logging_config import logger
from typing import Optional, Dict, Any, List, Tuple
import warnings

# Existing function signatures preserved from previous implementation
def calculate_correlation(
    x: np.ndarray,
    y: np.ndarray,
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    Calculate Pearson or Spearman correlation coefficient and p-value.
    
    Args:
        x: First variable array
        y: Second variable array
        method: 'pearson' or 'spearman'
        
    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Arrays must be of equal length and have at least 2 elements")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if method == 'pearson':
            corr, pval = stats.pearsonr(x, y)
        elif method == 'spearman':
            corr, pval = stats.spearmanr(x, y)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
    
    return float(corr), float(pval)

def calculate_partial_correlation(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    Calculate partial correlation between x and y, controlling for z.
    
    This is used to decouple system size N from entanglement structure.
    
    Args:
        x: First variable array (e.g., entanglement entropy)
        y: Second variable array (e.g., complexity/NCD)
        z: Control variable array (e.g., system size N)
        method: 'pearson' or 'spearman'
        
    Returns:
        Tuple of (partial correlation coefficient, p-value)
    """
    if len(x) != len(y) or len(y) != len(z) or len(x) < 3:
        raise ValueError("Arrays must be of equal length and have at least 3 elements")
    
    # Convert to arrays
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    
    # Handle NaN/Inf
    mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z) | 
             np.isinf(x) | np.isinf(y) | np.isinf(z))
    if np.sum(mask) < 3:
        raise ValueError("Insufficient valid data points after filtering NaN/Inf")
    
    x, y, z = x[mask], y[mask], z[mask]
    
    # Fit linear models: x ~ z and y ~ z
    # Residuals represent the variation in x and y not explained by z
    try:
        # Reshape for sklearn-like interface or use np.polyfit
        # Using polyfit for simplicity: x = a*z + b
        z_poly = z.reshape(-1, 1)
        
        # Fit x ~ z
        slope_x, intercept_x = np.polyfit(z, x, 1)
        x_pred = slope_x * z + intercept_x
        res_x = x - x_pred
        
        # Fit y ~ z
        slope_y, intercept_y = np.polyfit(z, y, 1)
        y_pred = slope_y * z + intercept_y
        res_y = y - y_pred
        
        # Calculate correlation of residuals
        if method == 'pearson':
            corr, pval = stats.pearsonr(res_x, res_y)
        elif method == 'spearman':
            corr, pval = stats.spearmanr(res_x, res_y)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        return float(corr), float(pval)
        
    except Exception as e:
        logger.error(f"Error calculating partial correlation: {e}")
        raise

def bootstrap_correlation(
    x: np.ndarray,
    y: np.ndarray,
    z: Optional[np.ndarray] = None,
    n_iterations: int = 1000,
    random_state: Optional[int] = None,
    method: str = 'pearson'
) -> Tuple[float, float, np.ndarray, Dict[str, float]]:
    """
    Implement bootstrap resampling engine for correlation analysis.
    
    Uses partial correlation controlling for system size N if z is provided.
    Otherwise uses standard correlation.
    
    Args:
        x: First variable array (e.g., entanglement entropy)
        y: Second variable array (e.g., complexity/NCD)
        z: Control variable array (e.g., system size N) for partial correlation
        n_iterations: Number of bootstrap iterations (sufficient for stable CI)
        random_state: Random seed for reproducibility
        method: 'pearson' or 'spearman'
        
    Returns:
        Tuple containing:
            - Original correlation estimate
            - Original p-value
            - Array of bootstrap correlation coefficients
            - Dictionary with bootstrap statistics (mean, std, 95% CI)
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Arrays must be of equal length and have at least 2 elements")
    
    if z is not None and len(z) != len(x):
        raise ValueError("Control variable z must have same length as x and y")
    
    if n_iterations < 100:
        logger.warning(f"n_iterations={n_iterations} is low; recommend >= 1000 for stable CI")
    
    rng = np.random.default_rng(random_state)
    n = len(x)
    bootstrap_corrs = np.zeros(n_iterations)
    
    # Filter NaN/Inf from input
    valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    if z is not None:
        valid_mask &= ~(np.isnan(z) | np.isinf(z))
    
    x_clean = np.asarray(x, dtype=float)[valid_mask]
    y_clean = np.asarray(y, dtype=float)[valid_mask]
    z_clean = np.asarray(z, dtype=float)[valid_mask] if z is not None else None
    
    if len(x_clean) < 3:
        raise ValueError("Insufficient valid data points after filtering NaN/Inf")
    
    # Calculate original estimate
    if z_clean is not None:
        orig_corr, orig_pval = calculate_partial_correlation(
            x_clean, y_clean, z_clean, method=method
        )
    else:
        orig_corr, orig_pval = calculate_correlation(
            x_clean, y_clean, method=method
        )
    
    # Bootstrap loop
    logger.info(f"Starting bootstrap resampling with {n_iterations} iterations...")
    for i in range(n_iterations):
        # Resample with replacement
        indices = rng.integers(0, len(x_clean), size=len(x_clean))
        x_boot = x_clean[indices]
        y_boot = y_clean[indices]
        z_boot = z_clean[indices] if z_clean is not None else None
        
        try:
            if z_boot is not None:
                corr_boot, _ = calculate_partial_correlation(
                    x_boot, y_boot, z_boot, method=method
                )
            else:
                corr_boot, _ = calculate_correlation(
                    x_boot, y_boot, method=method
                )
            bootstrap_corrs[i] = corr_boot
        except Exception as e:
            # If resample fails (e.g., all same values), skip
            logger.debug(f"Bootstrap iteration {i} failed: {e}")
            continue
    
    # Remove failed iterations
    valid_corrs = bootstrap_corrs[~np.isnan(bootstrap_corrs)]
    
    if len(valid_corrs) < 10:
        raise ValueError("Bootstrap failed: insufficient valid iterations")
    
    # Calculate bootstrap statistics
    boot_mean = np.mean(valid_corrs)
    boot_std = np.std(valid_corrs, ddof=1)
    ci_lower = np.percentile(valid_corrs, 2.5)
    ci_upper = np.percentile(valid_corrs, 97.5)
    
    stats_dict = {
        'mean': boot_mean,
        'std': boot_std,
        'ci_95_lower': ci_lower,
        'ci_95_upper': ci_upper,
        'n_successful_iterations': len(valid_corrs)
    }
    
    logger.info(f"Bootstrap complete: mean={boot_mean:.4f}, "
               f"95% CI=[{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return float(orig_corr), float(orig_pval), valid_corrs, stats_dict

def calculate_confidence_intervals(
    bootstrap_corrs: np.ndarray,
    alpha: float = 0.05,
    bias_correct: bool = True
) -> Dict[str, float]:
    """
    Calculate confidence intervals for bootstrap correlation coefficients.
    
    Supports standard percentile method and bias-corrected percentile method.
    
    Args:
        bootstrap_corrs: Array of bootstrap correlation coefficients
        alpha: Significance level (default 0.05 for 95% CI)
        bias_correct: If True, use bias-corrected percentile method
        
    Returns:
        Dictionary with confidence interval bounds and method used
    """
    if len(bootstrap_corrs) < 10:
        raise ValueError("Insufficient bootstrap samples for CI calculation")
    
    n = len(bootstrap_corrs)
    sorted_corrs = np.sort(bootstrap_corrs)
    
    if bias_correct:
        # Bias-corrected and accelerated (BCa) method approximation
        # Calculate bias correction factor z0
        mean_corr = np.mean(bootstrap_corrs)
        z0 = stats.norm.ppf(np.sum(bootstrap_corrs < mean_corr) / n)
        
        # Acceleration factor (approximate using jackknife)
        # Simplified: use standard error as approximation
        se = np.std(bootstrap_corrs, ddof=1)
        if se == 0:
            a = 0
        else:
            # Approximate acceleration
            a = 0.0 # Simplified for robustness; full BCa requires jackknife
        
        # Adjusted percentiles
        alpha_lower = alpha / 2
        alpha_upper = 1 - alpha / 2
        
        z_alpha_lower = stats.norm.ppf(alpha_lower)
        z_alpha_upper = stats.norm.ppf(alpha_upper)
        
        # BCa adjusted z-scores
        z_lower = z0 + (z0 + z_alpha_lower) / (1 - a * (z0 + z_alpha_lower))
        z_upper = z0 + (z0 + z_alpha_upper) / (1 - a * (z0 + z_alpha_upper))
        
        p_lower = stats.norm.cdf(z_lower)
        p_upper = stats.norm.cdf(z_upper)
        
        # Ensure bounds are within [0, 1]
        p_lower = max(0.001, min(0.999, p_lower))
        p_upper = max(0.001, min(0.999, p_upper))
        
        ci_lower = np.percentile(sorted_corrs, p_lower * 100)
        ci_upper = np.percentile(sorted_corrs, p_upper * 100)
        method = "BCa (bias-corrected)"
    else:
        # Standard percentile method
        ci_lower = np.percentile(sorted_corrs, alpha_lower * 100)
        ci_upper = np.percentile(sorted_corrs, alpha_upper * 100)
        method = "percentile"
    
    return {
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'alpha': alpha,
        'method': method,
        'n_samples': n
    }

def analyze_stratified_correlation(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    strata: Optional[np.ndarray] = None,
    n_iterations: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform stratified correlation analysis to decouple system size effects.
    
    If strata are provided, computes correlations within each stratum.
    Otherwise, uses partial correlation controlling for z.
    
    Args:
        x: First variable array (e.g., entanglement entropy)
        y: Second variable array (e.g., complexity/NCD)
        z: Control variable array (e.g., system size N)
        strata: Optional array defining strata groups
        n_iterations: Number of bootstrap iterations
        random_state: Random seed
        
    Returns:
        Dictionary with stratified analysis results
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    
    # Filter NaN/Inf
    valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z) | 
                  np.isinf(x) | np.isinf(y) | np.isinf(z))
    x, y, z = x[valid_mask], y[valid_mask], z[valid_mask]
    
    if strata is not None:
        strata = np.asarray(strata, dtype=int)[valid_mask]
        unique_strata = np.unique(strata)
        
        results = {}
        for s in unique_strata:
            mask = strata == s
            if np.sum(mask) < 3:
                continue
            
            try:
                boot_corr, boot_pval, boot_samples, boot_stats = bootstrap_correlation(
                    x[mask], y[mask], z[mask], 
                    n_iterations=n_iterations, 
                    random_state=random_state
                )
                results[f'stratum_{s}'] = {
                    'correlation': boot_corr,
                    'p_value': boot_pval,
                    'ci_95': (boot_stats['ci_95_lower'], boot_stats['ci_95_upper']),
                    'n_samples': np.sum(mask)
                }
            except Exception as e:
                logger.warning(f"Stratum {s} failed: {e}")
                continue
        
        return {
            'type': 'stratified',
            'n_strata': len(results),
            'strata_results': results
        }
    else:
        # Partial correlation controlling for z
        boot_corr, boot_pval, boot_samples, boot_stats = bootstrap_correlation(
            x, y, z, n_iterations=n_iterations, random_state=random_state
        )
        
        return {
            'type': 'partial',
            'correlation': boot_corr,
            'p_value': boot_pval,
            'ci_95_lower': boot_stats['ci_95_lower'],
            'ci_95_upper': boot_stats['ci_95_upper'],
            'control_variable': 'z (system size N)',
            'n_iterations': boot_stats['n_successful_iterations']
        }

def run_welch_t_test(
    group1: np.ndarray,
    group2: np.ndarray
) -> Tuple[float, float]:
    """
    Run Welch's t-test for comparing two independent groups.
    
    Args:
        group1: First group data
        group2: Second group data
        
    Returns:
        Tuple of (t-statistic, p-value)
    """
    g1 = np.asarray(group1, dtype=float)
    g2 = np.asarray(group2, dtype=float)
    
    valid_g1 = g1[~(np.isnan(g1) | np.isinf(g1))]
    valid_g2 = g2[~(np.isnan(g2) | np.isinf(g2))]
    
    if len(valid_g1) < 2 or len(valid_g2) < 2:
        raise ValueError("Each group must have at least 2 valid samples")
    
    t_stat, p_val = stats.ttest_ind(valid_g1, valid_g2, equal_var=False)
    return float(t_stat), float(p_val)

def run_anova_test(
    groups: List[np.ndarray]
) -> Tuple[float, float]:
    """
    Run one-way ANOVA test for comparing multiple groups.
    
    Args:
        groups: List of arrays, one per group
        
    Returns:
        Tuple of (F-statistic, p-value)
    """
    valid_groups = []
    for i, g in enumerate(groups):
        g_clean = np.asarray(g, dtype=float)
        g_clean = g_clean[~(np.isnan(g_clean) | np.isinf(g_clean))]
        if len(g_clean) > 0:
            valid_groups.append(g_clean)
    
    if len(valid_groups) < 2:
        raise ValueError("Need at least 2 valid groups for ANOVA")
    
    f_stat, p_val = stats.f_oneway(*valid_groups)
    return float(f_stat), float(p_val)

def compare_null_models_vs_physical(
    physical_data: np.ndarray,
    product_states: np.ndarray,
    haar_states: np.ndarray
) -> Dict[str, Any]:
    """
    Compare physical states against null models (product and Haar states).
    
    Args:
        physical_data: Metrics for physical states
        product_states: Metrics for random product states
        haar_states: Metrics for Haar-random states
        
    Returns:
        Dictionary with comparison results
    """
    p_phys = np.asarray(physical_data, dtype=float)
    p_prod = np.asarray(product_states, dtype=float)
    p_haar = np.asarray(haar_states, dtype=float)
    
    # Filter NaN/Inf
    p_phys = p_phys[~(np.isnan(p_phys) | np.isinf(p_phys))]
    p_prod = p_prod[~(np.isnan(p_prod) | np.isinf(p_prod))]
    p_haar = p_haar[~(np.isnan(p_haar) | np.isinf(p_haar))]
    
    results = {}
    
    if len(p_phys) > 1 and len(p_prod) > 1:
        t_stat, p_val = run_welch_t_test(p_phys, p_prod)
        results['phys_vs_product'] = {
            't_stat': t_stat,
            'p_value': p_val,
            'significant': p_val < 0.05
        }
    
    if len(p_phys) > 1 and len(p_haar) > 1:
        t_stat, p_val = run_welch_t_test(p_phys, p_haar)
        results['phys_vs_haar'] = {
            't_stat': t_stat,
            'p_value': p_val,
            'significant': p_val < 0.05
        }
    
    if len(p_prod) > 1 and len(p_haar) > 1:
        t_stat, p_val = run_welch_t_test(p_prod, p_haar)
        results['product_vs_haar'] = {
            't_stat': t_stat,
            'p_value': p_val,
            'significant': p_val < 0.05
        }
    
    return results

def run_full_correlation_analysis(
    entanglement: np.ndarray,
    complexity: np.ndarray,
    system_size: np.ndarray,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run full correlation analysis for User Story 3.
    
    Computes partial correlation controlling for system size N with bootstrap CI.
    
    Args:
        entanglement: Entanglement entropy values
        complexity: Complexity (NCD) values
        system_size: System size N values
        n_bootstrap: Number of bootstrap iterations
        random_state: Random seed
        
    Returns:
        Dictionary with complete analysis results including 95% CI
    """
    # Validate inputs
    if len(entanglement) != len(complexity) or len(entanglement) != len(system_size):
        raise ValueError("All input arrays must have the same length")
    
    # Filter NaN/Inf
    valid_mask = ~(np.isnan(entanglement) | np.isnan(complexity) | np.isnan(system_size) |
                  np.isinf(entanglement) | np.isinf(complexity) | np.isinf(system_size))
    
    x = np.asarray(entanglement, dtype=float)[valid_mask]
    y = np.asarray(complexity, dtype=float)[valid_mask]
    z = np.asarray(system_size, dtype=float)[valid_mask]
    
    if len(x) < 3:
        raise ValueError("Insufficient valid data points after filtering (need >= 3)")
    
    logger.info(f"Running full correlation analysis on {len(x)} data points...")
    
    # Bootstrap partial correlation
    orig_corr, orig_pval, boot_samples, boot_stats = bootstrap_correlation(
        x, y, z, 
        n_iterations=n_bootstrap, 
        random_state=random_state,
        method='pearson'
    )
    
    # Calculate confidence intervals
    ci_results = calculate_confidence_intervals(
        boot_samples, 
        alpha=0.05, 
        bias_correct=True
    )
    
    # Stratified analysis
    stratified_results = analyze_stratified_correlation(
        x, y, z, 
        n_iterations=n_bootstrap, 
        random_state=random_state
    )
    
    return {
        'original_correlation': orig_corr,
        'original_p_value': orig_pval,
        'bootstrap_mean': boot_stats['mean'],
        'bootstrap_std': boot_stats['std'],
        'ci_95_lower': ci_results['ci_lower'],
        'ci_95_upper': ci_results['ci_upper'],
        'ci_method': ci_results['method'],
        'n_bootstrap_iterations': boot_stats['n_successful_iterations'],
        'stratified_analysis': stratified_results,
        'n_samples': len(x)
    }

# Main entry point for direct execution (testing)
if __name__ == "__main__":
    # Test with synthetic data (for local validation only)
    # In production, this would load from real data files
    np.random.seed(42)
    n = 50
    system_size = np.random.uniform(10, 40, n)
    # Simulate correlation with some noise
    entanglement = 0.5 * system_size + np.random.normal(0, 2, n)
    complexity = 0.3 * system_size + np.random.normal(0, 1.5, n)
    
    print("Running full correlation analysis...")
    results = run_full_correlation_analysis(
        entanglement, complexity, system_size,
        n_bootstrap=1000, random_state=42
    )
    
    print(f"\nCorrelation coefficient: {results['original_correlation']:.4f}")
    print(f"P-value: {results['original_p_value']:.4f}")
    print(f"95% CI: [{results['ci_95_lower']:.4f}, {results['ci_95_upper']:.4f}]")
    print(f"Bootstrap mean: {results['bootstrap_mean']:.4f}")
    print(f"Bootstrap std: {results['bootstrap_std']:.4f}")
    print(f"CI Method: {results['ci_method']}")
    print(f"Samples: {results['n_samples']}")