"""Scaling analysis for agent counts.

Implements power-law fitting for specialization index and retrieval efficiency
versus agent count, using log-log regression on REAL measured data.
"""
from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: y = a * x^b

    Args:
        x: Independent variable values (agent counts).
        a: Prefactor coefficient.
        b: Exponent coefficient.

    Returns:
        Predicted y values.
    """
    return a * np.power(x, b)


def fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Fit a power law to data using log-log linear regression.

    Fits y = a * x^b by transforming to log(y) = log(a) + b * log(x).

    Args:
        x: Independent variable (agent counts).
        y: Dependent variable (metric values).

    Returns:
        Tuple (a, b) of fitted coefficients.
    """
    # Avoid log(0) or negative values
    mask = (x > 0) & (y > 0)
    if np.sum(mask) < 2:
        logger.log("fit_power_law_warning", message="Insufficient positive data points, returning defaults")
        return 1.0, 0.0

    log_x = np.log(x[mask])
    log_y = np.log(y[mask])

    # Linear regression: log_y = intercept + slope * log_x
    # np.polyfit returns [slope, intercept] for degree 1
    slope, intercept = np.polyfit(log_x, log_y, 1)
    a = np.exp(intercept)
    b = slope

    return float(a), float(b)


def fit_power_law_with_ci(
    x: np.ndarray, y: np.ndarray, confidence: float = 0.95
) -> Tuple[float, float, float]:
    """Fit power law and return exponent with approximate confidence interval.

    Uses bootstrap resampling to estimate the standard error of the exponent,
    then constructs a confidence interval assuming normality.

    Args:
        x: Independent variable (agent counts).
        y: Dependent variable (metric values).
        confidence: Confidence level (e.g., 0.95 for 95% CI).

    Returns:
        Tuple (a, b, ci_half_width) where ci_half_width is the half-width
        of the confidence interval for the exponent b.
    """
    a, b = fit_power_law(x, y)

    if len(x) < 3:
        # Cannot reliably bootstrap with too few points
        logger.log("fit_power_law_ci_warning", message="Too few points for CI, returning large default")
        return a, b, 0.5 * abs(b) if b != 0 else 0.5

    # Bootstrap resampling
    n_bootstrap = 1000
    rng = np.random.default_rng(seed=42)
    boot_exponents = []

    valid_mask = (x > 0) & (y > 0)
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]

    if len(x_valid) < 2:
        return a, b, 0.5 * abs(b) if b != 0 else 0.5

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = rng.choice(len(x_valid), size=len(x_valid), replace=True)
        x_boot = x_valid[indices]
        y_boot = y_valid[indices]

        try:
            _, b_boot = fit_power_law(x_boot, y_boot)
            boot_exponents.append(b_boot)
        except Exception:
            continue

    if len(boot_exponents) < 10:
        logger.log("fit_power_law_ci_warning", message="Bootstrap failed, returning large default")
        return a, b, 0.5 * abs(b) if b != 0 else 0.5

    boot_exponents = np.array(boot_exponents)
    std_err = np.std(boot_exponents, ddof=1)

    # Approximate CI using normal approximation
    # For 95% CI, z ≈ 1.96
    from scipy import stats
    z = stats.norm.ppf((1 + confidence) / 2)
    ci_half_width = z * std_err

    return float(a), float(b), float(ci_half_width)


def load_scaling_data(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Load and aggregate results for scaling analysis.

    Args:
        results: List of game result dictionaries containing 'agent_count',
                 'specialization_index', and 'retrieval_efficiency'.

    Returns:
        Aggregated DataFrame with mean metrics per agent_count.
    """
    if not results:
        logger.log("load_scaling_data_warning", message="No results provided")
        return pd.DataFrame(columns=["agent_count", "specialization_index", "retrieval_efficiency"])

    df = pd.DataFrame(results)
    required_cols = ["agent_count", "specialization_index", "retrieval_efficiency"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in results: {missing}")

    # Aggregate by agent_count
    aggregated = df.groupby("agent_count").agg({
        "specialization_index": "mean",
        "retrieval_efficiency": "mean"
    }).reset_index()

    logger.log("load_scaling_data_success", count=len(aggregated))
    return aggregated


def generate_scaling_plot(
    results: List[Dict[str, Any]],
    output_path: pathlib.Path
) -> None:
    """Generate a scaling plot with fitted power law curves.

    Reads REAL measured data from the provided results list (which must
    contain actual measurements, not synthetic placeholders), fits power laws,
    and writes a PDF plot to output_path.

    Args:
        results: List of game result dictionaries with real measurements.
        output_path: Path where the PDF plot will be saved.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        logger.log("matplotlib_missing", message="Cannot generate plot: matplotlib not installed")
        return

    if not results:
        logger.log("generate_scaling_plot_warning", message="No results to plot")
        return

    df = load_scaling_data(results)

    if len(df) < 2:
        logger.log("generate_scaling_plot_warning", message="Insufficient data points for trend (need >= 2)")
        # Still create a minimal plot to indicate the state
        plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, "Insufficient data for scaling plot",
                 ha='center', va='center', transform=plt.gca().transAxes)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    x = df["agent_count"].values
    y_spec = df["specialization_index"].values
    y_ret = df["retrieval_efficiency"].values

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Plot specialization
    ax = axes[0]
    ax.scatter(x, y_spec, label='Specialization Index', color='blue', zorder=3)
    if len(x) >= 2:
        try:
            a, b, ci = fit_power_law_with_ci(x, y_spec)
            x_fit = np.linspace(min(x), max(x), 100)
            y_fit = power_law(x_fit, a, b)
            ax.plot(x_fit, y_fit, 'b--', label=f'Power Law (exp={b:.3f} ± {ci:.3f})')
            ax.fill_between(x_fit,
                            power_law(x_fit, a, b - ci),
                            power_law(x_fit, a, b + ci),
                            color='blue', alpha=0.1)
        except Exception as e:
            logger.log("fit_specialization_error", message=str(e))

    ax.set_xlabel("Number of Agents")
    ax.set_ylabel("Specialization Index")
    ax.set_title("Scaling of Specialization")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot retrieval
    ax = axes[1]
    ax.scatter(x, y_ret, label='Retrieval Efficiency', color='green', zorder=3)
    if len(x) >= 2:
        try:
            a, b, ci = fit_power_law_with_ci(x, y_ret)
            x_fit = np.linspace(min(x), max(x), 100)
            y_fit = power_law(x_fit, a, b)
            ax.plot(x_fit, y_fit, 'g--', label=f'Power Law (exp={b:.3f} ± {ci:.3f})')
            ax.fill_between(x_fit,
                            power_law(x_fit, a, b - ci),
                            power_law(x_fit, a, b + ci),
                            color='green', alpha=0.1)
        except Exception as e:
            logger.log("fit_retrieval_error", message=str(e))

    ax.set_xlabel("Number of Agents")
    ax.set_ylabel("Retrieval Efficiency")
    ax.set_title("Scaling of Retrieval Efficiency")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.suptitle("Collective Remembering Scaling Analysis (Real Measurements)", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    logger.log("generate_scaling_plot_success", path=str(output_path))