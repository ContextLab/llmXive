"""Scaling analysis for multi-agent social memory networks.

Implements power-law fitting for metric trends vs. agent count.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PowerLawFitResult:
    """Result of a power-law fit: y = a * x^b."""
    exponent: float
    coefficient: float
    r_squared: float
    std_err_exponent: Optional[float] = None
    std_err_coefficient: Optional[float] = None


@dataclass
class ScalingAnalysisResult:
    """Full scaling analysis results."""
    agent_counts: List[int]
    specialization_means: List[float]
    specialization_stds: List[float]
    retrieval_means: List[float]
    retrieval_stds: List[float]
    specialization_fit: Optional[PowerLawFitResult] = None
    retrieval_fit: Optional[PowerLawFitResult] = None
    raw_data_path: Optional[str] = None


def power_law(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """Compute y = a * x^b."""
    return a * np.power(x, b)


def fit_power_law(
    x: np.ndarray,
    y: np.ndarray,
    min_x: float = 1.0,
) -> Optional[PowerLawFitResult]:
    """Fit a power-law model y = a * x^b using log-log linear regression.

    Args:
        x: Independent variable (agent counts).
        y: Dependent variable (metric values).
        min_x: Minimum x value to include (filter out zeros/negatives).

    Returns:
        PowerLawFitResult if fit succeeds, None otherwise.
    """
    if len(x) < 2:
        logger.log("fit_power_law_skip", reason="insufficient_data_points")
        return None

    # Filter out non-positive values
    mask = (x > 0) & (y > 0)
    x_filtered = x[mask]
    y_filtered = y[mask]

    if len(x_filtered) < 2:
        logger.log("fit_power_law_skip", reason="no_valid_points_after_filter")
        return None

    # Log-transform
    log_x = np.log(x_filtered)
    log_y = np.log(y_filtered)

    # Linear regression on log-log
    n = len(log_x)
    sum_x = np.sum(log_x)
    sum_y = np.sum(log_y)
    sum_xy = np.sum(log_x * log_y)
    sum_x2 = np.sum(log_x ** 2)

    denom = n * sum_x2 - sum_x ** 2
    if abs(denom) < 1e-10:
        logger.log("fit_power_law_skip", reason="singular_matrix")
        return None

    # Slope (exponent) and intercept
    b = (n * sum_xy - sum_x * sum_y) / denom
    a = (sum_y - b * sum_x) / n

    # R-squared
    y_pred = a + b * log_x
    ss_res = np.sum((log_y - y_pred) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Standard errors (simplified)
    std_err_b = None
    std_err_a = None
    if n > 2 and ss_res > 0:
        mse = ss_res / (n - 2)
        std_err_b = math.sqrt(mse / sum((log_x - np.mean(log_x)) ** 2))
        std_err_a = math.sqrt(mse * (1/n + sum_x**2 / denom))

    return PowerLawFitResult(
        exponent=float(b),
        coefficient=float(math.exp(a)),
        r_squared=float(r_squared),
        std_err_exponent=std_err_b,
        std_err_coefficient=std_err_a,
    )


def load_scaling_data(
    csv_path: pathlib.Path,
) -> Tuple[List[int], List[float], List[float], List[float], List[float]]:
    """Load scaling data from a CSV file.

    Expected columns: agent_count, specialization_index, retrieval_efficiency
    (and optionally game_id, context_condition, etc.)

    Returns:
        Tuple of (agent_counts, spec_means, spec_stds, ret_means, ret_stds)
        aggregated by agent_count.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Scaling data file not found: {csv_path}")

    agent_data: Dict[int, List[Tuple[float, float]]] = {}

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                agent_count = int(row["agent_count"])
                spec_idx = float(row["specialization_index"])
                ret_eff = float(row["retrieval_efficiency"])

                if agent_count not in agent_data:
                    agent_data[agent_count] = []
                agent_data[agent_count].append((spec_idx, ret_eff))
            except (KeyError, ValueError) as e:
                logger.log("load_scaling_data_skip_row", reason=str(e))
                continue

    if not agent_data:
        raise ValueError("No valid data rows found in scaling CSV")

    # Aggregate by agent count
    agent_counts = sorted(agent_data.keys())
    spec_means = []
    spec_stds = []
    ret_means = []
    ret_stds = []

    for ac in agent_counts:
        values = agent_data[ac]
        specs = [v[0] for v in values]
        rets = [v[1] for v in values]

        spec_means.append(float(np.mean(specs)))
        spec_stds.append(float(np.std(specs, ddof=1)) if len(specs) > 1 else 0.0)
        ret_means.append(float(np.mean(rets)))
        ret_stds.append(float(np.std(rets, ddof=1)) if len(rets) > 1 else 0.0)

    return agent_counts, spec_means, spec_stds, ret_means, ret_stds


