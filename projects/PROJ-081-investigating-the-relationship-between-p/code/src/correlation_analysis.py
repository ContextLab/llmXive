"""
correlation_analysis.py
-----------------------
Computes Pearson correlations between each metabolite class and the herbivory score,
applies Benjamini‑Hochberg FDR correction, enforces the required number of
significant negative classes (3‑5), saves the results as JSON, and generates a
heat‑map PNG visualisation.

This script is intended to be run after the preprocessing step has produced
``data/processed/clean.parquet``.  It can be executed directly:

    python code/src/correlation_analysis.py

The script writes its outputs to the ``outputs/`` directory using the
``llmxive_toolkit.paths`` helpers, ensuring the directories are created
automatically.
"""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from statsmodels.stats.multitest import multipletests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Expected column names in the processed DataFrame
METABOLITE_COLUMNS = ["alkaloids", "terpenes", "phenolics", "benzoxazinoids"]
OUTCOME_COLUMN = "herbivory_score"


def compute_correlations(df: pd.DataFrame) -> Dict:
    """
    Compute Pearson correlations between each metabolite class and herbivory_score,
    apply Benjamini‑Hochberg FDR correction, and enforce that the number of
    significant negative classes is between 3 and 5 (inclusive).

    Parameters
    ----------
    df : pd.DataFrame
        Processed data containing the required metabolite columns and herbivory_score.

    Returns
    -------
    dict
        AnalysisResult with keys:
          - result_type: "correlation"
          - matrix: dict of metabolite -> correlation coefficient
          - p_values: dict of metabolite -> two‑tailed p‑value
          - q_values: dict of metabolite -> BH‑adjusted q‑value
          - significant_negative_classes: list of metabolite names meeting q<0.05 and coeff<0
          - method: "Pearson"
    """
    # Verify required columns are present
    missing = [c for c in METABOLITE_COLUMNS + [OUTCOME_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for correlation analysis: {missing}")

    # Drop rows with any missing values in the columns of interest
    data = df[METABOLITE_COLUMNS + [OUTCOME_COLUMN]].dropna()
    if data.empty:
        raise ValueError("No data left after dropping rows with missing values.")

    # Compute Pearson r and p for each metabolite
    coeffs: Dict[str, float] = {}
    pvals: Dict[str, float] = {}
    for met in METABOLITE_COLUMNS:
        r, p = pearsonr(data[met], data[OUTCOME_COLUMN])
        coeffs[met] = r
        pvals[met] = p
        log.debug("Metabolite %s: r=%.4f, p=%.4g", met, r, p)

    # Benjamini‑Hochberg FDR correction
    p_array = np.array([pvals[m] for m in METABOLITE_COLUMNS])
    _, q_array, _, _ = multipletests(p_array, alpha=0.05, method="fdr_bh")
    qvals = {m: q for m, q in zip(METABOLITE_COLUMNS, q_array)}

    # Identify significant negative correlations
    significant_negative = [
        m for m in METABOLITE_COLUMNS if qvals[m] < 0.05 and coeffs[m] < 0
    ]

    # Enforce FR‑003: 3‑5 significant negative classes
    if not (3 <= len(significant_negative) <= 5):
        raise ValueError(
            f"Number of significant negative classes ({len(significant_negative)}) "
            f"is outside the required range 3‑5."
        )

    result = {
        "result_type": "correlation",
        "matrix": coeffs,
        "p_values": pvals,
        "q_values": qvals,
        "significant_negative_classes": significant_negative,
        "method": "Pearson",
    }
    return result


def _save_result(result: Dict, out_path: Path) -> None:
    """Write the result dict as pretty‑printed JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    log.info("Correlation results saved to %s", out_path)


def _run_pipeline() -> None:
    """
    Load the pre‑processed dataset, compute correlations, save the JSON
    result, and generate the heat‑map figure.
    """
    # Load the cleaned Parquet file produced by the preprocessing step
    data_path = paths.data("processed", "clean.parquet")
    if not data_path.is_file():
        raise FileNotFoundError(f"Processed data not found at {data_path}")

    df = pd.read_parquet(data_path)

    # Compute correlations
    corr_result = compute_correlations(df)

    # Save JSON result
    json_path = paths.outputs("correlation_results.json")
    _save_result(corr_result, json_path)

    # Generate heat‑map
    from src.visualization import plot_correlation_heatmap  # noqa: E402
    heatmap_path = paths.outputs("heatmap.png")
    plot_correlation_heatmap(corr_result, str(heatmap_path))


if __name__ == "__main__":
    try:
        _run_pipeline()
    except Exception as exc:
        log.error("Correlation analysis failed: %s", exc)
        raise  # Re‑raise to surface a non‑zero exit code
