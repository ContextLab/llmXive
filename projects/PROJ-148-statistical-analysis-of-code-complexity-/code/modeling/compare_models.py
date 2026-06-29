"""
Utilities for comparing the primary and alternative models.

This module provides:
- ``compare_models``: core function that computes ROC‑AUC difference and the
  Spearman rank correlation between two importance vectors.
- ``main``: command‑line entry point that loads model output artifacts,
  invokes ``compare_models`` and asserts that the Spearman correlation meets
  the required threshold (≥ 0.7).  It also prints a concise summary and
  optionally writes the comparison metrics to a JSON file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
from scipy.stats import spearmanr

# ----------------------------------------------------------------------
# Core comparison logic (unchanged from the original implementation)
# ----------------------------------------------------------------------
def compare_models(
    primary_auc: float,
    alternative_auc: float,
    primary_importance: np.ndarray,
    alternative_importance: np.ndarray,
) -> Tuple[Dict[str, float], float]:
    """
    Compare two models.

    Returns a dictionary with ROC‑AUC difference and the Spearman rank
    correlation between the two feature‑importance rankings, as well as
    the raw correlation coefficient.

    Parameters
    ----------
    primary_auc: float
        ROC‑AUC of the primary model.
    alternative_auc: float
        ROC‑AUC of the alternative model.
    primary_importance: np.ndarray
        Importance scores from the primary model (coefficients).
    alternative_importance: np.ndarray
        Importance scores from the alternative model.

    Returns
    -------
    metrics: dict
        ``{'auc_diff': float, 'spearman_corr': float}``
    spearman_r: float
        The raw Spearman correlation coefficient.
    """
    auc_diff = abs(primary_auc - alternative_auc)

    # Rank the absolute values to obtain importance rankings
    rank_primary = np.abs(primary_importance)
    rank_alternative = np.abs(alternative_importance)

    spearman_r, _ = spearmanr(rank_primary, rank_alternative)

    metrics = {"auc_diff": auc_diff, "spearman_corr": float(spearman_r)}
    return metrics, float(spearman_r)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_model_output(path: Path) -> Tuple[float, np.ndarray]:
    """
    Load a model output artifact.

    The function expects a JSON file with at least the following keys:
    - ``auc``: ROC‑AUC (float)
    - ``importance``: list or array of importance scores (numeric)

    Parameters
    ----------
    path: Path
        Path to the JSON file.

    Returns
    -------
    Tuple[float, np.ndarray]
        The ROC‑AUC and the importance vector as a NumPy array.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Model output file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        auc = float(data["auc"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Missing or invalid 'auc' in {path}") from exc

    try:
        importance_raw = data["importance"]
        importance = np.asarray(importance_raw, dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Missing or invalid 'importance' in {path}"
        ) from exc

    return auc, importance

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Command‑line interface for model comparison.

    Usage example::
        python code/modeling/compare_models.py \\
            --primary data/model/primary_output.json \\
            --alternative data/model/alternative_output.json \\
            --output data/model/comparison_metrics.json

    The script will:
    1. Load the two JSON artifacts.
    2. Compute the ROC‑AUC difference and Spearman rank correlation.
    3. Assert that the Spearman correlation is at least 0.7.
    4. Print a short summary.
    5. Optionally write the metrics dictionary to ``--output``.
    """
    parser = argparse.ArgumentParser(
        description="Compare primary and alternative model performance."
    )
    parser.add_argument(
        "--primary",
        type=Path,
        required=True,
        help="Path to primary model output JSON (contains 'auc' and 'importance').",
    )
    parser.add_argument(
        "--alternative",
        type=Path,
        required=True,
        help="Path to alternative model output JSON (contains 'auc' and 'importance').",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write comparison metrics as JSON.",
    )
    args = parser.parse_args()

    # Load artifacts
    primary_auc, primary_imp = _load_model_output(args.primary)
    alt_auc, alt_imp = _load_model_output(args.alternative)

    # Compute comparison metrics
    metrics, spearman_r = compare_models(
        primary_auc, alt_auc, primary_imp, alt_imp
    )

    # Assertion: Spearman correlation must be >= 0.7
    if spearman_r < 0.7:
        raise AssertionError(
            f"Spearman rank correlation {spearman_r:.4f} is below the required 0.7 threshold."
        )

    # Print a concise summary
    print("Model Comparison Summary")
    print("------------------------")
    print(f"Primary ROC‑AUC      : {primary_auc:.4f}")
    print(f"Alternative ROC‑AUC : {alt_auc:.4f}")
    print(f"AUC difference       : {metrics['auc_diff']:.4f}")
    print(f"Spearman correlation : {metrics['spearman_corr']:.4f}")

    # Optional persistence
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nComparison metrics written to {args.output}")

if __name__ == "__main__":
    main()