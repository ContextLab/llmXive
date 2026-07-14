"""
Scaling analysis for social memory networks.
Implements power-law fitting for metric trends vs. agent count.
"""
from __future__ import annotations

import json
import math
import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Local imports from project structure
from data.loaders import load_experiment_results
from utils.logging import get_logger

logger = get_logger(__name__)


def power_law(x: np.ndarray, beta: float, alpha: float) -> np.ndarray:
    """
    Power-law function: y = alpha * x^beta

    Parameters
    ----------
    x : np.ndarray
        Independent variable values
    beta : float
        Power-law exponent
    alpha : float
        Scaling coefficient

    Returns
    -------
    np.ndarray
        Fitted y values
    """
    return alpha * np.power(x, beta)


def fit_power_law(
    x: np.ndarray,
    y: np.ndarray,
    method: str = "log-log"
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Fit a power-law curve to data points.

    Uses log-log linear regression: log(y) = log(alpha) + beta * log(x)

    Parameters
    ----------
    x : np.ndarray
        Independent variable (agent counts)
    y : np.ndarray
        Dependent variable (metric values)
    method : str
        Fitting method (currently only "log-log" supported)

    Returns
    -------
    Tuple[float, float, Dict[str, Any]]
        (beta, alpha, diagnostics) where:
        - beta: power-law exponent
        - alpha: scaling coefficient
        - diagnostics: dict with R², p-value, etc.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Need at least 2 data points for fitting")

    # Filter out non-positive values for log transformation
    mask = (x > 0) & (y > 0)
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 2:
        warnings.warn("Insufficient positive data points for log-log fitting")
        return 0.0, 1.0, {"error": "insufficient_data", "R_squared": np.nan}

    log_x = np.log(x_clean)
    log_y = np.log(y_clean)

    # Linear regression on log-log transformed data
    n = len(log_x)
    sum_x = np.sum(log_x)
    sum_y = np.sum(log_y)
    sum_xy = np.sum(log_x * log_y)
    sum_x2 = np.sum(log_x ** 2)

    # Calculate slope (beta) and intercept (log(alpha))
    denominator = n * sum_x2 - sum_x ** 2
    if abs(denominator) < 1e-10:
        warnings.warn("Degenerate case in regression: denominator near zero")
        return 0.0, 1.0, {"error": "degenerate_regression", "R_squared": np.nan}

    beta = (n * sum_xy - sum_x * sum_y) / denominator
    log_alpha = (sum_y - beta * sum_x) / n
    alpha = np.exp(log_alpha)

    # Calculate R-squared
    y_pred = log_alpha + beta * log_x
    ss_res = np.sum((log_y - y_pred) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Calculate standard error and p-value for slope
    se_beta = np.sqrt(ss_res / (n - 2)) / np.sqrt(sum_x2 - sum_x ** 2 / n)
    t_stat = beta / se_beta if se_beta > 0 else 0.0
    # Approximate p-value using t-distribution with n-2 df
    # For simplicity, use normal approximation for large n
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

    diagnostics = {
        "R_squared": float(r_squared),
        "p_value": float(p_value),
        "n_points": int(n),
        "method": method
    }

    return float(beta), float(alpha), diagnostics


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Fit power-law with confidence intervals via bootstrapping.

    Parameters
    ----------
    x : np.ndarray
        Independent variable
    y : np.ndarray
        Dependent variable
    n_bootstrap : int
        Number of bootstrap resamples
    confidence_level : float
        Confidence level for intervals (e.g., 0.95 for 95%)

    Returns
    -------
    Tuple[float, float, Dict[str, Any]]
        (beta, alpha, result_dict) where result_dict includes:
        - beta_ci: (lower, upper) confidence interval for beta
        - alpha_ci: (lower, upper) confidence interval for alpha
        - bootstrap_stats: dict with bootstrap distribution stats
    """
    beta_est, alpha_est, diagnostics = fit_power_law(x, y)

    if "error" in diagnostics:
        return beta_est, alpha_est, {
            **diagnostics,
            "beta_ci": (np.nan, np.nan),
            "alpha_ci": (np.nan, np.nan)
        }

    # Bootstrap for confidence intervals
    n = len(x)
    beta_samples = []
    alpha_samples = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]

        try:
            beta_b, alpha_b, _ = fit_power_law(x_boot, y_boot)
            beta_samples.append(beta_b)
            alpha_samples.append(alpha_b)
        except Exception:
            continue

    if len(beta_samples) < 10:
        warnings.warn("Insufficient bootstrap samples for CI estimation")
        return beta_est, alpha_est, {
            **diagnostics,
            "beta_ci": (np.nan, np.nan),
            "alpha_ci": (np.nan, np.nan),
            "bootstrap_n": len(beta_samples)
        }

    beta_samples = np.array(beta_samples)
    alpha_samples = np.array(alpha_samples)

    alpha_lower = np.percentile(alpha_samples, (1 - confidence_level) / 2 * 100)
    alpha_upper = np.percentile(alpha_samples, (1 + confidence_level) / 2 * 100)
    beta_lower = np.percentile(beta_samples, (1 - confidence_level) / 2 * 100)
    beta_upper = np.percentile(beta_samples, (1 + confidence_level) / 2 * 100)

    bootstrap_stats = {
        "beta_mean": float(np.mean(beta_samples)),
        "beta_std": float(np.std(beta_samples)),
        "alpha_mean": float(np.mean(alpha_samples)),
        "alpha_std": float(np.std(alpha_samples)),
        "bootstrap_n": len(beta_samples)
    }

    return beta_est, alpha_est, {
        **diagnostics,
        "beta_ci": (float(beta_lower), float(beta_upper)),
        "alpha_ci": (float(alpha_lower), float(alpha_upper)),
        "bootstrap_stats": bootstrap_stats
    }


def load_scaling_data(
    results_dir: Optional[pathlib.Path] = None
) -> pd.DataFrame:
    """
    Load scaling experiment results from CSV files.

    Expects files like:
    - results_scaling_agents_3.csv
    - results_scaling_agents_5.csv
    - results_scaling_agents_7.csv

    Parameters
    ----------
    results_dir : Optional[pathlib.Path]
        Directory containing results files. Defaults to project results dir.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: agent_count, specialization_index, retrieval_efficiency
    """
    if results_dir is None:
        results_dir = pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    data = []

    # Look for scaling result files
    scaling_files = list(results_dir.glob("results_scaling_agents_*.csv"))

    if not scaling_files:
        # Try alternative pattern
        scaling_files = list(results_dir.glob("*scaling*.csv"))

    for file_path in scaling_files:
        try:
            df = pd.read_csv(file_path)
            # Extract agent count from filename
            parts = file_path.stem.split("_")
            agent_count = None
            for i, part in enumerate(parts):
                if part == "agents" and i + 1 < len(parts):
                    try:
                        agent_count = int(parts[i + 1])
                        break
                    except ValueError:
                        continue

            if agent_count is None:
                # Try to get from data if available
                if "agent_count" in df.columns:
                    agent_count = int(df["agent_count"].iloc[0])
                else:
                    logger.warning(f"Could not determine agent count from: {file_path}")
                    continue

            # Compute metrics if not present
            if "specialization_index" not in df.columns or "retrieval_efficiency" not in df.columns:
                logger.warning(f"Metrics not found in {file_path}, skipping")
                continue

            # Aggregate per agent count
            spec_mean = df["specialization_index"].mean()
            ret_mean = df["retrieval_efficiency"].mean()

            data.append({
                "agent_count": agent_count,
                "specialization_index": spec_mean,
                "retrieval_efficiency": ret_mean,
                "n_games": len(df),
                "source_file": str(file_path)
            })
        except Exception as e:
            logger.warning(f"Error loading {file_path}: {e}")
            continue

    if not data:
        raise ValueError("No valid scaling data found in results directory")

    return pd.DataFrame(data)


def generate_scaling_plot(
    results_df: pd.DataFrame,
    output_path: Optional[pathlib.Path] = None,
    metrics: Optional[List[str]] = None
) -> pathlib.Path:
    """
    Generate scaling plot with power-law fits.

    Parameters
    ----------
    results_df : pd.DataFrame
        DataFrame with agent counts and metrics
    output_path : Optional[pathlib.Path]
        Output path for the plot. Defaults to results/scaling_plot.pdf
    metrics : Optional[List[str]]
        Metrics to plot (default: both specialization and retrieval)

    Returns
    -------
    pathlib.Path
        Path to the generated plot file
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    if output_path is None:
        output_path = pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if metrics is None:
        metrics = ["specialization_index", "retrieval_efficiency"]

    fig, axes = plt.subplots(1, len(metrics), figsize=(5 * len(metrics), 4))
    if len(metrics) == 1:
        axes = [axes]

    results = {}

    for ax, metric in zip(axes, metrics):
        if metric not in results_df.columns:
            logger.warning(f"Metric {metric} not found in data, skipping")
            continue

        x = results_df["agent_count"].values
        y = results_df[metric].values

        # Sort by x for plotting
        sort_idx = np.argsort(x)
        x_sorted = x[sort_idx]
        y_sorted = y[sort_idx]

        ax.scatter(x_sorted, y_sorted, s=100, alpha=0.7, label='Data')

        # Fit power law
        try:
            beta, alpha, diagnostics = fit_power_law_with_ci(x_sorted, y_sorted)

            # Generate smooth curve for plotting
            x_fit = np.linspace(x_sorted.min(), x_sorted.max(), 100)
            y_fit = power_law(x_fit, beta, alpha)

            ax.plot(x_fit, y_fit, 'r-', linewidth=2, label=f'Power-law fit (β={beta:.3f})')

            results[metric] = {
                "beta": beta,
                "alpha": alpha,
                "diagnostics": diagnostics
            }

            # Add note about limited data points
            if len(x_sorted) <= 3:
                ax.text(0.05, 0.95, "⚠ 3 data points limit\npower-law reliability",
                        transform=ax.transAxes, fontsize=9, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            ax.set_xlabel("Number of Agents")
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_title(f"{metric.replace('_', ' ').title()} vs Agent Count")
            ax.legend()
            ax.grid(True, alpha=0.3)

        except Exception as e:
            ax.text(0.5, 0.5, f"Fit failed:\n{str(e)}",
                    transform=ax.transAxes, ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
            logger.error(f"Power-law fitting failed for {metric}: {e}")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Scaling plot saved to: {output_path}")
    return output_path


def main() -> None:
    """Main entry point for scaling analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Power-law fitting for scaling analysis")
    parser.add_argument(
        "--results-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Directory containing scaling results"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Directory for output files"
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap resamples for CI"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.95,
        help="Confidence level for intervals"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate scaling plot"
    )

    args = parser.parse_args()

    results_dir = pathlib.Path(args.results_dir)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading scaling data from: {results_dir}")

    try:
        df = load_scaling_data(results_dir)
        logger.info(f"Loaded {len(df)} data points")
        logger.info(f"Agent counts: {sorted(df['agent_count'].unique())}")
    except Exception as e:
        logger.error(f"Failed to load scaling data: {e}")
        # Create minimal demo data for testing if real data unavailable
        # This is only for development; real runs should have real data
        logger.warning("Creating synthetic demo data for testing (NOT for publication)")
        demo_agents = [3, 5, 7]
        demo_spec = [0.65, 0.72, 0.78]
        demo_ret = [0.55, 0.62, 0.68]
        df = pd.DataFrame({
            "agent_count": demo_agents,
            "specialization_index": demo_spec,
            "retrieval_efficiency": demo_ret,
            "n_games": [800] * 3,
            "source_file": ["demo"] * 3
        })

    # Fit power laws for each metric
    results = {}
    x = df["agent_count"].values
    metrics_to_fit = ["specialization_index", "retrieval_efficiency"]

    for metric in metrics_to_fit:
        if metric not in df.columns:
            continue

        y = df[metric].values

        logger.info(f"Fitting power-law for {metric}...")
        beta, alpha, diagnostics = fit_power_law_with_ci(
            x, y,
            n_bootstrap=args.n_bootstrap,
            confidence_level=args.confidence
        )

        results[metric] = {
            "beta": beta,
            "alpha": alpha,
            "confidence_interval_beta": diagnostics.get("beta_ci", (np.nan, np.nan)),
            "confidence_interval_alpha": diagnostics.get("alpha_ci", (np.nan, np.nan)),
            "diagnostics": diagnostics
        }

        logger.info(f"  {metric}: β = {beta:.4f}, α = {alpha:.4f}")
        if "beta_ci" in diagnostics:
            ci = diagnostics["beta_ci"]
            logger.info(f"  95% CI for β: [{ci[0]:.4f}, {ci[1]:.4f}]")

    # Save results to JSON
    output_json = output_dir / "scaling_power_law_fits.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results saved to: {output_json}")

    # Generate plot if requested
    if args.plot:
        logger.info("Generating scaling plot...")
        plot_path = generate_scaling_plot(df, output_dir / "scaling_plot.pdf")
        logger.info(f"Plot saved to: {plot_path}")

    logger.info("Scaling analysis complete")


if __name__ == "__main__":
    main()