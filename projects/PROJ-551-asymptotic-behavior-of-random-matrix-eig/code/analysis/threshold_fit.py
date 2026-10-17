"""
Threshold fitting script for Task T006.

This script reads the Monte‑Carlo sweep results (``mc_results.csv``), groups
the data by configuration ``(N, k, pattern_type)`` and fits a logistic
(sigmoid) model to the binary outlier flag as a function of the perturbation
norm ``theta``.  For each group a 5‑fold cross‑validation over the seed
dimension is performed: the set of seeds is split into five folds, the model
is fitted on four folds and evaluated on the held‑out fold; the fitted
critical threshold ``theta_c`` from each fold is averaged to obtain a
statistically robust estimate.  A simple 95 % confidence interval is
derived from the variability of the cross‑validated ``theta_c`` values.

The results are written to ``data/processed/threshold_statistical.json`` in
a schema‑compatible format:

{
    "generated_at": "<ISO‑8601 timestamp>",
    "threshold_estimates": [
        {
            "N": <int>,
            "k": <int>,
            "pattern_type": "<str>",
            "theta_c_statistical": <float>,
            "confidence_interval": {"lower": <float>, "upper": <float>}
        },
        ...
    ]
}

The script can be invoked directly:

    python -m code.analysis.threshold_fit

or via the CLI entry point defined in ``if __name__ == '__main__'``.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# Project utilities
from utils.config import get_project_paths, ensure_directories

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Sigmoid model
# ----------------------------------------------------------------------
def sigmoid(theta: np.ndarray, theta_c: float, slope: float) -> np.ndarray:
    """Logistic sigmoid used to model outlier probability.

    P(outlier) = 1 / (1 + exp(-slope * (theta - theta_c)))
    """
    return 1.0 / (1.0 + np.exp(-slope * (theta - theta_c)))


# ----------------------------------------------------------------------
# Helper: fit a sigmoid to (theta, outlier_flag) data
# ----------------------------------------------------------------------
def _fit_sigmoid(
    theta: np.ndarray, outlier_flag: np.ndarray
) -> Tuple[float, float]:
    """Fit the sigmoid model and return (theta_c, slope).

    Raises
    ------
    RuntimeError
        If curve fitting fails.
    """
    # Ensure inputs are 1‑D float arrays
    theta = np.asarray(theta, dtype=float).ravel()
    outlier_flag = np.asarray(outlier_flag, dtype=float).ravel()

    if theta.size < 2:
        raise ValueError("At least two data points are required for fitting.")

    # Heuristic initial guess: theta where probability ≈ 0.5
    # and a moderate slope.
    try:
        prob = outlier_flag
        mid_idx = np.argmin(np.abs(prob - 0.5))
        theta_c_init = float(theta[mid_idx])
    except Exception:
        theta_c_init = float(np.median(theta))

    slope_init = 1.0  # default slope

    p0 = (theta_c_init, slope_init)

    try:
        popt, _ = curve_fit(
            sigmoid,
            theta,
            outlier_flag,
            p0=p0,
            bounds=([0.0, -np.inf], [np.inf, np.inf]),
            maxfev=5000,
        )
        theta_c, slope = popt
        return float(theta_c), float(slope)
    except Exception as exc:
        raise RuntimeError(f"Curve fitting failed: {exc}") from exc


# ----------------------------------------------------------------------
# Cross‑validation over seeds
# ----------------------------------------------------------------------
def _cross_validate_group(df_group: pd.DataFrame) -> Tuple[float, Tuple[float, float]]:
    """Perform a 5‑fold CV over the ``seed`` column.

    Returns
    -------
    mean_theta_c : float
        Mean of the fitted critical thresholds across folds.
    ci : tuple (lower, upper)
        Simple 95 % confidence interval based on the empirical standard
        deviation of the fold estimates.
    """
    seeds = sorted(df_group["seed"].unique())
    if len(seeds) < 2:
        raise ValueError("Not enough distinct seeds for cross‑validation.")

    # Split seeds into (up to) five folds, preserving order for reproducibility.
    n_folds = min(5, len(seeds))
    folds: List[List[int]] = [[] for _ in range(n_folds)]
    for idx, s in enumerate(seeds):
        folds[idx % n_folds].append(s)

    theta_c_vals: List[float] = []

    for fold_idx, holdout_seeds in enumerate(folds):
        # Training data: all rows whose seed is NOT in holdout_seeds
        train_mask = ~df_group["seed"].isin(holdout_seeds)
        train_df = df_group[train_mask]

        if train_df.empty:
            logger.debug(
                f"Fold {fold_idx + 1}/{n_folds}: no training data after hold‑out; skipping."
            )
            continue

        theta = train_df["theta"].values
        flag = train_df["outlier_flag"].astype(int).values

        try:
            theta_c, _ = _fit_sigmoid(theta, flag)
            theta_c_vals.append(theta_c)
        except RuntimeError as exc:
            logger.warning(
                f"Fold {fold_idx + 1}/{n_folds}: fitting failed for N={df_group['N'].iloc[0]}, "
                f"k={df_group['k'].iloc[0]}, pattern={df_group['pattern_type'].iloc[0]} – {exc}"
            )
            continue

    if not theta_c_vals:
        raise RuntimeError("All folds failed to produce a fit.")

    theta_c_arr = np.array(theta_c_vals)
    mean_theta_c = float(theta_c_arr.mean())
    std_theta_c = float(theta_c_arr.std(ddof=1)) if len(theta_c_vals) > 1 else 0.0

    # 95 % CI using normal approximation
    ci_half_width = 1.96 * std_theta_c / np.sqrt(len(theta_c_vals))
    lower = mean_theta_c - ci_half_width
    upper = mean_theta_c + ci_half_width
    return mean_theta_c, (float(lower), float(upper))


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def run_threshold_fitting(
    input_csv: str,
    output_json: str,
) -> Dict[str, List[Dict]]:
    """Read ``mc_results.csv``, fit per‑configuration sigmoids, and write JSON.

    Parameters
    ----------
    input_csv : str
        Path to the Monte‑Carlo sweep CSV (must contain columns
        ``N``, ``k``, ``pattern_type``, ``theta``, ``seed``, ``outlier_flag``).
    output_json : str
        Destination JSON file for the statistical threshold estimates.

    Returns
    -------
    dict
        The JSON object that was written to disk.
    """
    logger.info(f"Loading Monte‑Carlo results from {input_csv}")
    df = pd.read_csv(input_csv)

    required_cols = {"N", "k", "pattern_type", "theta", "seed", "outlier_flag"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")

    # Group by configuration (N, k, pattern_type)
    groups = df.groupby(["N", "k", "pattern_type"])

    results: List[Dict] = []

    for (N, k, pattern), group_df in groups:
        logger.info(f"Processing group N={N}, k={k}, pattern={pattern}")

        try:
            theta_c, (ci_low, ci_high) = _cross_validate_group(group_df)
        except Exception as exc:
            logger.error(
                f"Failed to obtain a statistical estimate for N={N}, k={k}, pattern={pattern}: {exc}"
            )
            continue

        results.append(
            {
                "N": int(N),
                "k": int(k),
                "pattern_type": str(pattern),
                "theta_c_statistical": theta_c,
                "confidence_interval": {"lower": ci_low, "upper": ci_high},
            }
        )

    # ------------------------------------------------------------------
    # Write JSON output
    # ------------------------------------------------------------------
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "threshold_estimates": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info(f"Statistical threshold estimates written to {output_path}")
    return payload


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fit sigmoid curves per configuration and produce statistical threshold estimates."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/processed/mc_results.csv",
        help="Path to the Monte‑Carlo results CSV (default: data/processed/mc_results.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/threshold_statistical.json",
        help="Path to write the statistical threshold JSON (default: data/processed/threshold_statistical.json)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        run_threshold_fitting(args.input, args.output)
        return 0
    except Exception as exc:
        logger.error(f"Threshold fitting terminated with an error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())