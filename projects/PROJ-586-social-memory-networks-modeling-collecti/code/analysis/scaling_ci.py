"""Scaling confidence intervals via bootstrapping.

Computes 95% confidence intervals for power-law exponents fitted to
specialization index and retrieval efficiency vs. agent count.
Uses 1000 bootstrap resamples.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import the existing power-law fitting function from the shared analysis module
from analysis.scaling import fit_power_law, load_scaling_data

# Ensure reproducibility
np.random.seed(42)


def load_scaling_results_for_bootstrap(
    results_dir: Path,
) -> Optional[pd.DataFrame]:
    """Load scaling results from CSV files in the results directory.

    Expects files like:
      - scaling_results_agents_3.csv
      - scaling_results_agents_5.csv
      - scaling_results_agents_7.csv

    Returns a long-format DataFrame with columns:
      agent_count, specialization_index, retrieval_efficiency
    """
    files = list(results_dir.glob("scaling_results_agents_*.csv"))
    if not files:
        warnings.warn(f"No scaling result files found in {results_dir}")
        return None

    dfs = []
    for f in files:
        # Parse agent count from filename
        try:
            agent_count = int(f.stem.split("_")[-1])
        except (IndexError, ValueError):
            warnings.warn(f"Could not parse agent count from {f.name}, skipping")
            continue

        df = pd.read_csv(f)
        if "specialization_index" in df.columns and "retrieval_efficiency" in df.columns:
            # Take the mean across games for this agent count
            row = {
                "agent_count": agent_count,
                "specialization_index": df["specialization_index"].mean(),
                "retrieval_efficiency": df["retrieval_efficiency"].mean(),
            }
            dfs.append(row)
        else:
            warnings.warn(f"Missing expected columns in {f.name}, skipping")

    if not dfs:
        return None

    return pd.DataFrame(dfs)


def bootstrap_power_law_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_resamples: int = 1000,
    metric_name: str = "metric",
) -> Dict[str, Any]:
    """Bootstrap confidence intervals for power-law exponent.

    Fits y ~ a * x^b on log-log scale, then bootstraps the exponent b.

    Args:
        x: Independent variable (agent counts)
        y: Dependent variable (metric values)
        n_resamples: Number of bootstrap resamples
        metric_name: Name of the metric for labeling

    Returns:
        Dict with 'exponent', 'exponent_ci_lower', 'exponent_ci_upper',
        'r_squared', and 'resample_exponents'.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Need at least 2 data points for fitting")

    # Filter out zeros/nans for log transform
    mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 2:
        raise ValueError("Not enough valid data points after filtering")

    # Original fit
    try:
        exp_orig, r2_orig = fit_power_law(x_clean, y_clean)
    except Exception as e:
        warnings.warn(f"Power-law fit failed: {e}")
        return {
            "exponent": None,
            "exponent_ci_lower": None,
            "exponent_ci_upper": None,
            "r_squared": None,
            "resample_exponents": [],
            "error": str(e),
        }

    # Bootstrap
    resample_exponents = []
    for _ in range(n_resamples):
        # Resample with replacement
        indices = np.random.choice(len(x_clean), size=len(x_clean), replace=True)
        x_boot = x_clean[indices]
        y_boot = y_clean[indices]

        try:
            exp_boot, _ = fit_power_law(x_boot, y_boot)
            if np.isfinite(exp_boot):
                resample_exponents.append(exp_boot)
        except Exception:
            # Skip failed fits
            continue

    if not resample_exponents:
        warnings.warn("No successful bootstrap fits")
        return {
            "exponent": exp_orig,
            "exponent_ci_lower": None,
            "exponent_ci_upper": None,
            "r_squared": r2_orig,
            "resample_exponents": [],
        }

    resample_exponents = np.array(resample_exponents)
    ci_lower = float(np.percentile(resample_exponents, 2.5))
    ci_upper = float(np.percentile(resample_exponents, 97.5))

    return {
        "exponent": float(exp_orig),
        "exponent_ci_lower": ci_lower,
        "exponent_ci_upper": ci_upper,
        "r_squared": float(r2_orig),
        "resample_exponents": resample_exponents.tolist(),
    }


def run_scaling_ci_analysis(
    results_dir: Path,
    output_path: Path,
    n_resamples: int = 1000,
) -> Dict[str, Any]:
    """Run full confidence interval analysis for scaling metrics.

    Args:
        results_dir: Directory containing scaling result CSV files
        output_path: Path to write the JSON output
        n_resamples: Number of bootstrap resamples

    Returns:
        Dict with results for both metrics.
    """
    # Load data
    df = load_scaling_results_for_bootstrap(results_dir)
    if df is None or len(df) < 2:
        raise ValueError(
            f"Insufficient scaling data in {results_dir}. "
            "Need at least 2 agent counts with valid metrics."
        )

    x = df["agent_count"].values
    y_spec = df["specialization_index"].values
    y_ret = df["retrieval_efficiency"].values

    # Compute CIs
    ci_spec = bootstrap_power_law_ci(x, y_spec, n_resamples, "specialization_index")
    ci_ret = bootstrap_power_law_ci(x, y_ret, n_resamples, "retrieval_efficiency")

    result = {
        "metadata": {
            "n_resamples": n_resamples,
            "n_agent_counts": len(x),
            "agent_counts": x.tolist(),
            "note": "3 data points limit power-law reliability",
        },
        "specialization_index": ci_spec,
        "retrieval_efficiency": ci_ret,
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Compute 95% CI for scaling exponents via bootstrapping"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Directory containing scaling result CSV files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--n-resamples",
        type=int,
        default=1000,
        help="Number of bootstrap resamples",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_path = Path(args.output)

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_scaling_ci_analysis(
            results_dir=results_dir,
            output_path=output_path,
            n_resamples=args.n_resamples,
        )
        print(f"Confidence intervals written to: {output_path}")
        print(
            f"Specialization exponent: {result['specialization_index']['exponent']:.4f} "
            f"[{result['specialization_index']['exponent_ci_lower']:.4f}, "
            f"{result['specialization_index']['exponent_ci_upper']:.4f}]"
        )
        print(
            f"Retrieval exponent: {result['retrieval_efficiency']['exponent']:.4f} "
            f"[{result['retrieval_efficiency']['exponent_ci_lower']:.4f}, "
            f"{result['retrieval_efficiency']['exponent_ci_upper']:.4f}]"
        )
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
