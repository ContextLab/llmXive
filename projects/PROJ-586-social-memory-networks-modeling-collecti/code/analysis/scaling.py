"""
Scaling analysis for social memory networks.

Implements power-law fitting for metric trends vs. agent count.
Fits log-log curves for specialization index and retrieval efficiency.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
import warnings
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PowerLawFitResult:
    """Result of a power-law fit."""
    metric_name: str
    exponent: float
    intercept: float  # log(a) in log-log space
    r_squared: float
    p_value: float
    std_error: float
    n_points: int
    x_values: List[float]
    y_values: List[float]
    fitted_y: List[float]

@dataclass
class ScalingAnalysisResult:
    """Complete scaling analysis results."""
    specialization_fit: Optional[PowerLawFitResult]
    retrieval_fit: Optional[PowerLawFitResult]
    notes: List[str]


def power_law(x: float, a: float, b: float) -> float:
    """Compute power-law value: y = a * x^b."""
    return a * (x ** b)


def fit_power_law(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float, float, float]:
    """
    Power law function: y = alpha * x^beta
    
    Args:
        x: Independent variable values
        beta: Exponent parameter
        alpha: Scaling factor parameter
        
    Returns:
        Predicted y values
    """
    return alpha * np.power(x, beta)


def fit_power_law(
    x: np.ndarray, y: np.ndarray, method: str = "loglog"
) -> Tuple[float, float, Optional[Dict[str, Any]]]:
    """
    Fit a power law y = alpha * x^beta to data.
    
    Args:
        x: Independent variable (agent count)
        y: Dependent variable (metric value)
        method: Fitting method ("loglog" for linearized fit)
        
    Returns:
        Tuple of (beta, alpha, diagnostics)
        beta: Exponent
        alpha: Scaling factor
        diagnostics: Dictionary with R^2 and other fit metrics
    """
    if len(x) < 2:
        raise ValueError("At least 2 data points required for fitting")
    
    # Filter out non-positive values for log transformation
    mask = (x > 0) & (y > 0)
    x_valid = x[mask]
    y_valid = y[mask]
    
    if len(x_valid) < 2:
        raise ValueError("Need at least 2 positive data points for log-log fitting")
    
    if method == "loglog":
        # Linearize: log(y) = log(alpha) + beta * log(x)
        log_x = np.log(x_valid)
        log_y = np.log(y_valid)
        
        # Linear regression
        n = len(log_x)
        sum_x = np.sum(log_x)
        sum_y = np.sum(log_y)
        sum_xy = np.sum(log_x * log_y)
        sum_x2 = np.sum(log_x ** 2)
        
        # Slope (beta) and intercept (log(alpha))
        beta = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - beta * sum_x) / n
        alpha = np.exp(intercept)
        
        # Compute R^2
        y_pred = alpha * np.power(x_valid, beta)
        ss_res = np.sum((y_valid - y_pred) ** 2)
        ss_tot = np.sum((y_valid - np.mean(y_valid)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        diagnostics = {
            "r_squared": float(r_squared),
            "n_points": int(len(x_valid)),
            "method": method
        }
        
        return float(beta), float(alpha), diagnostics
    
    else:
        raise ValueError(f"Unknown fitting method: {method}")


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> Tuple[float, float, Dict[str, float], Dict[str, float]]:
    """
    Fit power law with bootstrap confidence intervals.
    
    Args:
        x: Independent variable (agent count)
        y: Dependent variable (metric value)
        n_bootstrap: Number of bootstrap resamples
        confidence_level: Confidence level for intervals (e.g., 0.95)
        
    Returns:
        Tuple of (beta, alpha, beta_ci, alpha_ci)
        beta: Exponent estimate
        alpha: Scaling factor estimate
        beta_ci: Dict with 'lower', 'upper' for beta
        alpha_ci: Dict with 'lower', 'upper' for alpha
    """
    beta_est, alpha_est, _ = fit_power_law(x, y)
    
    # Bootstrap for confidence intervals
    beta_samples = []
    alpha_samples = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(len(x), size=len(x), replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        try:
            b, a, _ = fit_power_law(x_boot, y_boot)
            beta_samples.append(b)
            alpha_samples.append(a)
        except (ValueError, RuntimeWarning):
            # Skip invalid fits
            continue
    
    if len(beta_samples) < 10:
        warnings.warn("Insufficient bootstrap samples for CI estimation")
        return beta_est, alpha_est, {"lower": beta_est, "upper": beta_est}, {"lower": alpha_est, "upper": alpha_est}
    
    beta_ci_lower = np.percentile(beta_samples, (1 - confidence_level) / 2 * 100)
    beta_ci_upper = np.percentile(beta_samples, (1 + confidence_level) / 2 * 100)
    alpha_ci_lower = np.percentile(alpha_samples, (1 - confidence_level) / 2 * 100)
    alpha_ci_upper = np.percentile(alpha_samples, (1 + confidence_level) / 2 * 100)
    
    beta_ci = {"lower": float(beta_ci_lower), "upper": float(beta_ci_upper)}
    alpha_ci = {"lower": float(alpha_ci_lower), "upper": float(alpha_ci_upper)}
    
    return beta_est, alpha_est, beta_ci, alpha_ci


def load_scaling_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load scaling analysis data from CSV.
    
    Args:
        data_path: Path to CSV file. If None, uses default path.
        
    Returns:
        DataFrame with columns: agent_count, specialization_index, retrieval_efficiency
    """
    if data_path is None:
        # Default path based on project structure
        data_path = "projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_data.csv"
    
    path = pathlib.Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {data_path}")
    
    df = pd.read_csv(path)
    
    # Validate required columns
    required_cols = ["agent_count", "specialization_index", "retrieval_efficiency"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in scaling data: {missing}")
    
    logger.log("load_scaling_data", path=str(path), rows=len(df))
    return df


def generate_scaling_plot(
    df: pd.DataFrame,
    output_path: str,
    title: str = "Scaling Analysis: Metrics vs. Agent Count"
) -> Dict[str, Any]:
    """
    Generate scaling plot with fitted power-law curves.
    
    Args:
        df: DataFrame with scaling data
        output_path: Path to save the plot (PDF or PNG)
        title: Plot title
        
    Returns:
        Dictionary with fit results and plot info
    """
    import matplotlib.pyplot as plt
    
    agent_counts = df["agent_count"].values
    spec_indices = df["specialization_index"].values
    ret_efficiencies = df["retrieval_efficiency"].values
    
    # Sort by agent count for plotting
    sort_idx = np.argsort(agent_counts)
    agent_counts = agent_counts[sort_idx]
    spec_indices = spec_indices[sort_idx]
    ret_efficiencies = ret_efficiencies[sort_idx]
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    results = {}
    
    # Specialization Index plot
    ax1 = axes[0]
    ax1.scatter(agent_counts, spec_indices, label="Observed", color="blue", s=60)
    
    try:
        beta_spec, alpha_spec, spec_diag = fit_power_law(agent_counts, spec_indices)
        x_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
        y_fit_spec = alpha_spec * np.power(x_fit, beta_spec)
        ax1.plot(x_fit, y_fit_spec, "r-", label=f"Power-law fit (β={beta_spec:.3f})", linewidth=2)
        ax1.set_xlabel("Number of Agents")
        ax1.set_ylabel("Specialization Index")
        ax1.set_title("Specialization Index vs. Agent Count")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        results["specialization"] = {
            "beta": beta_spec,
            "alpha": alpha_spec,
            "r_squared": spec_diag["r_squared"],
            "n_points": spec_diag["n_points"]
        }
    except (ValueError, RuntimeWarning) as e:
        ax1.text(0.5, 0.5, f"Fit failed: {str(e)}", transform=ax1.transAxes, ha="center")
        results["specialization"] = {"error": str(e)}
    
    # Retrieval Efficiency plot
    ax2 = axes[1]
    ax2.scatter(agent_counts, ret_efficiencies, label="Observed", color="green", s=60)
    
    try:
        beta_ret, alpha_ret, ret_diag = fit_power_law(agent_counts, ret_efficiencies)
        x_fit = np.linspace(min(agent_counts), max(agent_counts), 100)
        y_fit_ret = alpha_ret * np.power(x_fit, beta_ret)
        ax2.plot(x_fit, y_fit_ret, "r-", label=f"Power-law fit (β={beta_ret:.3f})", linewidth=2)
        ax2.set_xlabel("Number of Agents")
        ax2.set_ylabel("Retrieval Efficiency")
        ax2.set_title("Retrieval Efficiency vs. Agent Count")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        results["retrieval"] = {
            "beta": beta_ret,
            "alpha": alpha_ret,
            "r_squared": ret_diag["r_squared"],
            "n_points": ret_diag["n_points"]
        }
    except (ValueError, RuntimeWarning) as e:
        ax2.text(0.5, 0.5, f"Fit failed: {str(e)}", transform=ax2.transAxes, ha="center")
        results["retrieval"] = {"error": str(e)}
    
    fig.suptitle(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    
    results["plot_path"] = str(output_path)
    results["n_agent_counts"] = len(np.unique(agent_counts))
    
    logger.log("generate_scaling_plot", output=str(output_path), n_points=len(df))
    return results


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Fit power-law curves to scaling data"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_data.csv",
        help="Path to scaling data CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_results.json",
        help="Path to output JSON results"
    )
    parser.add_argument(
        "--plot",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf",
        help="Path to save scaling plot"
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap samples for CI"
    )
    return parser


def main() -> None:
    """Main entry point for scaling analysis."""
    parser = build_parser()
    args = parser.parse_args()
    
    logger.log("scaling_analysis_start", data=args.data, output=args.output)
    
    # Load data
    df = load_scaling_data(args.data)
    
    # Generate plot
    plot_results = generate_scaling_plot(df, args.plot)
    
    # Compute power-law fits with confidence intervals
    agent_counts = df["agent_count"].values
    spec_indices = df["specialization_index"].values
    ret_efficiencies = df["retrieval_efficiency"].values
    
    # Sort for consistency
    sort_idx = np.argsort(agent_counts)
    agent_counts = agent_counts[sort_idx]
    spec_indices = spec_indices[sort_idx]
    ret_efficiencies = ret_efficiencies[sort_idx]
    
    results = {
        "data_file": args.data,
        "plot_file": args.plot,
        "n_agent_counts": int(len(np.unique(agent_counts))),
        "specialization": {},
        "retrieval": {}
    }
    
    # Specialization fit with CI
    try:
        beta_spec, alpha_spec, beta_ci_spec, alpha_ci_spec = fit_power_law_with_ci(
            agent_counts, spec_indices, n_bootstrap=args.bootstrap
        )
        results["specialization"] = {
            "beta": beta_spec,
            "alpha": alpha_spec,
            "beta_ci": beta_ci_spec,
            "alpha_ci": alpha_ci_spec
        }
        logger.log("specialization_fit", beta=beta_spec, alpha=alpha_spec)
    except Exception as e:
        results["specialization"] = {"error": str(e)}
        logger.log("specialization_fit_failed", error=str(e))
    
    # Retrieval fit with CI
    try:
        beta_ret, alpha_ret, beta_ci_ret, alpha_ci_ret = fit_power_law_with_ci(
            agent_counts, ret_efficiencies, n_bootstrap=args.bootstrap
        )
        results["retrieval"] = {
            "beta": beta_ret,
            "alpha": alpha_ret,
            "beta_ci": beta_ci_ret,
            "alpha_ci": alpha_ci_ret
        }
        logger.log("retrieval_fit", beta=beta_ret, alpha=alpha_ret)
    except Exception as e:
        results["retrieval"] = {"error": str(e)}
        logger.log("retrieval_fit_failed", error=str(e))
    
    # Save results
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.log("scaling_analysis_complete", output=str(output_path))
    print(f"Scaling analysis complete. Results saved to {args.output}")
    print(f"Plot saved to {args.plot}")


if __name__ == "__main__":
    sys.exit(main())