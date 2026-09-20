"""
Analysis module for entanglement entropy scaling and model selection.

Model selection uses AIC per Plan.md and FR-005 (amended), superseding original Spec R² requirement.
This module implements the core logic for distinguishing between Area Law, Logarithmic,
and Volume Law scaling behaviors using Akaike Information Criterion (AIC).

Implementation follows Plan's methodological correction (AIC) over Spec's R² requirement.
"""
import numpy as np
from typing import Tuple, Dict, List, Optional, NamedTuple
from scipy import stats
from scipy.optimize import curve_fit
import warnings
import os
from dataclasses import dataclass

# Constants
AIC_LOG_ENTRY = "Model selection uses AIC per Plan.md and FR-005 (amended), superseding original Spec R² requirement."


class ModelSelectionResult(NamedTuple):
    """Result of AIC-based model selection."""
    best_model: str  # 'area_law', 'logarithmic', or 'volume_law'
    aic_scores: Dict[str, float]
    coefficients: Dict[str, Tuple[float, float]]  # model -> (slope, intercept)
    r_squared: Dict[str, float]
    log_entry: str


def _log_aic_deviation():
    """Log the AIC deviation to validation_log.txt."""
    log_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'validation_log.txt')
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"[{np.datetime64('now')}] {AIC_LOG_ENTRY}\n")
    except Exception:
        # Fail silently if logging fails; the core logic remains valid
        pass


def _log_entry():
    """Return the AIC deviation log entry."""
    return AIC_LOG_ENTRY


def _log_aic_selection(delta: float, best_model: str, aic_scores: Dict[str, float]):
    """Log the AIC selection result."""
    log_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'validation_log.txt')
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"[{np.datetime64('now')}] AIC Selection for delta={delta:.4f}: {best_model}\n")
            f.write(f"  AIC Scores: {aic_scores}\n")
    except Exception:
        pass


def _linear_func(x, slope, intercept):
    """Linear function: y = slope * x + intercept."""
    return slope * x + intercept


def _log_func(x, slope, intercept):
    """Logarithmic function: y = slope * log(x) + intercept."""
    # Avoid log(0) by ensuring x > 0
    x_safe = np.maximum(x, 1e-10)
    return slope * np.log(x_safe) + intercept


def _constant_func(x, intercept):
    """Constant function: y = intercept."""
    return np.ones_like(x) * intercept


