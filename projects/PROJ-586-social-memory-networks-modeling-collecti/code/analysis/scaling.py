"""
Scaling analysis: fit power-law curves to metric trends vs. agent count.

This module implements power-law fitting for specialization index and retrieval
efficiency as a function of the number of agents in the collective memory system.
Based on Geoffrey West's work on scaling laws in complex systems, we test whether
collective remembering fidelity follows a power-law relationship with population size.

Power-law model: y = a * x^b
Log-log form: log(y) = log(a) + b * log(x)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
import warnings
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Project-relative imports - must match API surface
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
    Fit a power-law curve y = a * x^b using log-log linear regression.

    Parameters
    ----------
    x : np.ndarray
        Independent variable (agent counts).
    y : np.ndarray
        Dependent variable (metric values).

    Returns
    -------
    tuple
        (exponent b, intercept log(a), r_squared, p_value, std_error)
    """
    # Filter out non-positive values for log transformation
    mask = (x > 0) & (y > 0)
    x_valid = x[mask]
    y_valid = y[mask]

    if len(x_valid) < 2:
        raise ValueError("Need at least 2 valid data points for power-law fitting")

    # Log-log transformation
    log_x = np.log(x_valid)
    log_y = np.log(y_valid)

    # Linear regression on log-log data
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)

    return slope, intercept, r_value**2, p_value, std_err


