"""
Evaluation script for molecular diffusion coefficient prediction.

This script extends the existing evaluation logic to:
1. Perform a paired t‑test on the absolute errors of the GNN and the baseline.
2. Respect the `data_source_flag.json` artifact – if the source is synthetic,
   the evaluation JSON is not created.
3. When the source is real, compute Pearson r, RMSE, p‑value from the t‑test,
   and a `hypothesis_status` field that reflects the strength of the correlation.

The script is intended to be run as a module:
    python -m training.evaluate

It writes its output to:
    artifacts/reports/evaluation.json
"""
import json
import logging
from pathlib import Path

import numpy as np
from scipy.stats import ttest_rel

from utils.config import get_project_root
from utils.logging import get_logger

# ----------------------------------------------------------------------
# Helper functions (some are re‑implemented here to keep the module self‑contained)
# ----------------------------------------------------------------------


def load_featurized_dataset() -> list[dict]:
    """
    Load the featurized dataset produced by ``code/ingestion/ingest.py``.
    The dataset is stored as a JSON‑Lines file where each line is a dict
    containing at least the keys:
        - ``target``: true diffusion coefficient (float)
        - ``gnn_pred``: model prediction from the GNN (float)
        - ``baseline_pred``: model prediction from the linear baseline (float)

    Returns
    -------
    List[dict]
        List of records, one per molecule‑solvent pair.
    """
    data_path = get_project_root() / "data" / "processed" / "featurized.jsonl"
    records = []
    with data_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Compute Pearson correlation coefficient and root‑mean‑square error.

    Parameters
    ----------
    y_true : np.ndarray
        Ground‑truth values.
    y_pred : np.ndarray
        Predicted values.

    Returns
    -------
    dict
        ``{'pearson_r': float, 'rmse': float}``
    """
    if y_true.size == 0:
        raise ValueError("Empty array provided to compute_metrics.")

    # Pearson r
    if y_true.size < 2:
        # np.corrcoef requires at least two samples; fall back to 0.0
        pearson_r = 0.0
    else:
        pearson_r = np.corrcoef(y_true, y_pred)[0, 1]

    # RMSE
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    return {"pearson_r": float(pearson_r), "rmse": float(rmse)}


def determine_hypothesis_status(pearson_r: float) -> str:
    """
    Translate a Pearson correlation coefficient into a qualitative hypothesis
    status as required by SC‑001.

    Parameters
    ----------
    pearson_r : float
        Pearson correlation coefficient.

    Returns
    -------
    str
        One of ``'positive'``, ``'null'``, ``'inconclusive'``.
    """
    if pearson_r > 0.7:
        return "positive"
    if pearson_r < 0.3:
        return "null"
    return "inconclusive"


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Execute the evaluation pipeline.

    The function respects the data‑source flag:
    * If the flag indicates a synthetic source, the function logs the decision
      and exits without writing ``evaluation.json``.
    * Otherwise, it computes the required metrics, performs the paired t‑test,
      and writes the JSON report.
    """
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 1️⃣  Determine whether we are dealing with synthetic data
    # ------------------------------------------------------------------
    flag_path = get_project_root() / "data" / "data_source_flag.json"
    if not flag_path.is_file():
        logger.warning(
            "Data source flag file not found at %s – assuming real data.",
            flag_path,
        )
        source_is_synthetic = False
    else:
        try:
            with flag_path.open("r", encoding="utf-8") as f:
                flag_content = json.load(f)
            source_is_synthetic = flag_content.get("source", "synthetic") == "synthetic"
        except Exception as exc:
            logger.error("Failed to read data source flag: %s", exc)
            source_is_synthetic = False

    if source_is_synthetic:
        logger.info(
            "Synthetic data detected – skipping metric calculation and evaluation report generation."
        )
        # Explicitly ensure no stray evaluation file remains from previous runs
        eval_path = (
            get_project_root()
            / "artifacts"
            / "reports"
            / "evaluation.json"
        )
        if eval_path.is_file():
            eval_path.unlink()
        return

    # ------------------------------------------------------------------
    # 2️⃣  Load featurized data
    # ------------------------------------------------------------------
    try:
        records = load_featurized_dataset()
    except Exception as exc:
        logger.error("Failed to load featurized dataset: %s", exc)
        raise

    # Extract true values and predictions
    y_true = np.array([rec["target"] for rec in records], dtype=float)
    y_pred_gnn = np.array([rec["gnn_pred"] for rec in records], dtype=float)
    y_pred_baseline = np.array([rec["baseline_pred"] for rec in records], dtype=float)

    # ------------------------------------------------------------------
    # 3️⃣  Compute individual model metrics
    # ------------------------------------------------------------------
    gnn_metrics = compute_metrics(y_true, y_pred_gnn)
    baseline_metrics = compute_metrics(y_true, y_pred_baseline)

    # ------------------------------------------------------------------
    # 4️⃣  Paired t‑test on absolute errors
    # ------------------------------------------------------------------
    abs_err_gnn = np.abs(y_true - y_pred_gnn)
    abs_err_baseline = np.abs(y_true - y_pred_baseline)

    # scipy's ttest_rel returns (statistic, pvalue)
    t_stat, p_value = ttest_rel(abs_err_gnn, abs_err_baseline, nan_policy="omit")
    p_value = float(p_value) if not np.isnan(p_value) else None

    # ------------------------------------------------------------------
    # 5️⃣  Assemble final report
    # ------------------------------------------------------------------
    report = {
        "gnn": gnn_metrics,
        "baseline": baseline_metrics,
        "pearson_r": gnn_metrics["pearson_r"],  # primary correlation for hypothesis
        "rmse": gnn_metrics["rmse"],
        "p_value": p_value,
        "hypothesis_status": determine_hypothesis_status(gnn_metrics["pearson_r"]),
    }

    # ------------------------------------------------------------------
    # 6️⃣  Write JSON report
    # ------------------------------------------------------------------
    report_path = (
        get_project_root()
        / "artifacts"
        / "reports"
        / "evaluation.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info("Evaluation report written to %s", report_path)
    except Exception as exc:
        logger.error("Failed to write evaluation report: %s", exc)
        raise


if __name__ == "__main__":
    main()