def aggregate_by_agent_count(
    raw_csv_path: pathlib.Path,
) -> ScalingAnalysisResult:
    """Aggregate raw game results by agent count.

    Args:
        raw_csv_path: Path to the raw results CSV (e.g., results_scaling_raw.csv)

    Returns:
        ScalingAnalysisResult with aggregated means/stds.
    """
    (
        agent_counts,
        spec_means,
        spec_stds,
        ret_means,
        ret_stds,
    ) = load_scaling_data(raw_csv_path)

    # Fit power laws
    x_arr = np.array(agent_counts, dtype=float)
    y_spec = np.array(spec_means, dtype=float)
    y_ret = np.array(ret_means, dtype=float)

    spec_fit = fit_power_law(x_arr, y_spec)
    ret_fit = fit_power_law(x_arr, y_ret)

    return ScalingAnalysisResult(
        agent_counts=agent_counts,
        specialization_means=spec_means,
        specialization_stds=spec_stds,
        retrieval_means=ret_means,
        retrieval_stds=ret_stds,
        specialization_fit=spec_fit,
        retrieval_fit=ret_fit,
        raw_data_path=str(raw_csv_path),
    )


def run_scaling_analysis(
    input_path: pathlib.Path,
    output_path: pathlib.Path,
) -> ScalingAnalysisResult:
    """Run full scaling analysis and write results to JSON.

    Args:
        input_path: Path to raw scaling data CSV.
        output_path: Path to write JSON results.

    Returns:
        ScalingAnalysisResult.
    """
    result = aggregate_by_agent_count(input_path)

    # Prepare output dict
    output_dict: Dict[str, Any] = {
        "input_file": result.raw_data_path,
        "agent_counts": result.agent_counts,
        "specialization": {
            "means": result.specialization_means,
            "stds": result.specialization_stds,
        },
        "retrieval": {
            "means": result.retrieval_means,
            "stds": result.retrieval_stds,
        },
        "power_law_fits": {
            "specialization": (
                {
                    "exponent": result.specialization_fit.exponent,
                    "coefficient": result.specialization_fit.coefficient,
                    "r_squared": result.specialization_fit.r_squared,
                    "std_err_exponent": result.specialization_fit.std_err_exponent,
                    "std_err_coefficient": result.specialization_fit.std_err_coefficient,
                }
                if result.specialization_fit
                else None
            ),
            "retrieval": (
                {
                    "exponent": result.retrieval_fit.exponent,
                    "coefficient": result.retrieval_fit.coefficient,
                    "r_squared": result.retrieval_fit.r_squared,
                    "std_err_exponent": result.retrieval_fit.std_err_exponent,
                    "std_err_coefficient": result.retrieval_fit.std_err_coefficient,
                }
                if result.retrieval_fit
                else None
            ),
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2)

    logger.log(
        "scaling_analysis_complete",
        input_file=str(input_path),
        output_file=str(output_path),
        agent_count=len(result.agent_counts),
    )

    return result


def generate_scaling_plot(
    result: ScalingAnalysisResult,
    output_path: pathlib.Path,
) -> None:
    """Generate a scaling plot with fitted power-law curves.

    Args:
        result: ScalingAnalysisResult with fit results.
        output_path: Path to write the PDF plot.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise RuntimeError(
            "matplotlib is required for plot generation. Install with: pip install matplotlib"
        ) from e

    if len(result.agent_counts) < 2:
        logger.log(
            "generate_scaling_plot_skip",
            reason="insufficient_data_points_for_plot",
            agent_count=len(result.agent_counts),
        )
        # Still create a minimal PDF with a note
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(
            0.5, 0.5,
            "Insufficient data points for scaling plot (need >= 2 agent counts)",
            ha="center", va="center", transform=ax.transAxes, fontsize=12
        )
        ax.set_title("Scaling Analysis")
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    x = np.array(result.agent_counts, dtype=float)
    y_spec = np.array(result.specialization_means, dtype=float)
    y_ret = np.array(result.retrieval_means, dtype=float)

    # Plot specialization
    ax1.errorbar(
        x, y_spec,
        yerr=result.specialization_stds,
        fmt="o-", capsize=5, label="Specialization Index"
    )
    if result.specialization_fit:
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = result.specialization_fit.coefficient * np.power(x_fit, result.specialization_fit.exponent)
        ax1.plot(x_fit, y_fit, "r--", label=f"Fit: y = {result.specialization_fit.coefficient:.3f} * x^{result.specialization_fit.exponent:.3f}")
        ax1.text(
            0.05, 0.95,
            f"R² = {result.specialization_fit.r_squared:.3f}",
            transform=ax1.transAxes, fontsize=10, verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        )
    ax1.set_xlabel("Number of Agents")
    ax1.set_ylabel("Specialization Index")
    ax1.set_title("Specialization vs. Agent Count")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot retrieval
    ax2.errorbar(
        x, y_ret,
        yerr=result.retrieval_stds,
        fmt="s-", capsize=5, label="Retrieval Efficiency"
    )
    if result.retrieval_fit:
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = result.retrieval_fit.coefficient * np.power(x_fit, result.retrieval_fit.exponent)
        ax2.plot(x_fit, y_fit, "r--", label=f"Fit: y = {result.retrieval_fit.coefficient:.3f} * x^{result.retrieval_fit.exponent:.3f}")
        ax2.text(
            0.05, 0.95,
            f"R² = {result.retrieval_fit.r_squared:.3f}",
            transform=ax2.transAxes, fontsize=10, verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        )
    ax2.set_xlabel("Number of Agents")
    ax2.set_ylabel("Retrieval Efficiency")
    ax2.set_title("Retrieval Efficiency vs. Agent Count")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add note about data points
    fig.suptitle(
        "Scaling Analysis: Collective Remembering in Multi-Agent Networks",
        fontsize=14
    )
    fig.text(
        0.5, 0.02,
        "Note: a limited number of data points limits power-law reliability",
        ha="center", fontsize=10, style="italic"
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.log(
        "scaling_plot_generated",
        output_path=str(output_path),
        agent_count=len(result.agent_counts),
    )


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for scaling analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze scaling of collective remembering metrics vs. agent count."
    )
    parser.add_argument(
        "--input",
        type=pathlib.Path,
        required=True,
        help="Path to raw scaling results CSV (e.g., results_scaling_raw.csv)",
    )
    parser.add_argument(
        "--output-json",
        type=pathlib.Path,
        default=pathlib.Path("results/scaling_analysis.json"),
        help="Path to write JSON analysis results",
    )
    parser.add_argument(
        "--output-plot",
        type=pathlib.Path,
        default=pathlib.Path("results/scaling_plot.pdf"),
        help="Path to write scaling plot (PDF)",
    )
    return parser


def main() -> None:
    """Main entry point for scaling analysis CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.input.exists():
        logger.log("main_error", reason="input_file_not_found", path=str(args.input))
        sys.exit(1)

    # Ensure output directories exist
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_plot.parent.mkdir(parents=True, exist_ok=True)

    result = run_scaling_analysis(args.input, args.output_json)
    generate_scaling_plot(result, args.output_plot)

    logger.log(
        "main_complete",
        input=str(args.input),
        json_output=str(args.output_json),
        plot_output=str(args.output_plot),
    )


if __name__ == "__main__":
    main()