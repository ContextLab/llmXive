"""
Evaluation script for molecular diffusion coefficient prediction.

This script reads the featurized dataset produced by the ingestion pipeline,
computes evaluation metrics (Pearson correlation, RMSE, paired t‑test on absolute
errors) and writes a JSON report to ``artifacts/reports/evaluation.json``.
It respects the ``data_source_flag.json`` artifact: if the data source is
marked as ``synthetic`` the evaluation is skipped and no report is written.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from scipy.stats import ttest_rel

from utils.config import get_project_root

__all__ = [
    "load_featurized_dataset",
    "compute_metrics",
    "determine_hypothesis_status",
    "main",
]


def _get_logger() -> logging.Logger:
    """Create (or retrieve) a module‑level logger."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        # Configure a simple console logger if none exists yet.
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_featurized_dataset() -> List[Dict[str, Any]]:
    """
    Load the featurized JSONL dataset.

    Returns
    -------
    List[Dict[str, Any]]
        Each entry must contain at least the keys ``true``, ``gnn_pred`` and
        ``baseline_pred``.  Entries missing any of these keys are ignored.
    """
    logger = _get_logger()
    data_path = (
        get_project_root()
        / "data"
        / "processed"
        / "featurized.jsonl"
    )
    if not data_path.is_file():
        logger.error(f"Featurized dataset not found at {data_path}")
        raise FileNotFoundError(f"Featurized dataset not found at {data_path}")

    records: List[Dict[str, Any]] = []
    with data_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning(
                    f"Skipping malformed JSON on line {line_num}: {exc}"
                )
                continue

            required_keys = {"true", "gnn_pred", "baseline_pred"}
            if not required_keys.issubset(rec):
                missing = required_keys - rec.keys()
                logger.warning(
                    f"Record on line {line_num} missing keys {missing}; skipping."
                )
                continue
            records.append(rec)

    if not records:
        logger.error("No valid records found in the featurized dataset.")
        raise ValueError("Featurized dataset contains no valid records.")
    logger.info(f"Loaded {len(records)} valid records from featurized dataset.")
    return records


def compute_metrics(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute evaluation metrics.

    Parameters
    ----------
    records : List[Dict[str, Any]]
        List of dictionaries containing ``true``, ``gnn_pred`` and
        ``baseline_pred``.

    Returns
    -------
    Dict[str, float]
        ``pearson_r`` – Pearson correlation coefficient between true and GNN
        predictions.
        ``rmse`` – Root‑mean‑square error of the GNN predictions.
        ``p_value`` – Two‑sided p‑value from a paired t‑test on the absolute
        errors of GNN vs. baseline.
    """
    logger = _get_logger()
    true_vals = np.array([r["true"] for r in records], dtype=float)
    gnn_preds = np.array([r["gnn_pred"] for r in records], dtype=float)
    baseline_preds = np.array(
        [r["baseline_pred"] for r in records], dtype=float
    )

    # Pearson correlation
    if true_vals.size < 2:
        logger.error("Not enough data points to compute Pearson correlation.")
        raise ValueError("Insufficient data for Pearson correlation.")
    pearson_r = np.corrcoef(true_vals, gnn_preds)[0, 1]

    # RMSE
    mse = np.mean((true_vals - gnn_preds) ** 2)
    rmse = float(np.sqrt(mse))

    # Paired t‑test on absolute errors
    abs_err_gnn = np.abs(true_vals - gnn_preds)
    abs_err_baseline = np.abs(true_vals - baseline_preds)
    t_stat, p_value = ttest_rel(abs_err_gnn, abs_err_baseline)

    logger.debug(
        f"Computed metrics – Pearson r: {pearson_r:.4f}, RMSE: {rmse:.4f}, "
        f"paired t‑test p‑value: {p_value:.4g}"
    )
    return {
        "pearson_r": float(pearson_r),
        "rmse": rmse,
        "p_value": float(p_value),
    }


def determine_hypothesis_status(pearson_r: float) -> str:
    """
    Determine the hypothesis status based on Pearson correlation.

    Parameters
    ----------
    pearson_r : float
        Pearson correlation coefficient.

    Returns
    -------
    str
        ``'positive'`` if r > 0.7,
        ``'null'`` if r < 0.3,
        ``'inconclusive'`` otherwise.
    """
    if pearson_r > 0.7:
        return "positive"
    if pearson_r < 0.3:
        return "null"
    return "inconclusive"


def _read_data_source_flag() -> str:
    """
    Read the ``data_source_flag.json`` artifact.

    Returns
    -------
    str
        Either ``'real'`` or ``'synthetic'``.
    """
    flag_path = get_project_root() / "data" / "data_source_flag.json"
    if not flag_path.is_file():
        raise FileNotFoundError(
            f"Data source flag not found at expected location: {flag_path}"
        )
    with flag_path.open("r", encoding="utf-8") as f:
        flag_content = json.load(f)
    source = flag_content.get("source")
    if source not in {"real", "synthetic"}:
        raise ValueError(
            f"Invalid source value in {flag_path}: {source!r}. "
            "Expected 'real' or 'synthetic'."
        )
    return source


def main() -> None:
    """
    Entry point for the evaluation stage.

    - Reads ``data_source_flag.json``.
    - If the source is ``synthetic`` the function exits without creating any
      evaluation artifact.
    - If the source is ``real`` computes metrics and writes them to
      ``artifacts/reports/evaluation.json``.
    """
    logger = _get_logger()
    try:
        source = _read_data_source_flag()
    except Exception as exc:
        logger.error(f"Failed to read data source flag: {exc}")
        raise

    if source == "synthetic":
        logger.info(
            "Synthetic data source detected – skipping metric calculation "
            "and not creating evaluation.json."
        )
        return

    logger.info("Real data source detected – proceeding with evaluation.")
    records = load_featurized_dataset()
    metrics = compute_metrics(records)
    hypothesis_status = determine_hypothesis_status(metrics["pearson_r"])

    report = {
        "pearson_r": metrics["pearson_r"],
        "rmse": metrics["rmse"],
        "p_value": metrics["p_value"],
        "hypothesis_status": hypothesis_status,
    }

    output_dir = get_project_root() / "artifacts" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "evaluation.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Evaluation report written to {output_path}")