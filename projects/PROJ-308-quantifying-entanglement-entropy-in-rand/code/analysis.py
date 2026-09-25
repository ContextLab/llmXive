"""
Entanglement Entropy Analysis Module.

This module provides utilities for analyzing entanglement entropy data,
including model selection (AIC), bootstrap resampling, and plotting.

Model selection uses AIC per Plan.md and FR-005 (amended), superseding
original Spec R² requirement.
"""
import numpy as np
from typing import Tuple, Dict, List, Optional, NamedTuple
from scipy import stats
from scipy.optimize import curve_fit
import warnings
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------
# Data Structures
# --------------------------------------------------------------------------

class ModelSelectionResult(NamedTuple):
    """Result of AIC-based model selection."""
    model_type: str  # 'constant', 'logarithmic', 'linear'
    aic: float
    slope: Optional[float]
    intercept: Optional[float]
    r_squared: float
    p_value: Optional[float]
    stderr: Optional[float]

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def _log_fit(l_vals: np.ndarray, s_vals: np.ndarray) -> Tuple[float, float]:
    """Fit S = a * log(l) + b."""
    # Avoid log(0)
    valid_mask = l_vals > 0
    if not np.any(valid_mask):
        raise ValueError("No valid l values > 0 for log fit.")
    
    l_valid = l_vals[valid_mask]
    s_valid = s_vals[valid_mask]
    
    log_l = np.log(l_valid)
    
    # Linear regression: y = mx + c
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_l, s_valid)
    return slope, intercept

def _linear_fit(l_vals: np.ndarray, s_vals: np.ndarray) -> Tuple[float, float]:
    """Fit S = a * l + b."""
    slope, intercept, r_value, p_value, std_err = stats.linregress(l_vals, s_vals)
    return slope, intercept

def _constant_fit(s_vals: np.ndarray) -> float:
    """Fit S = c (constant)."""
    return np.mean(s_vals)

def _calculate_aic(n: int, rss: float, k: int) -> float:
    """Calculate Akaike Information Criterion."""
    if rss <= 0:
        rss = 1e-10  # Prevent log(0)
    return n * np.log(rss / n) + 2 * k

# --------------------------------------------------------------------------
# Core Analysis Functions
# --------------------------------------------------------------------------

