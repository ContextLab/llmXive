"""
Scaling analysis for social memory networks.

Implements power-law fitting for metric trends (specialization index, retrieval efficiency)
versus agent count (3, 5, 7) as required by User Story 3.

Per reviewer feedback (Geoffrey West), we test whether collective remembering fidelity
scales sublinearly (N^0.85) like urban infrastructure, or follows a different law.

NOTE: With only 3 data points (N=3,5,7), power-law fitting is statistically fragile.
The implementation includes confidence intervals and explicitly notes this limitation
in the generated report.
"""
from __future__ import annotations

import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import existing metrics functions from sibling modules
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power-law function: y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law(
    x: np.ndarray, y: np.ndarray, p0: Optional[Tuple[float, float]] = None
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Fit a power-law model y = a * x^b to data using non-linear least squares.
    
    Args:
        x: Independent variable (agent counts).
        y: Dependent variable (metric values).
        p0: Initial guess for (a, b). If None, uses heuristic defaults.
        
    Returns:
        Tuple of (a, b, metadata_dict).
        metadata_dict contains covariance, r_squared, and fit diagnostics.
    """
    if len(x) < 2:
        raise ValueError("At least 2 data points required for fitting.")
    
    # Default initial guess: a=1, b=0.85 (sublinear, per West's urban scaling)
    if p0 is None:
        p0 = (1.0, 0.85)
    
    try:
        from scipy.optimize import curve_fit
    except ImportError:
        raise ImportError("scipy is required for power-law fitting.")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            popt, pcov = curve_fit(power_law, x, y, p0=p0, maxfev=5000)
            a, b = popt
            perr = np.sqrt(np.diag(pcov))
        except RuntimeError as e:
            # Fallback: log-log linear regression if non-linear fit fails
            # This is valid for power laws: log(y) = log(a) + b*log(x)
            log_x = np.log(x)
            log_y = np.log(y)
            slope, intercept, r_val, _, _ = stats.linregress(log_x, log_y)
            a = np.exp(intercept)
            b = slope
            perr = (np.nan, np.nan)  # Uncertainty unknown in fallback
    
    # Calculate R-squared
    y_pred = power_law(x, a, b)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    metadata = {
        "a": a,
        "b": b,
        "a_stderr": perr[0] if not np.isnan(perr[0]) else None,
        "b_stderr": perr[1] if not np.isnan(perr[1]) else None,
        "r_squared": r_squared,
        "n_points": len(x),
        "fit_method": "nonlinear" if 'popt' in locals() else "log-linear-fallback",
    }
    
    return a, b, metadata


def fit_power_law_with_ci(
    x: np.ndarray, y: np.ndarray, n_boot: int = 1000, confidence: float = 0.95
) -> Tuple[float, float, Tuple[float, float], Tuple[float, float], Dict[str, Any]]:
    """
    Fit power law with bootstrap confidence intervals for the exponent.
    
    Args:
        x: Independent variable.
        y: Dependent variable.
        n_boot: Number of bootstrap resamples.
        confidence: Confidence level (e.g., 0.95 for 95% CI).
        
    Returns:
        (a, b, (a_lo, a_hi), (b_lo, b_hi), metadata)
    """
    a, b, meta = fit_power_law(x, y)
    
    if len(x) < 3:
        # Cannot compute meaningful CI with < 3 points
        return a, b, (np.nan, np.nan), (np.nan, np.nan), meta
    
    boot_a = []
    boot_b = []
    
    for _ in range(n_boot):
        # Resample with replacement
        indices = np.random.choice(len(x), size=len(x), replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        try:
            a_boot, b_boot, _ = fit_power_law(x_boot, y_boot)
            boot_a.append(a_boot)
            boot_b.append(b_boot)
        except Exception:
            continue
    
    if len(boot_b) < 10:
        # Not enough successful fits
        return a, b, (np.nan, np.nan), (np.nan, np.nan), meta
    
    b_ci = np.percentile(boot_b, [(1 - confidence) / 2 * 100, (1 + confidence) / 2 * 100])
    a_ci = np.percentile(boot_a, [(1 - confidence) / 2 * 100, (1 + confidence) / 2 * 100])
    
    meta["b_ci"] = (b_ci[0], b_ci[1])
    meta["a_ci"] = (a_ci[0], a_ci[1])
    
    return a, b, tuple(a_ci), tuple(b_ci), meta


def load_scaling_data(
    results_path: pathlib.Path,
    agent_counts: List[int] = [3, 5, 7],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Load and aggregate scaling data from experiment results CSV.
    
    Expects a CSV with columns: game_id, specialization_index, retrieval_efficiency, agent_count, context_condition
    
    Returns:
        Tuple of (agent_counts_arr, spec_indices, retrieval_effs, full_df)
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    
    # Filter for requested agent counts
    df_filtered = df[df["agent_count"].isin(agent_counts)]
    
    if len(df_filtered) == 0:
        raise ValueError(f"No data found for agent counts {agent_counts} in {results_path}")
    
    # Aggregate by agent count (mean and std)
    summary = df_filtered.groupby("agent_count").agg(
        {
            "specialization_index": ["mean", "std"],
            "retrieval_efficiency": ["mean", "std"],
        }
    ).reset_index()
    
    # Flatten column names
    summary.columns = [
        "agent_count",
        "spec_mean",
        "spec_std",
        "retrieval_mean",
        "retrieval_std",
    ]
    
    # Sort by agent count
    summary = summary.sort_values("agent_count")
    
    x = summary["agent_count"].values.astype(float)
    y_spec = summary["spec_mean"].values
    y_ret = summary["retrieval_mean"].values
    
    return x, y_spec, y_ret, summary


def generate_scaling_plot(
    x: np.ndarray,
    y_spec: np.ndarray,
    y_ret: np.ndarray,
    output_path: pathlib.Path,
    title: str = "Scaling of Collective Remembering Metrics",
) -> Dict[str, Any]:
    """
    Generate scaling plot with fitted power-law curves.
    
    Args:
        x: Agent counts.
        y_spec: Specialization index means.
        y_ret: Retrieval efficiency means.
        output_path: Path to save the PDF.
        title: Plot title.
        
    Returns:
        Dictionary containing fit results for both metrics.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for plotting.")
    
    # Fit power laws
    a_spec, b_spec, _, b_spec_ci, meta_spec = fit_power_law_with_ci(x, y_spec)
    a_ret, b_ret, _, b_ret_ci, meta_ret = fit_power_law_with_ci(x, y_ret)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot data points
    ax.scatter(x, y_spec, color="blue", label="Specialization Index (Observed)", zorder=5)
    ax.scatter(x, y_ret, color="red", label="Retrieval Efficiency (Observed)", zorder=5)
    
    # Generate smooth curve for fitting
    x_smooth = np.linspace(min(x), max(x), 100)
    y_spec_fit = power_law(x_smooth, a_spec, b_spec)
    y_ret_fit = power_law(x_smooth, a_ret, b_ret)
    
    ax.plot(x_smooth, y_spec_fit, "b--", label=f"Spec Fit: y = {a_spec:.2f}x^{b_spec:.2f}", alpha=0.8)
    ax.plot(x_smooth, y_ret_fit, "r--", label=f"Ret Fit: y = {a_ret:.2f}x^{b_ret:.2f}", alpha=0.8)
    
    # Add annotations
    ax.set_xlabel("Number of Agents (N)")
    ax.set_ylabel("Metric Value")
    ax.set_title(title)
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    
    # Add note about data point limitation
    note_text = (
        "NOTE: Power-law fitting with only 3 data points (N=3,5,7) is statistically fragile.\n"
        f"Observed exponents: Spec={b_spec:.3f} (95% CI: {b_spec_ci[0]:.3f}-{b_spec_ci[1]:.3f}), "
        f"Ret={b_ret:.3f} (95% CI: {b_ret_ci[0]:.3f}-{b_ret_ci[1]:.3f}).\n"
        "Compare to sublinear urban scaling (N^0.85) per Geoffrey West."
    )
    fig.text(0.5, -0.05, note_text, ha="center", fontsize=9, style="italic")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return {
        "specialization": {"a": a_spec, "b": b_spec, "ci": b_spec_ci, "meta": meta_spec},
        "retrieval": {"a": a_ret, "b": b_ret, "ci": b_ret_ci, "meta": meta_ret},
    }


def main():
    """
    Main entry point for scaling analysis.
    
    Usage:
        python -m code.analysis.scaling --input results_scaling.csv --output scaling_plot.pdf
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Scaling analysis for social memory networks")
    parser.add_argument(
        "--input",
        type=str,
        default="data/results_scaling.csv",
        help="Path to input CSV with experiment results",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/scaling_plot.pdf",
        help="Path for output PDF plot",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="3,5,7",
        help="Comma-separated list of agent counts to analyze",
    )
    
    args = parser.parse_args()
    
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output)
    agent_counts = [int(x.strip()) for x in args.agents.split(",")]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading scaling data from {input_path}...")
    try:
        x, y_spec, y_ret, summary_df = load_scaling_data(input_path, agent_counts)
    except Exception as e:
        print(f"Error loading data: {e}")
        return 1
    
    print(f"Data loaded: {len(x)} agent counts")
    print(f"Agent counts: {list(x)}")
    print(f"Spec means: {list(y_spec)}")
    print(f"Ret means: {list(y_ret)}")
    
    print(f"Generating power-law fit and plot to {output_path}...")
    try:
        results = generate_scaling_plot(x, y_spec, y_ret, output_path)
    except Exception as e:
        print(f"Error generating plot: {e}")
        return 1
    
    print("\n--- Fit Results ---")
    print(f"Specialization Index: exponent = {results['specialization']['b']:.4f} "
          f"(95% CI: {results['specialization']['ci'][0]:.4f} - {results['specialization']['ci'][1]:.4f})")
    print(f"Retrieval Efficiency: exponent = {results['retrieval']['b']:.4f} "
          f"(95% CI: {results['retrieval']['ci'][0]:.4f} - {results['retrieval']['ci'][1]:.4f})")
    
    print(f"\nPlot saved to: {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())
