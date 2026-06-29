"""
Analysis module for entanglement entropy scaling.

Model selection uses AIC per Plan.md, superseding Spec FR-005 (R²) which is
methodologically incorrect for Area Law detection.

This module provides:
- Model selection via AIC (Constant, Logarithmic, Linear)
- Bootstrap resampling for uncertainty quantification
- Filtering of numerically unresolved realizations
- Visualization utilities (plotting)
"""
import numpy as np
from typing import Tuple, Dict, List, Optional, NamedTuple
from scipy import stats
from scipy.optimize import curve_fit
import warnings
import os
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Ensure plots are saved without displaying
plt.ioff()

# Set a clean style for scientific plots
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['DejaVu Sans']
rcParams['axes.labelsize'] = 10
rcParams['axes.titlesize'] = 10
rcParams['xtick.labelsize'] = 8
rcParams['ytick.labelsize'] = 8
rcParams['legend.fontsize'] = 8
rcParams['figure.figsize'] = (8, 6)
rcParams['figure.dpi'] = 150
rcParams['savefig.dpi'] = 150
rcParams['savefig.bbox'] = 'tight'
rcParams['savefig.pad_inches'] = 0.1

from ground_state import is_numerically_unresolved

class ModelSelectionResult(NamedTuple):
    """Result of model selection via AIC."""
    model_type: str  # 'constant', 'logarithmic', 'linear'
    params: Dict[str, float]
    aic_scores: Dict[str, float]
    selected_aic: float
    r_squared: float
    p_value: Optional[float]
    slope: Optional[float]
    intercept: Optional[float]

def _fit_constant_model(l_vals: np.ndarray, s_vals: np.ndarray) -> Tuple[float, float]:
    """Fit a constant model: S(l) = c."""
    c = np.mean(s_vals)
    # Residual sum of squares
    rss = np.sum((s_vals - c) ** 2)
    # Total sum of squares
    tss = np.sum((s_vals - np.mean(s_vals)) ** 2)
    r_squared = 1 - (rss / tss) if tss > 0 else 0.0
    # p-value for constant model is not meaningful in this context, set to None
    return r_squared, None

def _fit_logarithmic_model(l_vals: np.ndarray, s_vals: np.ndarray) -> Tuple[float, float, float]:
    """Fit a logarithmic model: S(l) = a * log(l) + b."""
    # Avoid log(0)
    valid_mask = l_vals > 0
    if not np.any(valid_mask):
        return 0.0, 0.0, 0.0

    l_valid = l_vals[valid_mask]
    s_valid = s_vals[valid_mask]

    log_l = np.log(l_valid)

    # Linear regression: s = a * log_l + b
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_l, s_valid)

    # Predicted values
    s_pred = slope * log_l + intercept
    rss = np.sum((s_valid - s_pred) ** 2)
    tss = np.sum((s_valid - np.mean(s_valid)) ** 2)
    r_squared = 1 - (rss / tss) if tss > 0 else 0.0

    return r_squared, slope, intercept

def _fit_linear_model(l_vals: np.ndarray, s_vals: np.ndarray) -> Tuple[float, float, float]:
    """Fit a linear model: S(l) = a * l + b."""
    slope, intercept, r_value, p_value, std_err = stats.linregress(l_vals, s_vals)

    s_pred = slope * l_vals + intercept
    rss = np.sum((s_vals - s_pred) ** 2)
    tss = np.sum((s_vals - np.mean(s_vals)) ** 2)
    r_squared = 1 - (rss / tss) if tss > 0 else 0.0

    return r_squared, slope, intercept

def _compute_aic(n: int, rss: float, k: int) -> float:
    """Compute AIC: AIC = n * ln(RSS/n) + 2k."""
    if rss <= 0:
        # Avoid log(0) or log(negative)
        rss = 1e-10
    return n * np.log(rss / n) + 2 * k