def _compute_r_squared(y_true, y_pred):
    """Compute R² score."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return 1 - (ss_res / ss_tot)


def _compute_aic(n, rss, k):
    """
    Compute AIC: AIC = 2k - 2ln(L)
    For linear regression with normal errors: -2ln(L) = n*ln(rss/n) + const
    So AIC = 2k + n*ln(rss/n)
    """
    if rss <= 0:
        rss = 1e-10
    return 2 * k + n * np.log(rss / n)


def select_model_aic(
    l_values: np.ndarray,
    entropy_values: np.ndarray,
    log_entry_path: Optional[str] = None
) -> ModelSelectionResult:
    """
    Perform AIC-based model selection to distinguish between Area Law, Logarithmic, and Volume Law.

    Fits three models:
    1. Area Law (Constant): S(l) = c
    2. Logarithmic: S(l) = a * log(l) + b
    3. Volume Law (Linear): S(l) = a * l + b

    Returns the model with the lowest AIC score.

    Args:
        l_values: Array of bipartition lengths (l).
        entropy_values: Array of entanglement entropy values S(l).
        log_entry_path: Optional path to log the AIC deviation message.

    Returns:
        ModelSelectionResult with best model, AIC scores, coefficients, and R² values.
    """
    # Log the AIC deviation if not already logged
    if log_entry_path is None:
        _log_aic_deviation()
    else:
        try:
            with open(log_entry_path, 'a') as f:
                f.write(f"{AIC_LOG_ENTRY}\n")
        except Exception:
            pass

    n = len(l_values)
    if n < 3:
        raise ValueError("At least 3 data points are required for model selection.")

    results = {}
    coefficients = {}
    r_squared = {}

    # Model 1: Area Law (Constant)
    try:
        popt, _ = curve_fit(_constant_func, l_values, entropy_values, p0=[np.mean(entropy_values)])
        y_pred = _constant_func(l_values, *popt)
        rss = np.sum((entropy_values - y_pred) ** 2)
        aic = _compute_aic(n, rss, k=1)  # 1 parameter (intercept)
        r2 = _compute_r_squared(entropy_values, y_pred)
        results['area_law'] = aic
        coefficients['area_law'] = (0.0, popt[0])  # slope=0, intercept
        r_squared['area_law'] = r2
    except Exception as e:
        warnings.warn(f"Area Law fit failed: {e}")
        results['area_law'] = np.inf
        coefficients['area_law'] = (0.0, 0.0)
        r_squared['area_law'] = 0.0

    # Model 2: Logarithmic
    try:
        # Ensure l_values > 0 for log
        l_safe = np.maximum(l_values, 1e-10)
        popt, _ = curve_fit(_log_func, l_safe, entropy_values, p0=[0.5, np.mean(entropy_values)])
        y_pred = _log_func(l_safe, *popt)
        rss = np.sum((entropy_values - y_pred) ** 2)
        aic = _compute_aic(n, rss, k=2)  # 2 parameters (slope, intercept)
        r2 = _compute_r_squared(entropy_values, y_pred)
        results['logarithmic'] = aic
        coefficients['logarithmic'] = (popt[0], popt[1])
        r_squared['logarithmic'] = r2
    except Exception as e:
        warnings.warn(f"Logarithmic fit failed: {e}")
        results['logarithmic'] = np.inf
        coefficients['logarithmic'] = (0.0, 0.0)
        r_squared['logarithmic'] = 0.0

    # Model 3: Volume Law (Linear)
    try:
        popt, _ = curve_fit(_linear_func, l_values, entropy_values, p0=[0.5, np.mean(entropy_values)])
        y_pred = _linear_func(l_values, *popt)
        rss = np.sum((entropy_values - y_pred) ** 2)
        aic = _compute_aic(n, rss, k=2)  # 2 parameters (slope, intercept)
        r2 = _compute_r_squared(entropy_values, y_pred)
        results['volume_law'] = aic
        coefficients['volume_law'] = (popt[0], popt[1])
        r_squared['volume_law'] = r2
    except Exception as e:
        warnings.warn(f"Volume Law fit failed: {e}")
        results['volume_law'] = np.inf
        coefficients['volume_law'] = (0.0, 0.0)
        r_squared['volume_law'] = 0.0

    # Select best model
    best_model = min(results, key=results.get)

    return ModelSelectionResult(
        best_model=best_model,
        aic_scores=results,
        coefficients=coefficients,
        r_squared=r_squared,
        log_entry=AIC_LOG_ENTRY
    )


def filter_unresolved_realizations(
    data: List[Dict[str, any]]
) -> List[Dict[str, any]]:
    """
    Filter out 'numerically unresolved' realizations from the dataset.

    Args:
        data: List of dictionaries containing realization data with 'resolved' key.

    Returns:
        Filtered list with only resolved realizations.
    """
    return [r for r in data if r.get('resolved', True)]


def bootstrap_resample(
    l_values: np.ndarray,
    entropy_values: np.ndarray,
    n_resamples: int = 1000,
    random_seed: Optional[int] = None
) -> List[np.ndarray]:
    """
    Perform non-parametric percentile bootstrap resampling.

    Args:
        l_values: Array of bipartition lengths.
        entropy_values: Array of entanglement entropy values.
        n_resamples: Number of bootstrap resamples.
        random_seed: Random seed for reproducibility.

    Returns:
        List of bootstrapped entropy arrays.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n = len(l_values)
    resamples = []

    for _ in range(n_resamples):
        indices = np.random.choice(n, size=n, replace=True)
        resampled_entropy = entropy_values[indices]
        resamples.append(resampled_entropy)

    return resamples


def compute_bootstrap_statistics(
    l_values: np.ndarray,
    entropy_values: np.ndarray,
    n_resamples: int = 1000,
    random_seed: Optional[int] = None
) -> Dict[str, any]:
    """
    Compute bootstrap statistics for the scaling exponent.

    Args:
        l_values: Array of bipartition lengths.
        entropy_values: Array of entanglement entropy values.
        n_resamples: Number of bootstrap resamples.
        random_seed: Random seed for reproducibility.

    Returns:
        Dictionary containing mean, std, confidence intervals, and p-value.
    """
    resamples = bootstrap_resample(l_values, entropy_values, n_resamples, random_seed)
    slopes = []

    for resampled_entropy in resamples:
        try:
            l_safe = np.maximum(l_values, 1e-10)
            popt, _ = curve_fit(_log_func, l_safe, resampled_entropy, p0=[0.5, np.mean(resampled_entropy)])
            slopes.append(popt[0])
        except Exception:
            slopes.append(0.0)

    slopes = np.array(slopes)
    mean_slope = np.mean(slopes)
    std_slope = np.std(slopes)
    ci_lower = np.percentile(slopes, 2.5)
    ci_upper = np.percentile(slopes, 97.5)

    # Two-sided p-value for testing if slope is significantly different from 0
    t_stat = mean_slope / (std_slope / np.sqrt(len(slopes))) if std_slope > 0 else 0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(slopes) - 1))

    return {
        'mean': mean_slope,
        'std': std_slope,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'p_value': p_value,
        'n_resamples': n_resamples
    }