def select_model_aic(
    l_vals: np.ndarray,
    s_vals: np.ndarray,
    log_path: Optional[str] = None
) -> ModelSelectionResult:
    """
    Select the best model (Constant, Logarithmic, Linear) using AIC.
    
    Models:
      - Constant: S = c (Area Law)
      - Logarithmic: S = a * log(l) + b (Critical/Random Singlet)
      - Linear: S = a * l + b (Volume Law)
    
    Args:
        l_vals: Array of bipartition lengths l.
        s_vals: Array of entropy values S(l).
        log_path: Optional path to write validation log.
        
    Returns:
        ModelSelectionResult named tuple.
    """
    n = len(l_vals)
    valid_mask = l_vals > 0
    l_valid = l_vals[valid_mask]
    s_valid = s_vals[valid_mask]
    n_valid = len(s_valid)
    
    if n_valid < 2:
        raise ValueError("Need at least 2 valid data points for model selection.")
    
    results = {}
    
    # 1. Constant Model (k=1: intercept)
    c_val = _constant_fit(s_valid)
    rss_const = np.sum((s_valid - c_val)**2)
    aic_const = _calculate_aic(n_valid, rss_const, k=1)
    results['constant'] = {'aic': aic_const, 'slope': None, 'intercept': c_val, 'k': 1}
    
    # 2. Logarithmic Model (k=2: slope, intercept)
    try:
        m_log, c_log = _log_fit(l_valid, s_valid)
        s_pred_log = m_log * np.log(l_valid) + c_log
        rss_log = np.sum((s_valid - s_pred_log)**2)
        aic_log = _calculate_aic(n_valid, rss_log, k=2)
        # Calculate R-squared and p-value for slope
        slope, intercept, r_val, p_val, std_err = stats.linregress(np.log(l_valid), s_valid)
        results['logarithmic'] = {
            'aic': aic_log, 
            'slope': slope, 
            'intercept': intercept, 
            'r_squared': r_val**2,
            'p_value': p_val,
            'stderr': std_err,
            'k': 2
        }
    except Exception as e:
        warnings.warn(f"Logarithmic fit failed: {e}")
        results['logarithmic'] = {'aic': np.inf, 'slope': None, 'intercept': None, 'k': 2}

    # 3. Linear Model (k=2: slope, intercept)
    try:
        m_lin, c_lin = _linear_fit(l_valid, s_valid)
        s_pred_lin = m_lin * l_valid + c_lin
        rss_lin = np.sum((s_valid - s_pred_lin)**2)
        aic_lin = _calculate_aic(n_valid, rss_lin, k=2)
        # Calculate R-squared and p-value
        slope, intercept, r_val, p_val, std_err = stats.linregress(l_valid, s_valid)
        results['linear'] = {
            'aic': aic_lin, 
            'slope': slope, 
            'intercept': intercept, 
            'r_squared': r_val**2,
            'p_value': p_val,
            'stderr': std_err,
            'k': 2
        }
    except Exception as e:
        warnings.warn(f"Linear fit failed: {e}")
        results['linear'] = {'aic': np.inf, 'slope': None, 'intercept': None, 'k': 2}

    # Select best model
    best_model_name = min(results, key=lambda x: results[x]['aic'])
    best = results[best_model_name]
    
    # Construct return object
    if best_model_name == 'constant':
        return ModelSelectionResult(
            model_type='constant',
            aic=best['aic'],
            slope=0.0,
            intercept=best['intercept'],
            r_squared=0.0, # R^2 not meaningful for constant vs variable in this context
            p_value=None,
            stderr=None
        )
    else:
        return ModelSelectionResult(
            model_type=best_model_name,
            aic=best['aic'],
            slope=best['slope'],
            intercept=best['intercept'],
            r_squared=best['r_squared'],
            p_value=best['p_value'],
            stderr=best['stderr']
        )

def filter_unresolved_realizations(
    data: List[Dict],
    unresolved_ids: set
) -> List[Dict]:
    """
    Filter out realizations marked as 'numerically unresolved'.
    
    Args:
        data: List of realization dictionaries.
        unresolved_ids: Set of realization IDs to exclude.
        
    Returns:
        Filtered list of dictionaries.
    """
    return [d for d in data if d.get('realization_id') not in unresolved_ids]

def bootstrap_resample(
    l_vals: np.ndarray,
    s_vals: np.ndarray,
    n_resamples: int = 1000,
    random_seed: Optional[int] = None
) -> np.ndarray:
    """
    Perform non-parametric percentile bootstrap resampling.
    
    Args:
        l_vals: Array of lengths.
        s_vals: Array of entropy values.
        n_resamples: Number of bootstrap samples.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Array of bootstrap slope estimates.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    n = len(l_vals)
    slopes = []
    
    for _ in range(n_resamples):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        l_boot = l_vals[indices]
        s_boot = s_vals[indices]
        
        # Sort by l to ensure monotonicity for fitting (optional but good practice)
        sort_idx = np.argsort(l_boot)
        l_boot = l_boot[sort_idx]
        s_boot = s_boot[sort_idx]
        
        try:
            slope, _, _, _, _ = stats.linregress(np.log(l_boot), s_boot)
            slopes.append(slope)
        except Exception:
            continue
            
    return np.array(slopes)

def compute_bootstrap_statistics(
    slopes: np.ndarray,
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Compute standard error and confidence intervals from bootstrap slopes.
    
    Args:
        slopes: Array of bootstrap slope estimates.
        alpha: Significance level (default 0.05 for 95% CI).
        
    Returns:
        Dictionary with 'mean', 'std_err', 'ci_lower', 'ci_upper', 'p_value'.
    """
    if len(slopes) == 0:
        raise ValueError("No valid bootstrap slopes computed.")
        
    mean_slope = np.mean(slopes)
    std_err = np.std(slopes, ddof=1)
    
    ci_lower = np.percentile(slopes, 100 * alpha / 2)
    ci_upper = np.percentile(slopes, 100 * (1 - alpha / 2))
    
    # Two-sided p-value (test against 0)
    # Assuming normal approximation for p-value
    t_stat = mean_slope / std_err if std_err > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(t_stat)))
    
    return {
        'mean': mean_slope,
        'std_err': std_err,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'p_value': p_value
    }

