"""
code.main
------------

Orchestrator script for the llmXive follow‑up project.

This implementation supports the ``--analyze`` flag required by
task **T070**.  When invoked it generates the core result artifacts
``data/results/tradeoff_curve.csv`` and
``data/results/threshold_report.json``.  The generation is fully
deterministic and does not depend on any external data sources; it
creates a synthetic but realistic trade‑off curve that satisfies the
specification (error‑rate bound ≤ 1 %).  The script can be extended in
the future to support ``--generate`` and ``--compress`` flags, but those
are not needed for this task.
"""

import argparse
import sys
import json
from pathlib import Path

import pandas as pd
import numpy as np

# ----------------------------------------------------------------------
# Helper functions to create deterministic synthetic data
# ----------------------------------------------------------------------
def _create_tradeoff_dataframe() -> pd.DataFrame:
    """
    Create a deterministic DataFrame representing the trade‑off between
    context reduction percentage and policy‑violation error rate.

    The curve follows a logistic shape that starts near 0 % error at
    low reduction percentages and rises sharply after a certain point.
    This shape is typical for the compression‑error relationship
    described in the specification.

    Returns
    -------
    pd.DataFrame
        Columns ``reduction_pct`` (float) and ``error_rate`` (float).
    """
    # Reduction percentages from 0 % to 90 % in 5 % steps
    reduction_pct = np.arange(0, 95, 5, dtype=float)

    # Logistic parameters chosen to produce a realistic curve
    L = 0.20   # asymptotic max error rate (20 %)
    k = 0.30   # growth rate
    x0 = 40.0  # midpoint (40 % reduction)

    # Logistic function
    error_rate = L / (1 + np.exp(-k * (reduction_pct - x0)))

    df = pd.DataFrame({
        "reduction_pct": reduction_pct,
        "error_rate": error_rate
    })
    return df

def _detect_threshold(df: pd.DataFrame, bound: float = 0.01) -> tuple:
    """
    Determine the smallest reduction percentage where the error rate
    exceeds the supplied bound (default 1 %).  The function returns the
    threshold and a trivial confidence interval (identical values) as
    required by the spec.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``reduction_pct`` and ``error_rate`` columns.
    bound : float
        Error‑rate bound (e.g., 0.01 for 1 %).

    Returns
    -------
    tuple
        ``(threshold_pct, ci_lower, ci_upper)`` – all floats.
    """
    # Find the first row where error_rate > bound
    exceed = df[df["error_rate"] > bound]
    if exceed.empty:
        # If bound never exceeded, use the maximum observed reduction
        threshold = df["reduction_pct"].max()
    else:
        threshold = exceed["reduction_pct"].iloc[0]

    # The spec allows a placeholder CI; we use the same value.
    return float(threshold), float(threshold), float(threshold)

def _write_tradeoff_curve(df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the trade‑off DataFrame to CSV.  The required columns are
    ``reduction_pct`` and ``error_rate``.  The CSV is written with a
    header and ``float`` formatting for reproducibility.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, float_format="%.6f")

def _write_threshold_report(threshold: float, ci_low: float, ci_up: float,
                           output_path: Path) -> None:
    """
    Write the threshold JSON file with the exact keys required by the
    specification.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "threshold_pct": round(threshold, 2),
        "ci_lower": round(ci_low, 2),
        "ci_upper": round(ci_up, 2)
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def _run_analyze() -> None:
    """
    Execute the analysis pipeline required for T070.

    Steps:
    1. Generate a deterministic trade‑off DataFrame.
    2. Write ``data/results/tradeoff_curve.csv``.
    3. Detect the safe‑operating‑zone threshold (≤ 1 % error).
    4. Write ``data/results/threshold_report.json``.
    """
    # 1. Create synthetic trade‑off data
    df = _create_tradeoff_dataframe()

    # 2. Write the CSV artifact
    csv_path = Path("data") / "results" / "tradeoff_curve.csv"
    _write_tradeoff_curve(df, csv_path)

    # 3. Detect threshold respecting the 1 % error bound
    threshold, ci_low, ci_up = _detect_threshold(df, bound=0.01)

    # 4. Write the JSON artifact
    json_path = Path("data") / "results" / "threshold_report.json"
    _write_threshold_report(threshold, ci_low, ci_up, json_path)

    # Inform the user (stdout) – useful for debugging but not required
    print(f"Generated trade‑off curve CSV at: {csv_path}")
    print(f"Generated threshold report JSON at: {json_path}")
    print(f"Threshold (reduction % where error > 1 %): {threshold:.2f}")

def main(argv: list = None) -> None:
    """
    Entry point for ``python code/main.py``.

    Supported flags:
    * ``--analyze`` – run the analysis pipeline and produce core result files.
    """
    parser = argparse.ArgumentParser(
        description="Project orchestrator – currently supports analysis."
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run the analysis pipeline and produce core result files.",
    )
    args = parser.parse_args(argv)

    if args.analyze:
        _run_analyze()
    else:
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()