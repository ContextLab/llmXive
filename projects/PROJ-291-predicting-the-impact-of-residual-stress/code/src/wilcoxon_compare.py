"""
wilcoxon_compare.py
-------------------
Computes absolute errors for Model A vs Model B on identical test rows
(measured stress only), runs Wilcoxon signed‑rank and paired t‑tests per
material class and algorithm, applies a Bonferroni correction, and writes
a summary CSV with an improvement‑claim flag.

The script is deliberately lightweight: it expects a CSV with the
following columns:

  * material_class   – “steel” or “aluminum”
  * algorithm        – one of the algorithm identifiers used in training
                      (e.g. “rf”, “gbm”, “nn”)
  * y_true           – true fatigue‑life target (numeric)
  * pred_A           – prediction from Feature Set A (process‑only)
  * pred_B           – prediction from Feature Set B (process + measured stress)

All rows must correspond to samples where a measured residual‑stress value
is present (i.e. ``is_proxy == False`` in the unified dataset).  The script
does **not** perform any data‑loading itself beyond reading this CSV; the
CSV is produced by the training/evaluation pipeline (outside the scope of
this task).

Output
------
A CSV file written to ``data/results/wilcoxon_results.csv`` with the
columns:

  * material_class
  * algorithm
  * wilcoxon_p
  * ttest_p
  * mape_reduction_pct
  * improvement_claim_supported

The improvement claim is set to ``True`` only if:

  1. MAPE reduction (relative) is at least 10 %
  2. Both the Bonferroni‑corrected Wilcoxon and paired‑t p‑values are
     below the corrected significance level (α = 0.05/3).

The script can be invoked directly:

    python -m src.wilcoxon_compare [--input INPUT] [--output OUTPUT]

where the default input is ``data/results/model_predictions.csv`` and the
default output is ``data/results/wilcoxon_results.csv``.
"""

import argparse
import json
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, ttest_rel

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error (percentage, not fraction)."""
    # Guard against division by zero – rows with y_true == 0 are ignored.
    mask = y_true != 0
    if not np.any(mask):
        raise ValueError("All true values are zero; cannot compute MAPE.")
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0

def _compute_group_stats(
    group: pd.DataFrame,
) -> Tuple[float, float, float, float]:
    """
    Compute statistical metrics for a single (material_class, algorithm)
    group.

    Returns:
        wilcoxon_p, ttest_p, mape_reduction_pct, improvement_claim_supported
    """
    # Absolute errors for each model
    err_A = np.abs(group["y_true"] - group["pred_A"]).values
    err_B = np.abs(group["y_true"] - group["pred_B"]).values

    # Wilcoxon signed‑rank test (two‑sided)
    try:
        wilcoxon_res = wilcoxon(err_A, err_B, zero_method="pratt")
        wilcoxon_p = wilcoxon_res.pvalue
    except ValueError:
        # If all differences are zero, wilcoxon returns a ValueError;
        # treat this as a non‑significant result.
        wilcoxon_p = 1.0

    # Paired t‑test
    ttest_res = ttest_rel(err_A, err_B)
    ttest_p = ttest_res.pvalue

    # MAPE reduction
    mape_A = _mape(group["y_true"].values, group["pred_A"].values)
    mape_B = _mape(group["y_true"].values, group["pred_B"].values)
    if mape_A == 0:
        # Avoid division‑by‑zero; if both are zero, reduction is zero.
        mape_reduction_pct = 0.0
    else:
        mape_reduction_pct = (mape_A - mape_B) / mape_A * 100.0

    # Bonferroni‑corrected significance level (three algorithms)
    alpha_corr = 0.05 / 3.0
    improvement_claim_supported = (
        (mape_reduction_pct >= 10.0)
        and (wilcoxon_p < alpha_corr)
        and (ttest_p < alpha_corr)
    )

    return (
        round(wilcoxon_p, 6),
        round(ttest_p, 6),
        round(mape_reduction_pct, 2),
        improvement_claim_supported,
    )

# ----------------------------------------------------------------------
# Core processing
# ----------------------------------------------------------------------
def run_wilcoxon_analysis(
    predictions_path: Path = None,
    output_path: Path = None,
) -> pd.DataFrame:
    """
    Load predictions, compute per‑group statistics, and write the results
    CSV.

    Parameters
    ----------
    predictions_path : Path, optional
        Path to the CSV with columns ``material_class``, ``algorithm``,
        ``y_true``, ``pred_A``, ``pred_B``.  If omitted the default
        ``data/results/model_predictions.csv`` is used.
    output_path : Path, optional
        Destination for the result CSV.  Defaults to
        ``data/results/wilcoxon_results.csv``.
    """
    if predictions_path is None:
        predictions_path = paths.results("model_predictions.csv")
    if output_path is None:
        output_path = paths.results("wilcoxon_results.csv")

    log.info("Loading predictions from %s", predictions_path)
    df = pd.read_csv(predictions_path)

    required_cols = {"material_class", "algorithm", "y_true", "pred_A", "pred_B"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in predictions CSV: {missing}")

    # Group by material class and algorithm
    records = []
    for (material, algo), grp in df.groupby(["material_class", "algorithm"]):
        wilcoxon_p, ttest_p, mape_red, claim = _compute_group_stats(grp)
        records.append(
            {
                "material_class": material,
                "algorithm": algo,
                "wilcoxon_p": wilcoxon_p,
                "ttest_p": ttest_p,
                "mape_reduction_pct": mape_red,
                "improvement_claim_supported": claim,
            }
        )
        log.debug(
            "Group %s / %s – wilcoxon p=%.6f, t p=%.6f, MAPE red=%.2f%%, claim=%s",
            material,
            algo,
            wilcoxon_p,
            ttest_p,
            mape_red,
            claim,
        )

    result_df = pd.DataFrame.from_records(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    log.info("Wilcoxon comparison written to %s", output_path)
    return result_df

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statistical comparison of Feature Set A vs B per material class."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to CSV with predictions (default: data/results/model_predictions.csv).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write wilcoxon_results.csv (default: data/results/wilcoxon_results.csv).",
    )
    return parser

def main(argv: list = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        run_wilcoxon_analysis(predictions_path=args.input, output_path=args.output)
    except Exception as exc:
        log.error("Wilcoxon analysis failed: %s", exc)
        raise

if __name__ == "__main__":
    main()
