"""Scaling analysis for multi-agent social memory networks.

Implements power-law fitting for specialization index and retrieval efficiency
as a function of agent count (N^beta).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PowerLawFitResult:
    """Result of a power-law fit: y = a * x^beta."""

    exponent: float  # beta
    intercept: float  # log(a)
    r_squared: float
    std_err: float
    n_points: int
    x_data: List[float] = field(default_factory=list)
    y_data: List[float] = field(default_factory=list)
    fitted_y: List[float] = field(default_factory=list)


@dataclass
class ScalingAnalysisResult:
    """Aggregated results of scaling analysis."""

    specialization_fit: Optional[PowerLawFitResult] = None
    retrieval_fit: Optional[PowerLawFitResult] = None
    agent_counts: List[int] = field(default_factory=list)
    specialization_means: List[float] = field(default_factory=list)
    retrieval_means: List[float] = field(default_factory=list)
    specialization_stds: List[float] = field(default_factory=list)
    retrieval_stds: List[float] = field(default_factory=list)


def power_law(x: float, a: float, beta: float) -> float:
    """Evaluate power law y = a * x^beta."""
    if x <= 0:
        return float("nan")
    return a * (x ** beta)


def fit_power_law(
    x_vals: List[float], y_vals: List[float]
) -> Optional[PowerLawFitResult]:
    """Fit y = a * x^beta via log-log linear regression.

    Returns None if fewer than 2 valid points or if fit fails.
    """
    if len(x_vals) < 2 or len(y_vals) < 2:
        logger.warning("fit_power_law: need at least 2 points")
        return None

    # Filter out non-positive x or non-finite y
    valid = []
    for x, y in zip(x_vals, y_vals):
        if x > 0 and math.isfinite(y):
            valid.append((x, y))

    if len(valid) < 2:
        logger.warning("fit_power_law: not enough valid points after filtering")
        return None

    xs = [p[0] for p in valid]
    ys = [p[1] for p in valid]

    log_x = [math.log(x) for x in xs]
    log_y = [math.log(y) for y in ys]

    # Linear regression on log-log
    n = len(log_x)
    sum_x = sum(log_x)
    sum_y = sum(log_y)
    sum_xy = sum(a * b for a, b in zip(log_x, log_y))
    sum_xx = sum(a * a for a in log_x)

    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-12:
        logger.warning("fit_power_law: singular matrix in regression")
        return None

    beta = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - beta * sum_x) / n

    # Compute R^2
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in log_y)
    ss_res = 0.0
    for lx, ly in zip(log_x, log_y):
        y_pred = intercept + beta * lx
        ss_res += (ly - y_pred) ** 2

    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Standard error of beta
    if n > 2:
        mse = ss_res / (n - 2)
        var_beta = mse / (sum_xx - (sum_x ** 2) / n)
        std_err = math.sqrt(var_beta) if var_beta > 0 else 0.0
    else:
        std_err = 0.0

    a = math.exp(intercept)

    # Fitted values in original scale
    fitted_y = [power_law(x, a, beta) for x in xs]

    return PowerLawFitResult(
        exponent=beta,
        intercept=intercept,
        r_squared=r_squared,
        std_err=std_err,
        n_points=n,
        x_data=xs,
        y_data=ys,
        fitted_y=fitted_y,
    )


def load_scaling_data(
    results_path: pathlib.Path,
) -> Dict[int, List[Dict[str, Any]]]:
    """Load experiment results and group by agent count.

    Expects CSV with columns: game_id, agent_count, specialization_index, retrieval_efficiency, ...
    """
    if not results_path.exists():
        logger.error(f"Scaling data file not found: {results_path}")
        return {}

    grouped: Dict[int, List[Dict[str, Any]]] = {}
    with results_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                agent_count = int(row["agent_count"])
            except (KeyError, ValueError):
                continue

            try:
                spec = float(row["specialization_index"])
                ret = float(row["retrieval_efficiency"])
            except (KeyError, ValueError):
                continue

            if not (math.isfinite(spec) and math.isfinite(ret)):
                continue

            grouped.setdefault(agent_count, []).append(
                {"specialization_index": spec, "retrieval_efficiency": ret}
            )

    return grouped


def aggregate_by_agent_count(
    data: Dict[int, List[Dict[str, Any]]]
) -> ScalingAnalysisResult:
    """Aggregate metrics by agent count, computing means and stds."""
    if not data:
        return ScalingAnalysisResult()

    agent_counts = sorted(data.keys())
    spec_means = []
    spec_stds = []
    ret_means = []
    ret_stds = []

    for n in agent_counts:
        rows = data[n]
        if not rows:
            continue

        specs = [r["specialization_index"] for r in rows]
        rets = [r["retrieval_efficiency"] for r in rows]

        spec_means.append(float(np.mean(specs)))
        spec_stds.append(float(np.std(specs, ddof=1)) if len(specs) > 1 else 0.0)
        ret_means.append(float(np.mean(rets)))
        ret_stds.append(float(np.std(rets, ddof=1)) if len(rets) > 1 else 0.0)

    return ScalingAnalysisResult(
        agent_counts=agent_counts,
        specialization_means=spec_means,
        specialization_stds=spec_stds,
        retrieval_means=ret_means,
        retrieval_stds=ret_stds,
    )


def run_scaling_analysis(
    results_path: pathlib.Path,
    output_dir: Optional[pathlib.Path] = None,
) -> ScalingAnalysisResult:
    """Run full scaling analysis: load, aggregate, fit power laws.

    Writes JSON summary to output_dir if provided.
    """
    data = load_scaling_data(results_path)
    agg = aggregate_by_agent_count(data)

    # Fit power laws
    if agg.agent_counts and agg.specialization_means:
        agg.specialization_fit = fit_power_law(
            [float(n) for n in agg.agent_counts], agg.specialization_means
        )

    if agg.agent_counts and agg.retrieval_means:
        agg.retrieval_fit = fit_power_law(
            [float(n) for n in agg.agent_counts], agg.retrieval_means
        )

    # Write summary JSON
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "scaling_analysis_summary.json"

        summary: Dict[str, Any] = {
            "agent_counts": agg.agent_counts,
            "specialization": {
                "means": agg.specialization_means,
                "stds": agg.specialization_stds,
            },
            "retrieval": {
                "means": agg.retrieval_means,
                "stds": agg.retrieval_stds,
            },
            "specialization_fit": (
                {
                    "exponent": agg.specialization_fit.exponent,
                    "intercept": agg.specialization_fit.intercept,
                    "r_squared": agg.specialization_fit.r_squared,
                    "std_err": agg.specialization_fit.std_err,
                    "n_points": agg.specialization_fit.n_points,
                }
                if agg.specialization_fit
                else None
            ),
            "retrieval_fit": (
                {
                    "exponent": agg.retrieval_fit.exponent,
                    "intercept": agg.retrieval_fit.intercept,
                    "r_squared": agg.retrieval_fit.r_squared,
                    "std_err": agg.retrieval_fit.std_err,
                    "n_points": agg.retrieval_fit.n_points,
                }
                if agg.retrieval_fit
                else None
            ),
        }

        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Scaling summary written to {summary_path}")

    return agg


def generate_scaling_plot(
    result: ScalingAnalysisResult,
    output_path: pathlib.Path,
) -> None:
    """Generate a scaling plot with fitted power-law curves.

    Writes a PDF with specialization and retrieval vs. agent count.
    Includes a note that 3 data points limit power-law reliability.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib not available; cannot generate plot")
        raise

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 6))

    agent_counts = result.agent_counts
    if not agent_counts:
        logger.warning("No agent counts to plot")
        plt.close(fig)
        return

    x = np.array(agent_counts, dtype=float)

    # Plot specialization
    if result.specialization_means:
        ax.errorbar(
            x,
            result.specialization_means,
            yerr=result.specialization_stds,
            fmt="o-",
            label="Specialization Index",
            capsize=4,
        )
        if result.specialization_fit:
            x_fit = np.linspace(min(x), max(x), 100)
            y_fit = [
                power_law(xx, math.exp(result.specialization_fit.intercept), result.specialization_fit.exponent)
                for xx in x_fit
            ]
            ax.plot(x_fit, y_fit, ":", label=f"Specialization fit (β={result.specialization_fit.exponent:.3f})")

    # Plot retrieval (secondary axis)
    if result.retrieval_means:
        ax2 = ax.twinx()
        ax2.errorbar(
            x,
            result.retrieval_means,
            yerr=result.retrieval_stds,
            fmt="s-",
            color="tab:orange",
            label="Retrieval Efficiency",
            capsize=4,
        )
        if result.retrieval_fit:
            x_fit = np.linspace(min(x), max(x), 100)
            y_fit = [
                power_law(xx, math.exp(result.retrieval_fit.intercept), result.retrieval_fit.exponent)
                for xx in x_fit
            ]
            ax2.plot(x_fit, y_fit, ":.", color="tab:orange",
                     label=f"Retrieval fit (β={result.retrieval_fit.exponent:.3f})")

    ax.set_xlabel("Number of Agents (N)")
    ax.set_ylabel("Specialization Index")
    if result.retrieval_means:
        ax2.set_ylabel("Retrieval Efficiency")

    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels() if result.retrieval_means else ([], [])
    ax.legend(lines1 + lines2, labels1 + labels2, loc="best")

    # Add note about limited data points
    note = "Note: 3 data points limit power-law reliability"
    fig.text(
        0.5,
        -0.02,
        note,
        ha="center",
        fontsize=9,
        style="italic",
        bbox=dict(facecolor="white", alpha=0.7, boxstyle="round,pad=0.3"),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info(f"Scaling plot written to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run scaling analysis and fit power laws for multi-agent memory metrics."
    )
    parser.add_argument(
        "--results",
        type=pathlib.Path,
        required=True,
        help="Path to CSV with experiment results (game_id, agent_count, specialization_index, retrieval_efficiency, ...)",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory for output JSON and plot",
    )
    parser.add_argument(
        "--plot",
        type=pathlib.Path,
        default=pathlib.Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf"),
        help="Path for the scaling plot PDF",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.results.exists():
        logger.error(f"Results file not found: {args.results}")
        return

    result = run_scaling_analysis(args.results, args.output_dir)

    generate_scaling_plot(result, args.plot)

    # Print summary to stdout
    print("Scaling Analysis Summary")
    print("-" * 40)
    print(f"Agent counts: {result.agent_counts}")
    if result.specialization_fit:
        print(f"Specialization exponent (β): {result.specialization_fit.exponent:.4f} ± {result.specialization_fit.std_err:.4f}")
        print(f"Specialization R²: {result.specialization_fit.r_squared:.4f}")
    else:
        print("Specialization fit: not computed (insufficient data)")

    if result.retrieval_fit:
        print(f"Retrieval exponent (β): {result.retrieval_fit.exponent:.4f} ± {result.retrieval_fit.std_err:.4f}")
        print(f"Retrieval R²: {result.retrieval_fit.r_squared:.4f}")
    else:
        print("Retrieval fit: not computed (insufficient data)")

    print(f"\nOutputs written to {args.output_dir}")
    print(f"Plot written to {args.plot}")


if __name__ == "__main__":
    main()