def compute_scaling_exponent(
    l_vals: np.ndarray,
    s_vals: np.ndarray,
    n_resamples: int = 1000,
    random_seed: Optional[int] = None
) -> Dict[str, any]:
    """
    Compute scaling exponent alpha via bootstrap.
    
    Args:
        l_vals: Array of lengths.
        s_vals: Array of entropy values.
        n_resamples: Bootstrap resamples.
        random_seed: Random seed.
        
    Returns:
        Dictionary with exponent, CI, p-value, etc.
    """
    # Initial fit
    model = select_model_aic(l_vals, s_vals)
    
    if model.model_type == 'constant':
        return {
            'alpha': 0.0,
            'std_err': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'p_value': 1.0,
            'model_type': 'constant'
        }
    
    # Bootstrap
    slopes = bootstrap_resample(l_vals, s_vals, n_resamples, random_seed)
    stats_dict = compute_bootstrap_statistics(slopes)
    
    return {
        'alpha': stats_dict['mean'],
        'std_err': stats_dict['std_err'],
        'ci_lower': stats_dict['ci_lower'],
        'ci_upper': stats_dict['ci_upper'],
        'p_value': stats_dict['p_value'],
        'model_type': model.model_type
    }

def generate_toy_model_data(L: int = 10, n_realizations: int = 5, seed: int = 42) -> List[Dict]:
    """
    Generate toy model data for verification (Feynman review).
    Uses random couplings to simulate entropy scaling.
    
    Args:
        L: Chain length.
        n_realizations: Number of realizations.
        seed: Random seed.
        
    Returns:
        List of dicts with l, S(l) for various l.
    """
    np.random.seed(seed)
    data = []
    
    # Simulate Refael-Moore scaling: S ~ (ln 2)/3 * log(l)
    # Add some noise
    for r_id in range(n_realizations):
        for l in range(2, L + 1):
            # Theoretical value
            s_theory = (np.log(2) / 3) * np.log(l)
            # Add noise
            noise = np.random.normal(0, 0.1)
            s_val = s_theory + noise
            data.append({
                'realization_id': r_id,
                'l': l,
                'entropy': s_val
            })
            
    return data

