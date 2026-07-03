"""Scaling analysis utilities.

Provides power-law fitting for metric trends versus agent count,
specifically for the agent counts 3, 5, and 7 as required by US-3.
"""

from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import t

__all__ = [
    "fit_power_law",
    "fit_power_law_with_ci",
    "generate_scaling_plot",
    "load_scaling_data",
]


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power-law function: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law(
    x: np.ndarray,
    y: np.ndarray,
    x0: Optional[float] = None,
    y0: Optional[float] = None,
) -> Tuple[float, float]:
    """Fit a power-law model y = a * x^b to the data.

    Args:
        x: Independent variable (agent counts).
        y: Dependent variable (metric values).
        x0: Initial guess for a (scaling factor).
        y0: Initial guess for b (scaling exponent).

    Returns:
        Tuple (a, b) of fitted parameters.

    Raises:
        ValueError: If fitting fails or data is insufficient.
    """
    if len(x) < 2:
        raise ValueError("At least 2 data points are required for power-law fitting.")

    # Filter out non-positive values for log-transform stability
    mask = (x > 0) & (y > 0)
    if np.sum(mask) < 2:
        raise ValueError(
            "At least 2 positive (x, y) pairs are required for power-law fitting."
        )
    x_fit = x[mask]
    y_fit = y[mask]

    # Initial guesses
    if x0 is None:
        x0 = y_fit[0] / np.power(x_fit[0], 1.0) if x_fit[0] != 0 else 1.0
    if y0 is None:
        y0 = 1.0

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            popt, _ = curve_fit(
                power_law,
                x_fit,
                y_fit,
                p0=[x0, y0],
                maxfev=10000,
                bounds=([0, -10], [np.inf, 10]),
            )
    except Exception as e:
        raise ValueError(f"Power-law fitting failed: {e}") from e

    return float(popt[0]), float(popt[1])


def fit_power_law_with_ci(
    df: pd.DataFrame,
    metric: str,
    agent_counts: List[int] = [3, 5, 7],
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """Fit a power-law to metric vs. agent count and compute confidence intervals.

    Args:
        df: DataFrame with columns including 'agent_count' and the metric.
        metric: Name of the metric column to fit.
        agent_counts: List of agent counts to include (default: [3, 5, 7]).
        confidence_level: Confidence level for CI (default: 0.95).

    Returns:
        Dictionary containing:
            - 'a': scaling factor
            - 'b': scaling exponent
            - 'b_ci': (lower, upper) confidence interval for exponent
            - 'r_squared': coefficient of determination
            - 'n': number of data points used
    """
    # Filter and aggregate data by agent count
    subset = df[df["agent_count"].isin(agent_counts)].copy()
    if subset.empty:
        raise ValueError(
            f"No data found for agent counts {agent_counts} in the provided DataFrame."
        )

    # Compute mean metric per agent count
    aggregated = (
        subset.groupby("agent_count")[metric]
        .mean()
        .reset_index()
        .sort_values("agent_count")
    )

    x = aggregated["agent_count"].values.astype(float)
    y = aggregated[metric].values.astype(float)

    # Fit power law
    a, b = fit_power_law(x, y)

    # Compute residuals for CI
    y_pred = power_law(x, a, b)
    residuals = y - y_pred
    n = len(x)
    dof = n - 2

    if dof <= 0:
        # Not enough degrees of freedom for CI; return wide interval
        b_ci = (-10.0, 10.0)
        r_squared = 0.0
    else:
        # Standard error of the exponent (approximate via bootstrap or delta method)
        # Here we use a simplified approach: SE_b ≈ std(residuals) / (std(x) * |b|)
        # More robust would be to use the covariance matrix from curve_fit
        try:
            popt, pcov = curve_fit(power_law, x, y, p0=[a, b], maxfev=10000)
            perr = np.sqrt(np.diag(pcov))
            se_b = perr[1] if len(perr) > 1 else 0.1
        except Exception:
            se_b = 0.1  # Fallback

        # Confidence interval for b
        t_crit = t.ppf((1 + confidence_level) / 2, dof)
        b_ci = (b - t_crit * se_b, b + t_crit * se_b)

        # R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    return {
        "a": a,
        "b": b,
        "b_ci": b_ci,
        "r_squared": r_squared,
        "n": n,
        "agent_counts": agent_counts,
        "metric": metric,
    }


def load_scaling_data(csv_path: pathlib.Path) -> pd.DataFrame:
    """Load scaling experiment data from a CSV file.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        DataFrame with columns including 'agent_count' and metrics.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required_cols = ["agent_count"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(
            f"CSV must contain columns: {required_cols}. Found: {list(df.columns)}"
        )
    return df


def generate_scaling_plot(
    csv_path: pathlib.Path,
    output_path: pathlib.Path,
    agent_counts: List[int] = [3, 5, 7],
) -> None:
    """Read ``csv_path`` (produced by ``run_experiment``) and write a PDF plot.

    The plot shows specialization index and retrieval efficiency versus the
    number of agents, together with fitted power‑law curves.

    Args:
        csv_path: Path to the CSV file with scaling results.
        output_path: Path where the PDF plot will be saved.
        agent_counts: List of agent counts to include in the analysis.
    """
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    df = load_scaling_data(csv_path)

    metrics_to_plot = ["specialization_index", "retrieval_efficiency"]
    fits = {}

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, metric in zip(axes, metrics_to_plot):
        if metric not in df.columns:
            ax.text(
                0.5, 0.5, f"Column '{metric}' not found",
                ha="center", va="center", transform=ax.transAxes
            )
            ax.set_title(metric.replace("_", " ").title())
            continue

        # Fit power law
        fit_result = fit_power_law_with_ci(df, metric, agent_counts)
        fits[metric] = fit_result

        # Plot data points
        subset = df[df["agent_count"].isin(agent_counts)]
        ax.scatter(
            subset["agent_count"],
            subset[metric],
            color="blue",
            label="Observed",
            alpha=0.7,
        )

        # Plot fitted curve
        x_vals = np.linspace(min(agent_counts), max(agent_counts), 100)
        y_vals = power_law(x_vals, fit_result["a"], fit_result["b"])
        ax.plot(x_vals, y_vals, "r-", label="Power-law fit")

        # Annotate exponent and CI
        b = fit_result["b"]
        b_ci = fit_result["b_ci"]
        ax.text(
            0.05, 0.95,
            f"Exponent: {b:.3f}\n95% CI: [{b_ci[0]:.3f}, {b_ci[1]:.3f}]\n"
            f"R²: {fit_result['r_squared']:.3f}",
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

        ax.set_xlabel("Number of Agents")
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.set_title(metric.replace("_", " ").title())
        ax.legend()
        ax.grid(True, alpha=0.3)

    # Add note about data limitation
    fig.suptitle(
        "Scaling Analysis: Metric Trends vs. Agent Count\n"
        "(Note: 3 data points limit power-law reliability)",
        fontsize=12,
        y=1.02,
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()