def select_model_aic(
    l_vals: np.ndarray,
    s_vals: np.ndarray,
    n_resamples: Optional[int] = None
) -> ModelSelectionResult:
    """
    Select the best model (Constant, Logarithmic, Linear) using AIC.

    Models:
    - Constant (Area Law): S(l) = c, k=1
    - Logarithmic (Critical): S(l) = a*log(l) + b, k=2
    - Linear (Volume Law): S(l) = a*l + b, k=2

    Args:
        l_vals: Array of bipartition lengths.
        s_vals: Array of entanglement entropies.
        n_resamples: Number of data points (n) for AIC calculation. If None, uses len(l_vals).

    Returns:
        ModelSelectionResult with selected model, parameters, and diagnostics.
    """
    n = n_resamples if n_resamples is not None else len(l_vals)

    # Fit constant model
    r2_const, _ = _fit_constant_model(l_vals, s_vals)
    # For constant model, we can compute RSS directly
    c_est = np.mean(s_vals)
    rss_const = np.sum((s_vals - c_est) ** 2)
    aic_const = _compute_aic(n, rss_const, k=1)

    # Fit logarithmic model
    r2_log, slope_log, intercept_log = _fit_logarithmic_model(l_vals, s_vals)
    log_l = np.log(l_vals[l_vals > 0])
    s_log = s_vals[l_vals > 0]
    s_pred_log = slope_log * log_l + intercept_log
    rss_log = np.sum((s_log - s_pred_log) ** 2)
    aic_log = _compute_aic(len(s_log), rss_log, k=2)

    # Fit linear model
    r2_lin, slope_lin, intercept_lin = _fit_linear_model(l_vals, s_vals)
    s_pred_lin = slope_lin * l_vals + intercept_lin
    rss_lin = np.sum((s_vals - s_pred_lin) ** 2)
    aic_lin = _compute_aic(n, rss_lin, k=2)

    aic_scores = {
        'constant': aic_const,
        'logarithmic': aic_log,
        'linear': aic_lin
    }

    selected_model = min(aic_scores, key=aic_scores.get)
    selected_aic = aic_scores[selected_model]

    # Determine parameters and diagnostics based on selected model
    if selected_model == 'constant':
        params = {'c': c_est}
        slope = None
        intercept = None
        p_value = None
        r_squared = r2_const
    elif selected_model == 'logarithmic':
        params = {'slope': slope_log, 'intercept': intercept_log}
        slope = slope_log
        intercept = intercept_log
        # Re-compute p-value for the slope in the log fit
        _, _, _, p_value, _ = stats.linregress(log_l, s_log)
        r_squared = r2_log
    else:  # linear
        params = {'slope': slope_lin, 'intercept': intercept_lin}
        slope = slope_lin
        intercept = intercept_lin
        _, _, _, p_value, _ = stats.linregress(l_vals, s_vals)
        r_squared = r2_lin

    return ModelSelectionResult(
        model_type=selected_model,
        params=params,
        aic_scores=aic_scores,
        selected_aic=selected_aic,
        r_squared=r_squared,
        p_value=p_value,
        slope=slope,
        intercept=intercept
    )

def filter_unresolved_realizations(
    entropy_data: List[Dict]
) -> List[Dict]:
    """
    Filter out realizations marked as numerically unresolved.

    Args:
        entropy_data: List of dictionaries with 'entropy' and 'unresolved' keys.

    Returns:
        Filtered list excluding unresolved realizations.
    """
    return [d for d in entropy_data if not d.get('unresolved', False)]

def bootstrap_resample(
    data: np.ndarray,
    n_resamples: int = 1000,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Perform non-parametric bootstrap resampling.

    Args:
        data: 1D array of data points.
        n_resamples: Number of bootstrap samples.
        random_state: Random seed for reproducibility.

    Returns:
        Array of bootstrap sample means.
    """
    if random_state is not None:
        np.random.seed(random_state)

    n = len(data)
    resample_means = np.zeros(n_resamples)

    for i in range(n_resamples):
        sample = np.random.choice(data, size=n, replace=True)
        resample_means[i] = np.mean(sample)

    return resample_means

def compute_bootstrap_statistics(
    bootstrap_means: np.ndarray,
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Compute statistics from bootstrap distribution.

    Args:
        bootstrap_means: Array of bootstrap sample means.
        confidence_level: Confidence level for interval (e.g., 0.95).

    Returns:
        Dictionary with mean, std_err, ci_lower, ci_upper.
    """
    mean_val = np.mean(bootstrap_means)
    std_err = np.std(bootstrap_means, ddof=1)
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))

    return {
        'mean': mean_val,
        'std_err': std_err,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    }