def generate_entropy_vs_l_plot(
    data: List[Dict],
    output_path: str,
    title: str = "Entanglement Entropy vs. Bipartition Length",
    log_scale: bool = True
) -> None:
    """
    Generate a log-log plot of Entropy S(l) vs. length l with a fit line.
    
    This function aggregates data from multiple realizations, computes the mean
    entropy for each l, fits a logarithmic model, and plots the result.
    
    Args:
        data: List of dictionaries containing 'l' and 'entropy' keys.
        output_path: Path to save the plot (e.g., 'data/entropy_vs_l.png').
        title: Plot title.
        log_scale: If True, use log-log scale.
    """
    if not data:
        raise ValueError("No data provided for plotting.")
        
    # Aggregate data by l
    l_vals = sorted(list(set(d['l'] for d in data)))
    mean_s = []
    std_s = []
    
    for l in l_vals:
        subset = [d['entropy'] for d in data if d['l'] == l]
        mean_s.append(np.mean(subset))
        std_s.append(np.std(subset) if len(subset) > 1 else 0)
        
    l_arr = np.array(l_vals)
    s_arr = np.array(mean_s)
    s_err = np.array(std_s)
    
    # Filter valid l for fitting
    valid_mask = l_arr > 0
    l_fit = l_arr[valid_mask]
    s_fit = s_arr[valid_mask]
    
    # Fit logarithmic model: S = a * log(l) + b
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(np.log(l_fit), s_fit)
        fit_line = slope * np.log(l_fit) + intercept
        has_fit = True
    except Exception as e:
        warnings.warn(f"Fit failed: {e}. Plotting data only.")
        has_fit = False
        
    # Create plot
    plt.figure(figsize=(10, 6))
    
    # Scatter plot with error bars
    plt.errorbar(l_fit, s_fit, yerr=s_err[valid_mask], fmt='o', capsize=5, 
                 label='Simulation Data', color='blue', alpha=0.7)
    
    # Fit line
    if has_fit:
        plt.plot(l_fit, fit_line, 'r--', label=f'Log Fit: S = {slope:.3f} log(l) + {intercept:.3f}')
        
        # Annotate slope (alpha)
        plt.text(0.05, 0.95, f'$\\alpha$ = {slope:.3f}', 
                 transform=plt.gca().transAxes, 
                 fontsize=12, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.xlabel('Bipartition Length (l)', fontsize=12)
    plt.ylabel('Entanglement Entropy S(l)', fontsize=12)
    plt.title(title, fontsize=14)
    
    if log_scale:
        plt.xscale('log')
        plt.yscale('log')
        
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    # Log the action
    print(f"Plot saved to {output_path}")

def verify_scaling_ansatz(
    l_vals: np.ndarray,
    s_vals: np.ndarray,
    log_path: str = "validation_log.txt"
) -> Dict[str, float]:
    """
    Explicitly verify the Refael-Moore scaling ansatz.
    Compares Logarithmic vs Constant model AIC.
    
    Args:
        l_vals: Lengths.
        s_vals: Entropies.
        log_path: Path to log file.
        
    Returns:
        Dictionary with AIC values and delta AIC.
    """
    # Re-use select_model_aic logic but return detailed AICs
    n = len(l_vals)
    valid_mask = l_vals > 0
    l_valid = l_vals[valid_mask]
    s_valid = s_vals[valid_mask]
    n_valid = len(s_valid)
    
    # Constant
    c_val = np.mean(s_valid)
    rss_const = np.sum((s_valid - c_val)**2)
    aic_const = n_valid * np.log(rss_const / n_valid) + 2 * 1
    
    # Logarithmic
    try:
        m_log, c_log = _log_fit(l_valid, s_valid)
        s_pred_log = m_log * np.log(l_valid) + c_log
        rss_log = np.sum((s_valid - s_pred_log)**2)
        aic_log = n_valid * np.log(rss_log / n_valid) + 2 * 2
    except Exception:
        aic_log = np.inf
        
    delta_aic = aic_const - aic_log
    
    with open(log_path, 'a') as f:
        f.write(f"Scaling Ansatz Verification:\n")
        f.write(f"  AIC(Constant): {aic_const:.4f}\n")
        f.write(f"  AIC(Logarithmic): {aic_log:.4f}\n")
        f.write(f"  Delta AIC (Const - Log): {delta_aic:.4f}\n")
        if delta_aic > 2:
            f.write("  Result: Logarithmic model strongly preferred (Refael-Moore).\n")
        elif delta_aic < -2:
            f.write("  Result: Constant model preferred (Area Law).\n")
        else:
            f.write("  Result: Models are indistinguishable.\n")
        f.write("-" * 40 + "\n")
        
    return {
        'aic_constant': aic_const,
        'aic_logarithmic': aic_log,
        'delta_aic': delta_aic
    }
