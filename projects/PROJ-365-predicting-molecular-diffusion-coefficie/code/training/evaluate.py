"""
Evaluation script for the molecular diffusion coefficient prediction project.

This module provides functions to:
- Load the featurized dataset (JSON Lines format) produced by the ingestion pipeline.
- Compute performance metrics (RMSE and Pearson correlation) for the GNN and
  Linear Regression baseline.
- Perform a paired t‑test on the absolute errors of the two models.
- Determine a hypothesis status based on the Pearson correlation coefficient.
- Respect the ``data_source_flag.json`` artifact: if the data source is marked as
  ``synthetic`` the evaluation step is skipped and no JSON report is created.

The public API matches the original specification:
  - ``load_featurized_dataset``
  - ``compute_metrics``
  - ``determine_hypothesis_status``
  - ``main``
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from scipy.stats import ttest_rel

from utils.config import get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def _ensure_dir(path: Path) -> None:
    """Make sure the parent directory of *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def load_featurized_dataset() -> List[Dict[str, Any]]:
    """
    Load the featurized dataset produced by ``code/ingestion/featurize.py``.

    The dataset is expected to be a JSON Lines file located at
    ``data/processed/featurized.jsonl``.  Each line must contain at least the
    following keys:

    - ``target``: the experimental diffusion coefficient (float)
    - ``gnn_pred``: the GNN model prediction (float)
    - ``baseline_pred``: the Linear Regression baseline prediction (float)

    Returns
    -------
    List[Dict[str, Any]]
        A list where each element corresponds to a molecule record.
    """
    dataset_path = (
        get_project_root() / "data" / "processed" / "featurized.jsonl"
    )
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Featurized dataset not found at expected location: {dataset_path}"
        )

    records: List[Dict[str, Any]] = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.error(f"Invalid JSON line in featurized dataset: {exc}")
                raise
            # Basic validation – ensure required fields are present
            for key in ("target", "gnn_pred", "baseline_pred"):
                if key not in record:
                    raise KeyError(
                        f"Record missing required key '{key}': {record}"
                    )
            records.append(record)
    logger.info(f"Loaded {len(records)} featurized records.")
    return records


def compute_metrics(
    records: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Compute performance metrics for the GNN and baseline models.

    Parameters
    ----------
    records : List[Dict[str, Any]]
        Output of :func:`load_featurized_dataset`.

    Returns
    -------
    dict
        Dictionary containing:

        - ``gnn_rmse`` : RMSE for the GNN predictions.
        - ``baseline_rmse`` : RMSE for the baseline predictions.
        - ``gnn_pearson_r`` : Pearson correlation coefficient for GNN.
        - ``baseline_pearson_r`` : Pearson correlation coefficient for baseline.
        - ``p_value`` : p‑value from a paired t‑test on absolute errors.
    """
    # Extract arrays
    targets = np.array([rec["target"] for rec in records], dtype=float)
    gnn_preds = np.array([rec["gnn_pred"] for rec in records], dtype=float)
    baseline_preds = np.array(
        [rec["baseline_pred"] for rec in records], dtype=float
    )

    # RMSE
    gnn_rmse = float(np.sqrt(np.mean((gnn_preds - targets) ** 2)))
    baseline_rmse = float(np.sqrt(np.mean((baseline_preds - targets) ** 2)))

    # Pearson correlation (handle constant arrays gracefully)
    def _pearson(x: np.ndarray, y: np.ndarray) -> float:
        if np.std(x) == 0 or np.std(y) == 0:
            return 0.0
        return float(np.corrcoef(x, y)[0, 1])

    gnn_pearson_r = _pearson(gnn_preds, targets)
    baseline_pearson_r = _pearson(baseline_preds, targets)

    # Paired t‑test on absolute errors
    gnn_abs_err = np.abs(gnn_preds - targets)
    baseline_abs_err = np.abs(baseline_preds - targets)

    # If there are fewer than 2 samples, t‑test is not defined; fall back to NaN.
    if len(gnn_abs_err) < 2:
        p_value = float("nan")
    else:
        t_stat, p_value = ttest_rel(gnn_abs_err, baseline_abs_err)
        p_value = float(p_value)

    metrics = {
        "gnn_rmse": gnn_rmse,
        "baseline_rmse": baseline_rmse,
        "gnn_pearson_r": gnn_pearson_r,
        "baseline_pearson_r": baseline_pearson_r,
        "p_value": p_value,
    }
    logger.debug(f"Computed metrics: {metrics}")
    return metrics


def determine_hypothesis_status(pearson_r: float) -> str:
    """
    Translate a Pearson correlation coefficient into a hypothesis status.

    Parameters
    ----------
    pearson_r : float
        Pearson correlation coefficient.

    Returns
    -------
    str
        One of ``'positive'``, ``'null'``, or ``'inconclusive'`` according to
        the specification:
          - > 0.7   → ``positive``
          - < 0.3   → ``null``
          - otherwise → ``inconclusive``
    """
    if pearson_r > 0.7:
        return "positive"
    if pearson_r < 0.3:
        return "null"
    return "inconclusive"


def main() -> None:
    """
    Entry point for the evaluation step.

    The function performs the following actions:

    1. Reads ``data/data_source_flag.json`` to determine whether the pipeline
       is operating on real or synthetic data.
    2. If the source is synthetic, the function logs the decision and exits
       without creating an evaluation report.
    3. If the source is real, the featurized dataset is loaded, metrics are
       computed, a paired t‑test is performed, and a JSON report is written to
       ``data/artifacts/reports/evaluation.json``.
    """
    # ------------------------------------------------------------------- #
    # Step 1 – Determine data source
    # ------------------------------------------------------------------- #
    flag_path = get_project_root() / "data" / "data_source_flag.json"
    if not flag_path.is_file():
        logger.error(
            f"Data source flag file not found at {flag_path}. "
            "Assuming synthetic data to avoid accidental metric leakage."
        )
        return

    try:
        with flag_path.open("r", encoding="utf-8") as f:
            flag = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error(f"Unable to parse data source flag JSON: {exc}")
        raise

    source = flag.get("source", "synthetic").lower()
    logger.info(f"Data source flag indicates: {source}")

    if source != "real":
        logger.info(
            "Synthetic data detected – skipping metric calculation and "
            "evaluation report generation."
        )
        return

    # ------------------------------------------------------------------- #
    # Step 2 – Load featurized data
    # ------------------------------------------------------------------- #
    records = load_featurized_dataset()
    if not records:
        logger.warning("Featurized dataset is empty – no evaluation will be performed.")
        return

    # ------------------------------------------------------------------- #
    # Step 3 – Compute metrics and paired t‑test
    # ------------------------------------------------------------------- #
    metrics = compute_metrics(records)

    # ------------------------------------------------------------------- #
    # Step 4 – Determine hypothesis status (based on GNN Pearson r)
    # ------------------------------------------------------------------- #
    hypothesis_status = determine_hypothesis_status(metrics["gnn_pearson_r"])

    # ------------------------------------------------------------------- #
    # Step 5 – Write evaluation report
    # ------------------------------------------------------------------- #
    report = {
        "pearson_r": metrics["gnn_pearson_r"],
        "rmse": metrics["gnn_rmse"],
        "p_value": metrics["p_value"],
        "hypothesis_status": hypothesis_status,
    }

    report_path = (
        get_project_root() / "data" / "artifacts" / "reports" / "evaluation.json"
    )
    _ensure_dir(report_path)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    logger.info(f"Evaluation report written to {report_path}")


if __name__ == "__main__":
    # When executed as a script, run the evaluation.
    main()