def compute_scaling_exponent(
    l_vals: np.ndarray,
    s_vals: np.ndarray,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[Dict, ModelSelectionResult]:
    """
    Compute the scaling exponent and its uncertainty via bootstrap.

    Args:
        l_vals: Array of bipartition lengths.
        s_vals: Array of entanglement entropies.
        n_bootstrap: Number of bootstrap resamples.
        random_state: Random seed.

    Returns:
        Tuple of (bootstrap_stats_dict, model_selection_result).
    """
    # Select model
    model_result = select_model_aic(l_vals, s_vals)

    # For bootstrap, we focus on the slope if the model is logarithmic or linear
    if model_result.model_type == 'logarithmic':
        # Bootstrap on the slope of log(l) vs s
        log_l = np.log(l_vals[l_vals > 0])
        s_log = s_vals[l_vals > 0]

        # Perform bootstrap on the slope
        n = len(log_l)
        slope_samples = np.zeros(n_bootstrap)

        if random_state is not None:
            np.random.seed(random_state)

        for i in range(n_bootstrap):
            indices = np.random.choice(n, size=n, replace=True)
            sample_l = log_l[indices]
            sample_s = s_log[indices]
            slope, _, _, _, _ = stats.linregress(sample_l, sample_s)
            slope_samples[i] = slope

        bootstrap_stats = compute_bootstrap_statistics(slope_samples)
        # Override slope in model_result with bootstrap mean
        model_result = model_result._replace(slope=bootstrap_stats['mean'])

    elif model_result.model_type == 'linear':
        # Bootstrap on the slope of l vs s
        n = len(l_vals)
        slope_samples = np.zeros(n_bootstrap)

        if random_state is not None:
            np.random.seed(random_state)

        for i in range(n_bootstrap):
            indices = np.random.choice(n, size=n, replace=True)
            sample_l = l_vals[indices]
            sample_s = s_vals[indices]
            slope, _, _, _, _ = stats.linregress(sample_l, sample_s)
            slope_samples[i] = slope

        bootstrap_stats = compute_bootstrap_statistics(slope_samples)
        model_result = model_result._replace(slope=bootstrap_stats['mean'])

    else:
        # Constant model: bootstrap on the mean
        bootstrap_stats = compute_bootstrap_statistics(bootstrap_resample(s_vals, n_bootstrap, random_state))
        model_result = model_result._replace(slope=None)

    return bootstrap_stats, model_result

def generate_toy_model_data(
    L: int = 10,
    delta: float = 0.5,
    n_realizations: int = 5,
    random_seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate toy model data for visualization.

    This function creates a short chain with random couplings and computes
    the entanglement entropy for each bipartition.

    Args:
        L: Chain length.
        delta: Disorder strength.
        n_realizations: Number of disorder realizations.
        random_seed: Random seed.

    Returns:
        Tuple of (l_vals, s_avg) where s_avg is the average entropy over realizations.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    l_vals = np.arange(1, L)
    s_sum = np.zeros_like(l_vals, dtype=float)

    for _ in range(n_realizations):
        # Generate random couplings
        couplings = np.random.uniform(1 - delta, 1 + delta, size=L - 1)
        # For a toy model, we approximate entropy as proportional to log(l)
        # This is a simplified representation; real computation would use TEBD
        # Here we add some noise to simulate disorder effects
        noise = np.random.normal(0, 0.1, size=len(l_vals))
        s_vals = (np.log(l_vals) / 3.0) * np.mean(couplings) + noise
        s_sum += s_vals

    s_avg = s_sum / n_realizations
    return l_vals, s_avg

def generate_entropy_vs_l_plot(
    l_vals: np.ndarray,
    s_vals: np.ndarray,
    output_path: str,
    model_result: Optional[ModelSelectionResult] = None,
    title: Optional[str] = None,
    xlabel: str = "Bipartition Length $l$",
    ylabel: str = "Entanglement Entropy $S(l)$",
    log_scale: bool = True
) -> None:
    """
    Generate a log-log plot of entanglement entropy vs bipartition length.

    This function creates a plot with the data points and, if available,
    the fitted model line. The plot is saved to the specified output path.

    Args:
        l_vals: Array of bipartition lengths.
        s_vals: Array of entanglement entropies.
        output_path: Path to save the plot (e.g., 'data/entropy_vs_l.png').
        model_result: Optional ModelSelectionResult to plot the fit line.
        title: Optional plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        log_scale: If True, use log-log scale.
    """
    plt.figure()

    # Plot data points
    plt.scatter(l_vals, s_vals, alpha=0.6, label='Data', color='blue', edgecolors='k')

    # Plot fit line if model_result is provided
    if model_result is not None:
        if model_result.model_type == 'logarithmic' and model_result.slope is not None:
            # Fit line: S(l) = slope * log(l) + intercept
            l_fit = np.linspace(min(l_vals), max(l_vals), 100)
            s_fit = model_result.slope * np.log(l_fit) + (model_result.intercept or 0)
            plt.plot(l_fit, s_fit, 'r-', label=f'Log Fit: $S = {model_result.slope:.3f} \\ln l + {model_result.intercept:.3f}$')
        elif model_result.model_type == 'linear' and model_result.slope is not None:
            # Fit line: S(l) = slope * l + intercept
            l_fit = np.linspace(min(l_vals), max(l_vals), 100)
            s_fit = model_result.slope * l_fit + (model_result.intercept or 0)
            plt.plot(l_fit, s_fit, 'r-', label=f'Linear Fit: $S = {model_result.slope:.3f} l + {model_result.intercept:.3f}$')
        elif model_result.model_type == 'constant' and 'c' in model_result.params:
            # Constant line
            c = model_result.params['c']
            plt.axhline(y=c, color='r', linestyle='--', label=f'Constant Fit: $S = {c:.3f}$')

    if log_scale:
        plt.xscale('log')
        plt.yscale('log')

    if title:
        plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.5)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(output_path)
    plt.close()