def compute_scaling_exponent(
    l_values: np.ndarray,
    entropy_values: np.ndarray
) -> Tuple[float, float]:
    """
    Compute the scaling exponent alpha from S(l) ~ l^alpha or S(l) ~ log(l).

    For logarithmic scaling, alpha is the coefficient of log(l).
    For power-law scaling, alpha is the exponent.

    Args:
        l_values: Array of bipartition lengths.
        entropy_values: Array of entanglement entropy values.

    Returns:
        Tuple of (alpha, intercept) for the best-fit model.
    """
    result = select_model_aic(l_values, entropy_values)
    return result.coefficients[result.best_model]


def generate_toy_model_data(
    L: int = 10,
    n_points: int = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate toy model data for verification.

    Args:
        L: Total chain length.
        n_points: Number of bipartition points to evaluate.

    Returns:
        Tuple of (l_values, entropy_values) for the toy model.
    """
    l_values = np.linspace(1, L - 1, n_points)
    # Simulate logarithmic scaling: S(l) = (ln 2)/3 * log(l) + c
    # Using Refael-Moore result for random singlet phase
    entropy_values = (np.log(2) / 3) * np.log(l_values) + 0.5
    return l_values, entropy_values


def generate_entropy_vs_l_plot(
    l_values: np.ndarray,
    entropy_values: np.ndarray,
    output_path: str,
    title: str = "Entanglement Entropy vs Bipartition Length"
):
    """
    Generate a log-log plot of entropy vs l with fit line.

    Args:
        l_values: Array of bipartition lengths.
        entropy_values: Array of entanglement entropy values.
        output_path: Path to save the plot.
        title: Plot title.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    result = select_model_aic(l_values, entropy_values)
    best_model = result.best_model
    coeffs = result.coefficients[best_model]

    plt.figure(figsize=(10, 6))
    plt.scatter(l_values, entropy_values, label='Data', alpha=0.6)

    # Plot fit line
    l_fit = np.linspace(min(l_values), max(l_values), 100)
    if best_model == 'area_law':
        y_fit = np.ones_like(l_fit) * coeffs[1]
        label = f'Area Law (Const): S = {coeffs[1]:.3f}'
    elif best_model == 'logarithmic':
        l_safe = np.maximum(l_fit, 1e-10)
        y_fit = _log_func(l_safe, *coeffs)
        label = f'Logarithmic: S = {coeffs[0]:.3f} log(l) + {coeffs[1]:.3f}'
    else:  # volume_law
        y_fit = _linear_func(l_fit, *coeffs)
        label = f'Volume Law (Linear): S = {coeffs[0]:.3f} l + {coeffs[1]:.3f}'

    plt.plot(l_fit, y_fit, 'r-', label=label)

    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Bipartition Length (l)')
    plt.ylabel('Entanglement Entropy S(l)')
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def verify_scaling_ansatz(
    l_values: np.ndarray,
    entropy_values: np.ndarray
) -> Dict[str, any]:
    """
    Verify the scaling ansatz by comparing AIC scores for different models.

    Implements the "Bartender Test" by explicitly computing ΔAIC.

    Args:
        l_values: Array of bipartition lengths.
        entropy_values: Array of entanglement entropy values.

    Returns:
        Dictionary with AIC scores, ΔAIC, and best model.
    """
    result = select_model_aic(l_values, entropy_values)
    aic_scores = result.aic_scores
    best_model = result.best_model
    min_aic = aic_scores[best_model]

    delta_aic = {model: score - min_aic for model, score in aic_scores.items()}

    # Log the verification
    log_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'validation_log.txt')
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"[{np.datetime64('now')}] Scaling Ansatz Verification:\n")
            f.write(f"  Best Model: {best_model}\n")
            f.write(f"  AIC Scores: {aic_scores}\n")
            f.write(f"  ΔAIC: {delta_aic}\n")
    except Exception:
        pass

    return {
        'best_model': best_model,
        'aic_scores': aic_scores,
        'delta_aic': delta_aic,
        'coefficients': result.coefficients,
        'r_squared': result.r_squared
    }
