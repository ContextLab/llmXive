"""
Scaling analysis: Power-law fitting for collective memory metrics.

Fits log-log curves for specialization index and retrieval efficiency
versus agent count to test for power-law scaling relationships.
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
import pandas as pd
from scipy import stats

# Ensure project root is on path for relative imports if run as script
try:
    from metrics.specialization import compute_specialization_index
    from metrics.retrieval import compute_retrieval_efficiency
except ImportError:
    pass  # Will be available in project context


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
    Compute power-law function: y = alpha * x^beta.
    
    Parameters
    ----------
    x : np.ndarray
        Independent variable (agent count).
    beta : float
        Power-law exponent.
    alpha : float
        Scaling coefficient.
        
    Returns
    -------
    np.ndarray
        Fitted values.
    """
    return alpha * np.power(x, beta)


def fit_power_law(
    x: np.ndarray, y: np.ndarray
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Fit a power-law model y = alpha * x^beta via log-log linear regression.
    
    Transforms to log(y) = log(alpha) + beta * log(x) and performs OLS.
    
    Parameters
    ----------
    x : np.ndarray
        Agent counts (independent variable).
    y : np.ndarray
        Metric values (dependent variable).
        
    Returns
    -------
    beta : float
        Estimated power-law exponent.
    alpha : float
        Estimated scaling coefficient.
    stats : dict
        Regression statistics including R-squared and p-value.
    """
    if len(x) < 2:
        raise ValueError("At least two data points are required for fitting.")
    
    # Filter out non-positive values which cannot be log-transformed
    valid_mask = (x > 0) & (y > 0)
    if np.sum(valid_mask) < 2:
        raise ValueError("Insufficient positive data points for log-log fitting.")
    
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    log_x = np.log(x_valid)
    log_y = np.log(y_valid)
    
    # Perform linear regression on log-transformed data
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
    
    beta = slope
    alpha = math.exp(intercept)
    
    stats_dict = {
        "r_squared": r_value**2,
        "p_value": p_value,
        "std_err_beta": std_err,
        "n_points": len(x_valid),
        "method": "log-log OLS"
    }
    
    return beta, alpha, stats_dict


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> Tuple[float, float, Dict[str, Any], Dict[str, float]]:
    """
    Fit power-law and compute bootstrap confidence intervals for the exponent.
    
    Parameters
    ----------
    x : np.ndarray
        Agent counts.
    y : np.ndarray
        Metric values.
    n_bootstrap : int
        Number of bootstrap resamples.
    confidence_level : float
        Confidence level for intervals (e.g., 0.95 for 95% CI).
        
    Returns
    -------
    beta : float
        Point estimate of exponent.
    alpha : float
        Point estimate of coefficient.
    stats : dict
        Regression statistics.
    ci : dict
        Confidence interval bounds for beta (lower, upper).
    """
    # Point estimate
    beta, alpha, stats = fit_power_law(x, y)
    
    # Bootstrap for confidence intervals
    beta_samples = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(len(x), size=len(x), replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        try:
            b, _, _ = fit_power_law(x_boot, y_boot)
            beta_samples.append(b)
        except ValueError:
            # Skip invalid resamples
            continue
    
    if len(beta_samples) < 10:
        warnings.warn(
            "Insufficient valid bootstrap samples to compute confidence intervals."
        )
        ci = {"lower": np.nan, "upper": np.nan}
    else:
        beta_samples = np.array(beta_samples)
        alpha_val = (1 - confidence_level) / 2
        lower = np.percentile(beta_samples, 100 * alpha_val)
        upper = np.percentile(beta_samples, 100 * (1 - alpha_val))
        ci = {"lower": float(lower), "upper": float(upper)}
    
    return beta, alpha, stats, ci


def load_scaling_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load scaling experiment results from CSV files.
    
    Expects files named:
    - results_scaling_Nagents.csv where N is the agent count
    Or a single aggregated file if specified.
    
    Parameters
    ----------
    results_dir : pathlib.Path, optional
        Directory containing result CSVs. Defaults to project results dir.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: agent_count, specialization_index, retrieval_efficiency
    """
    if results_dir is None:
        results_dir = pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
    
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    
    data_rows = []
    
    # Look for scaling result files
    scaling_files = list(results_dir.glob("results_scaling_*.csv"))
    
    if not scaling_files:
        # Fallback: try to load from a generic scaling results file
        generic_file = results_dir / "scaling_results.csv"
        if generic_file.exists():
            scaling_files = [generic_file]
        else:
            raise FileNotFoundError(
                f"No scaling result files found in {results_dir}. "
                "Expected files like results_scaling_Nagents.csv"
            )
    
    for file_path in scaling_files:
        try:
            df = pd.read_csv(file_path)
            
            # Ensure required columns exist
            required_cols = ["agent_count", "specialization_index", "retrieval_efficiency"]
            if not all(col in df.columns for col in required_cols):
                # Try to infer from available columns
                if "agent_count" not in df.columns:
                    # Try to extract from filename
                    parts = file_path.stem.split("_")
                    for i, part in enumerate(parts):
                        if part.lower() == "agents" and i > 0:
                            try:
                                n_agents = int(parts[i-1])
                                df["agent_count"] = n_agents
                                break
                            except ValueError:
                                pass
                
                if "specialization_index" not in df.columns:
                    # Try common aliases
                    for alias in ["spec_index", "specialization", "specialization_mean"]:
                        if alias in df.columns:
                            df["specialization_index"] = df[alias]
                            break
                
                if "retrieval_efficiency" not in df.columns:
                    for alias in ["retrieval_eff", "retrieval", "retrieval_mean"]:
                        if alias in df.columns:
                            df["retrieval_efficiency"] = df[alias]
                            break
            
            # Filter valid rows
            valid_df = df.dropna(subset=required_cols)
            valid_df = valid_df[
                (valid_df["agent_count"] > 0) &
                (valid_df["specialization_index"] > 0) &
                (valid_df["retrieval_efficiency"] > 0)
            ]
            
            for _, row in valid_df.iterrows():
                data_rows.append({
                    "agent_count": int(row["agent_count"]),
                    "specialization_index": float(row["specialization_index"]),
                    "retrieval_efficiency": float(row["retrieval_efficiency"])
                })
                
        except Exception as e:
            warnings.warn(f"Failed to load {file_path}: {e}")
            continue
    
    if not data_rows:
        raise ValueError("No valid scaling data loaded from any files.")
    
    return pd.DataFrame(data_rows)


def generate_scaling_plot(
    data: pd.DataFrame,
    output_path: Optional[pathlib.Path] = None,
    show: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Generate scaling plot with fitted power-law curves.
    
    Plots specialization index and retrieval efficiency vs agent count
    on log-log scales with fitted power-law curves overlaid.
    
    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with agent_count, specialization_index, retrieval_efficiency.
    output_path : pathlib.Path, optional
        Path to save the plot. Defaults to results/scaling_plot.pdf.
    show : bool
        Whether to display the plot interactively.
        
    Returns
    -------
    results : dict
        Dictionary containing fit results for both metrics.
    """
    import matplotlib.pyplot as plt
    
    if output_path is None:
        output_path = pathlib.Path(
            "projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf"
        )
    
    # Prepare data
    agent_counts = data["agent_count"].values
    spec_indices = data["specialization_index"].values
    ret_effs = data["retrieval_efficiency"].values
    
    # Sort by agent count for plotting
    sort_idx = np.argsort(agent_counts)
    agent_counts = agent_counts[sort_idx]
    spec_indices = spec_indices[sort_idx]
    ret_effs = ret_effs[sort_idx]
    
    # Fit power laws
    results = {}
    
    # Specialization index fit
    try:
        beta_spec, alpha_spec, stats_spec, ci_spec = fit_power_law_with_ci(
            agent_counts, spec_indices
        )
        results["specialization"] = {
            "beta": beta_spec,
            "alpha": alpha_spec,
            "stats": stats_spec,
            "ci": ci_spec
        }
    except Exception as e:
        warnings.warn(f"Failed to fit specialization index: {e}")
        results["specialization"] = None
    
    # Retrieval efficiency fit
    try:
        beta_ret, alpha_ret, stats_ret, ci_ret = fit_power_law_with_ci(
            agent_counts, ret_effs
        )
        results["retrieval"] = {
            "beta": beta_ret,
            "alpha": alpha_ret,
            "stats": stats_ret,
            "ci": ci_ret
        }
    except Exception as e:
        warnings.warn(f"Failed to fit retrieval efficiency: {e}")
        results["retrieval"] = None
    
    # Create plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Specialization Index
    ax1 = axes[0]
    ax1.loglog(agent_counts, spec_indices, 'o', label='Data', markersize=8)
    
    if results["specialization"]:
        beta = results["specialization"]["beta"]
        alpha = results["specialization"]["alpha"]
        x_fit = np.logspace(np.log10(agent_counts.min()), np.log10(agent_counts.max()), 100)
        y_fit = alpha * np.power(x_fit, beta)
        ax1.loglog(x_fit, y_fit, '--', label=f'Fit: y = {alpha:.3f}x^{beta:.3f}')
        
        # Add CI note if available
        ci = results["specialization"]["ci"]
        if not np.isnan(ci["lower"]):
            ax1.text(
                0.05, 0.95,
                f"β = {beta:.3f} [95% CI: {ci['lower']:.3f}, {ci['upper']:.3f}]",
                transform=ax1.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
    
    ax1.set_xlabel("Number of Agents (N)")
    ax1.set_ylabel("Specialization Index")
    ax1.set_title("Specialization Index Scaling")
    ax1.grid(True, which="both", ls="--", alpha=0.5)
    ax1.legend()
    
    # Plot 2: Retrieval Efficiency
    ax2 = axes[1]
    ax2.loglog(agent_counts, ret_effs, 's', label='Data', markersize=8)
    
    if results["retrieval"]:
        beta = results["retrieval"]["beta"]
        alpha = results["retrieval"]["alpha"]
        x_fit = np.logspace(np.log10(agent_counts.min()), np.log10(agent_counts.max()), 100)
        y_fit = alpha * np.power(x_fit, beta)
        ax2.loglog(x_fit, y_fit, '--', label=f'Fit: y = {alpha:.3f}x^{beta:.3f}')
        
        ci = results["retrieval"]["ci"]
        if not np.isnan(ci["lower"]):
            ax2.text(
                0.05, 0.95,
                f"β = {beta:.3f} [95% CI: {ci['lower']:.3f}, {ci['upper']:.3f}]",
                transform=ax2.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5)
            )
    
    ax2.set_xlabel("Number of Agents (N)")
    ax2.set_ylabel("Retrieval Efficiency")
    ax2.set_title("Retrieval Efficiency Scaling")
    ax2.grid(True, which="both", ls="--", alpha=0.5)
    ax2.legend()
    
    # Add note about data points
    fig.suptitle(
        "Power-law Scaling Analysis of Collective Memory Metrics\n"
        "Note: 3 data points limit power-law reliability",
        fontsize=12,
        y=1.02
    )
    
    plt.tight_layout()
    
    # Save plot
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Scaling plot saved to: {output_path}")
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return results


def main():
    """Main entry point for scaling analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fit power-law models to scaling experiment results."
    )
    parser.add_argument(
        "--results-dir",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory containing scaling result CSVs"
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Output path for the plot (default: results/scaling_plot.pdf)"
    )
    parser.add_argument(
        "--json-output",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_fit_results.json"),
        help="Output path for JSON results"
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap samples for CI (default: 1000)"
    )
    
    args = parser.parse_args()
    
    print(f"Loading scaling data from: {args.results_dir}")
    data = load_scaling_data(args.results_dir)
    print(f"Loaded {len(data)} data points")
    print(data)
    
    print("\nFitting power-law models...")
    results = generate_scaling_plot(data, args.output)
    
    # Save results to JSON
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.json_output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFit results saved to: {args.json_output}")
    
    # Print summary
    print("\n" + "="*60)
    print("SCALING ANALYSIS SUMMARY")
    print("="*60)
    
    for metric, res in results.items():
        if res:
            print(f"\n{metric.upper()}:")
            print(f"  Exponent (β): {res['beta']:.4f}")
            print(f"  Coefficient (α): {res['alpha']:.4f}")
            print(f"  R²: {res['stats']['r_squared']:.4f}")
            print(f"  p-value: {res['stats']['p_value']:.4f}")
            ci = res['ci']
            if not np.isnan(ci['lower']):
                print(f"  95% CI for β: [{ci['lower']:.4f}, {ci['upper']:.4f}]")
        else:
            print(f"\n{metric.upper()}: Fit failed")
    
    print("\n" + "="*60)
    print("Note: 3 data points limit power-law reliability")
    print("="*60)


if __name__ == "__main__":
    sys.exit(main())