def fit_power_law_with_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Fit power-law with bootstrap confidence intervals.

    Parameters
    ----------
    x : np.ndarray
        Independent variable.
    y : np.ndarray
        Dependent variable.
    n_bootstrap : int
        Number of bootstrap resamples.
    confidence_level : float
        Confidence level for intervals (default 0.95).

    Returns
    -------
    dict
        Fit parameters with confidence intervals.
    """
    # Get point estimate
    exponent, intercept, r2, p_val, std_err = fit_power_law(x, y)

    # Bootstrap for confidence intervals
    bootstrap_exponents = []
    bootstrap_intercepts = []

    n_points = len(x)
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_points, size=n_points, replace=True)
        x_resample = x[indices]
        y_resample = y[indices]

        try:
            exp_b, int_b, _, _, _ = fit_power_law(x_resample, y_resample)
            bootstrap_exponents.append(exp_b)
            bootstrap_intercepts.append(int_b)
        except ValueError:
            # Skip invalid resamples
            continue

    if len(bootstrap_exponents) < 10:
        warnings.warn("Too few valid bootstrap samples for CI estimation")
        return {
            "exponent": exponent,
            "exponent_ci_lower": None,
            "exponent_ci_upper": None,
            "intercept": intercept,
            "intercept_ci_lower": None,
            "intercept_ci_upper": None,
            "r_squared": r2,
            "p_value": p_val,
            "std_error": std_err,
            "n_bootstrap_valid": len(bootstrap_exponents)
        }

    # Compute confidence intervals
    alpha = 1 - confidence_level
    exp_lower = np.percentile(bootstrap_exponents, 100 * alpha / 2)
    exp_upper = np.percentile(bootstrap_exponents, 100 * (1 - alpha / 2))
    int_lower = np.percentile(bootstrap_intercepts, 100 * alpha / 2)
    int_upper = np.percentile(bootstrap_intercepts, 100 * (1 - alpha / 2))

    return {
        "exponent": float(exponent),
        "exponent_ci_lower": float(exp_lower),
        "exponent_ci_upper": float(exp_upper),
        "intercept": float(intercept),
        "intercept_ci_lower": float(int_lower),
        "intercept_ci_upper": float(int_upper),
        "r_squared": float(r2),
        "p_value": float(p_val),
        "std_error": float(std_err),
        "n_bootstrap_valid": len(bootstrap_exponents)
    }


def load_scaling_data(
    results_dir: pathlib.Path,
    metrics: List[str] = ["specialization_index", "retrieval_efficiency"]
) -> Dict[str, List[Tuple[int, float]]]:
    """
    Load scaling results from CSV files.

    Expects CSV files with columns: game_id, agent_count, specialization_index,
    retrieval_efficiency, context_condition

    Parameters
    ----------
    results_dir : pathlib.Path
        Directory containing results CSV files.
    metrics : List[str]
        Metrics to extract.

    Returns
    -------
    dict
        Mapping from metric name to list of (agent_count, value) tuples.
    """
    data = {metric: [] for metric in metrics}
    csv_files = list(results_dir.glob("results_*.csv"))

    if not csv_files:
        logger.log("scaling_data_warning", message=f"No results CSV files found in {results_dir}")
        return data

    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        agent_count = int(row.get('agent_count', row.get('n_agents', 0)))
                        if agent_count <= 0:
                            continue

                        for metric in metrics:
                            if metric in row:
                                try:
                                    value = float(row[metric])
                                    if not math.isnan(value) and not math.isinf(value):
                                        data[metric].append((agent_count, value))
                                except (ValueError, TypeError):
                                    continue
                    except (KeyError, ValueError):
                        continue
        except Exception as e:
            logger.log("scaling_data_load_error", file=str(csv_file), error=str(e))
            continue

    # Aggregate by agent count (average across games)
    aggregated = {metric: [] for metric in metrics}
    for metric in metrics:
        if not data[metric]:
            continue

        # Group by agent count
        by_count: Dict[int, List[float]] = {}
        for agent_count, value in data[metric]:
            if agent_count not in by_count:
                by_count[agent_count] = []
            by_count[agent_count].append(value)

        # Average per agent count
        for agent_count in sorted(by_count.keys()):
            avg_value = sum(by_count[agent_count]) / len(by_count[agent_count])
            aggregated[metric].append((agent_count, avg_value))

    return aggregated


def generate_scaling_plot(
    results: ScalingAnalysisResult,
    output_path: pathlib.Path
) -> None:
    """
    Generate a scaling plot with fitted power-law curves.

    Parameters
    ----------
    results : ScalingAnalysisResult
        Fitting results.
    output_path : pathlib.Path
        Path to save the plot.
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot specialization index
    ax1 = axes[0]
    if results.specialization_fit:
        fit = results.specialization_fit
        x = np.array(fit.x_values)
        y = np.array(fit.y_values)
        fitted_y = np.array(fit.fitted_y)

        ax1.scatter(x, y, alpha=0.7, label='Observed', s=60)
        x_smooth = np.linspace(min(x), max(x), 100)
        y_smooth = power_law(x_smooth, np.exp(fit.intercept), fit.exponent)
        ax1.plot(x_smooth, y_smooth, 'r-', linewidth=2,
                label=f'Power-law fit: y = {np.exp(fit.intercept):.3f} * x^{fit.exponent:.3f}')

        ax1.set_xlabel('Number of Agents (N)')
        ax1.set_ylabel('Specialization Index')
        ax1.set_title(f'Specialization Scaling (R² = {fit.r_squared:.3f}, p = {fit.p_value:.3f})')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Add note about limited data points
        if fit.n_points <= 3:
            note = f"Note: {fit.n_points} data points limit power-law reliability"
            ax1.text(0.02, 0.98, note, transform=ax1.transAxes, fontsize=9,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax1.set_xscale('log')
    ax1.set_yscale('log')

    # Plot retrieval efficiency
    ax2 = axes[1]
    if results.retrieval_fit:
        fit = results.retrieval_fit
        x = np.array(fit.x_values)
        y = np.array(fit.y_values)
        fitted_y = np.array(fit.fitted_y)

        ax2.scatter(x, y, alpha=0.7, label='Observed', s=60, color='green')
        x_smooth = np.linspace(min(x), max(x), 100)
        y_smooth = power_law(x_smooth, np.exp(fit.intercept), fit.exponent)
        ax2.plot(x_smooth, y_smooth, 'g-', linewidth=2,
                label=f'Power-law fit: y = {np.exp(fit.intercept):.3f} * x^{fit.exponent:.3f}')

        ax2.set_xlabel('Number of Agents (N)')
        ax2.set_ylabel('Retrieval Efficiency')
        ax2.set_title(f'Retrieval Scaling (R² = {fit.r_squared:.3f}, p = {fit.p_value:.3f})')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Add note about limited data points
        if fit.n_points <= 3:
            note = f"Note: {fit.n_points} data points limit power-law reliability"
            ax2.text(0.02, 0.98, note, transform=ax2.transAxes, fontsize=9,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax2.set_xscale('log')
    ax2.set_yscale('log')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.log("scaling_plot_saved", path=str(output_path))


def run_scaling_analysis(
    results_dir: pathlib.Path,
    output_dir: pathlib.Path
) -> ScalingAnalysisResult:
    """
    Run complete scaling analysis on experiment results.

    Parameters
    ----------
    results_dir : pathlib.Path
        Directory containing results CSV files.
    output_dir : pathlib.Path
        Directory for output files.

    Returns
    -------
    ScalingAnalysisResult
        Complete analysis results.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    data = load_scaling_data(results_dir)

    notes = []
    specialization_fit: Optional[PowerLawFitResult] = None
    retrieval_fit: Optional[PowerLawFitResult] = None

    # Fit specialization index
    if data.get("specialization_index"):
        points = data["specialization_index"]
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])

        if len(x) >= 2:
            try:
                exponent, intercept, r2, p_val, std_err = fit_power_law(x, y)

                # Compute fitted values
                fitted_y = power_law(x, np.exp(intercept), exponent)

                specialization_fit = PowerLawFitResult(
                    metric_name="specialization_index",
                    exponent=exponent,
                    intercept=intercept,
                    r_squared=r2,
                    p_value=p_val,
                    std_error=std_err,
                    n_points=len(x),
                    x_values=x.tolist(),
                    y_values=y.tolist(),
                    fitted_y=fitted_y.tolist()
                )

                if len(x) <= 3:
                    notes.append(
                        f"Specialization fit based on {len(x)} agent counts; "
                        "power-law reliability is limited with few data points."
                    )
            except ValueError as e:
                notes.append(f"Specialization fit failed: {e}")
        else:
            notes.append("Insufficient data points for specialization index fitting.")

    # Fit retrieval efficiency
    if data.get("retrieval_efficiency"):
        points = data["retrieval_efficiency"]
        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])

        if len(x) >= 2:
            try:
                exponent, intercept, r2, p_val, std_err = fit_power_law(x, y)

                # Compute fitted values
                fitted_y = power_law(x, np.exp(intercept), exponent)

                retrieval_fit = PowerLawFitResult(
                    metric_name="retrieval_efficiency",
                    exponent=exponent,
                    intercept=intercept,
                    r_squared=r2,
                    p_value=p_val,
                    std_error=std_err,
                    n_points=len(x),
                    x_values=x.tolist(),
                    y_values=y.tolist(),
                    fitted_y=fitted_y.tolist()
                )

                if len(x) <= 3:
                    notes.append(
                        f"Retrieval fit based on {len(x)} agent counts; "
                        "power-law reliability is limited with few data points."
                    )
            except ValueError as e:
                notes.append(f"Retrieval fit failed: {e}")
        else:
            notes.append("Insufficient data points for retrieval efficiency fitting.")

    results = ScalingAnalysisResult(
        specialization_fit=specialization_fit,
        retrieval_fit=retrieval_fit,
        notes=notes
    )

    # Save results as JSON
    results_path = output_dir / "scaling_analysis_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "specialization_fit": asdict(specialization_fit) if specialization_fit else None,
            "retrieval_fit": asdict(retrieval_fit) if retrieval_fit else None,
            "notes": notes
        }, f, indent=2)

    logger.log("scaling_results_saved", path=str(results_path))

    # Generate plot
    plot_path = output_dir / "scaling_plot.pdf"
    generate_scaling_plot(results, plot_path)

    return results


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Fit power-law curves to scaling analysis results"
    )
    parser.add_argument(
        "--results-dir",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory containing results CSV files"
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory for output files"
    )
    parser.add_argument(
        "--bootstrap-n",
        type=int,
        default=1000,
        help="Number of bootstrap resamples for CI estimation"
    )
    return parser


def main() -> int:
    """Main entry point for scaling analysis."""
    parser = build_parser()
    args = parser.parse_args()

    logger.log("scaling_analysis_started", results_dir=str(args.results_dir))

    try:
        results = run_scaling_analysis(args.results_dir, args.output_dir)

        # Print summary
        print("\n=== Scaling Analysis Results ===")
        if results.specialization_fit:
            print(f"\nSpecialization Index:")
            print(f"  Exponent (b): {results.specialization_fit.exponent:.4f}")
            print(f"  R-squared: {results.specialization_fit.r_squared:.4f}")
            print(f"  p-value: {results.specialization_fit.p_value:.4f}")
        else:
            print("\nSpecialization Index: No fit computed")

        if results.retrieval_fit:
            print(f"\nRetrieval Efficiency:")
            print(f"  Exponent (b): {results.retrieval_fit.exponent:.4f}")
            print(f"  R-squared: {results.retrieval_fit.r_squared:.4f}")
            print(f"  p-value: {results.retrieval_fit.p_value:.4f}")
        else:
            print("\nRetrieval Efficiency: No fit computed")

        if results.notes:
            print("\nNotes:")
            for note in results.notes:
                print(f"  - {note}")

        print(f"\nOutput saved to: {args.output_dir}")
        return 0

    except Exception as e:
        logger.log("scaling_analysis_failed", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())