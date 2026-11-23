"""
correlation_analysis.py
-----------------------
Provides functions to compute Pearson correlations between each metabolite
class and the herbivory score, apply Benjamini‑Hochberg correction, enforce
the required number of significant negative classes, and persist the
results. Also includes a small helper that runs the full step when the
module is executed as a script.
"""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from statsmodels.stats.multitest import multipletests

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

METABOLITE_COLUMNS = ["alkaloids", "terpenes", "phenolics", "benzoxazinoids"]
HERBIVORY_COLUMN = "herbivory_score"


def _safe_pearson(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    """
    Compute Pearson correlation safely.

    If either series has zero variance (i.e., all values identical),
    ``pearsonr`` raises a ``ValueError``. In that case we return
    a correlation of 0.0 and a p‑value of 1.0, indicating no
    relationship.

    Parameters
    ----------
    x, y : pd.Series
        Input data series.

    Returns
    -------
    r : float
        Pearson correlation coefficient (or 0.0 if undefined).
    p : float
        Two‑tailed p‑value (or 1.0 if undefined).
    """
    if x.nunique() < 2 or y.nunique() < 2:
        # No variation – correlation undefined.
        return 0.0, 1.0
    try:
        r, p = pearsonr(x.values, y.values)
    except ValueError as exc:
        # Catch any unexpected ValueError from scipy and fallback.
        log.warning(f"pearsonr failed for column pair: {exc}")
        r, p = 0.0, 1.0
    return r, p


def compute_correlations(df: pd.DataFrame) -> Dict:
    """
    Compute Pearson correlations between each metabolite class and
    ``herbivory_score`` and apply Benjamini‑Hochberg FDR correction.

    Parameters
    ----------
    df : pd.DataFrame
        Processed data containing the required metabolite columns and
        ``herbivory_score``.

    Returns
    -------
    dict
        AnalysisResult dict with keys:
          - result_type: "correlation"
          - matrix: metabolite → r
          - p_values: metabolite → p
          - q_values: metabolite → BH‑adjusted q
          - significant_negative_classes: list of metabolites with q<0.05 and r<0
          - method: "Pearson"
    """
    # Ensure required columns exist
    missing = [c for c in METABOLITE_COLUMNS + [HERBIVORY_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for correlation: {missing}")

    r_dict: Dict[str, float] = {}
    p_dict: Dict[str, float] = {}

    for met in METABOLITE_COLUMNS:
        r, p = _safe_pearson(df[met], df[HERBIVORY_COLUMN])
        r_dict[met] = r
        p_dict[met] = p
        log.debug(f"Metabolite {met}: r={r:.4f}, p={p:.4e}")

    # Benjamini‑Hochberg correction
    p_vals = np.array([p_dict[met] for met in METABOLITE_COLUMNS])
    _, q_vals, _, _ = multipletests(p_vals, method="fdr_bh")
    q_dict = {met: q for met, q in zip(METABOLITE_COLUMNS, q_vals)}

    # Select significant negative classes
    significant_negative = [
        met
        for met in METABOLITE_COLUMNS
        if q_dict[met] < 0.05 and r_dict[met] < 0.0
    ]

    # Enforce FR‑003: between 3 and 5 inclusive
    if not (3 <= len(significant_negative) <= 5):
        raise ValueError(
            f"Number of significant negative classes ({len(significant_negative)}) "
            f"is outside the required range 3‑5."
        )

    result = {
        "result_type": "correlation",
        "matrix": r_dict,
        "p_values": p_dict,
        "q_values": q_dict,
        "significant_negative_classes": significant_negative,
        "method": "Pearson",
    }
    return result


def _save_result(result: Dict, out_path: Path) -> None:
    """
    Write the result dict as pretty‑printed JSON.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    log.info(f"Correlation result written to {out_path}")


def _run_pipeline() -> None:
    """
    Load the pre‑processed dataset, compute correlations, save the JSON
    result, and generate the heat‑map figure.
    """
    data_path = paths.data("processed", "clean.parquet")
    df = pd.read_parquet(data_path)

    result = compute_correlations(df)

    # Write JSON result
    json_path = paths.outputs("correlation_results.json")
    _save_result(result, json_path)

    # Generate heat‑map
    from src.visualization import plot_correlation_heatmap

    heatmap_path = paths.outputs("heatmap.png")
    plot_correlation_heatmap(result, str(heatmap_path))


if __name__ == "__main__":
    _run_pipeline()
