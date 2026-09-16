import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from scipy.stats import ttest_rel

from utils.config import get_project_root

logger = logging.getLogger(__name__)

def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON Lines file and return a list of records."""
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def load_featurized_dataset() -> List[Dict[str, Any]]:
    """
    Load the featurized dataset produced by ``code/ingestion/ingest.py``.

    The dataset is expected to be a JSONL file where each line contains at least:
        - ``target``: the experimental diffusion coefficient (float)
        - ``gnn_pred``: the prediction from the trained MPNN model (float)
        - ``baseline_pred``: the prediction from the Linear Regression baseline (float)

    Returns
    -------
    List[Dict[str, Any]]
        List of records with the fields described above.
    """
    data_path = (
        Path(get_project_root()) / "data" / "processed" / "featurized.jsonl"
    )
    if not data_path.is_file():
        raise FileNotFoundError(f"Featurized dataset not found at {data_path}")
    logger.info(f"Loading featurized dataset from {data_path}")
    return _load_jsonl(data_path)

def compute_metrics(
    records: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Compute evaluation metrics for the GNN model against the true target values.

    The function also performs a paired t‑test on the absolute errors of the GNN
    and the baseline model.

    Parameters
    ----------
    records : List[Dict[str, Any]]
        The featurized dataset with predictions.

    Returns
    -------
    Dict[str, float]
        Dictionary containing:
            - ``pearson_r``: Pearson correlation coefficient between GNN predictions and true targets.
            - ``rmse``: Root‑mean‑square error of the GNN predictions.
            - ``p_value``: p‑value from a paired t‑test on absolute errors (GNN vs baseline).
    """
    # Extract arrays
    true = np.array([r["target"] for r in records], dtype=float)
    gnn_pred = np.array([r["gnn_pred"] for r in records], dtype=float)
    baseline_pred = np.array([r["baseline_pred"] for r in records], dtype=float)

    # Pearson correlation
    if true.size == 0:
        raise ValueError("Empty dataset supplied to compute_metrics.")
    pearson_r = np.corrcoef(gnn_pred, true)[0, 1]

    # RMSE
    rmse = np.sqrt(np.mean((gnn_pred - true) ** 2))

    # Paired t‑test on absolute errors
    abs_err_gnn = np.abs(gnn_pred - true)
    abs_err_baseline = np.abs(baseline_pred - true)
    # scipy returns (statistic, pvalue)
    _, p_value = ttest_rel(abs_err_gnn, abs_err_baseline)

    return {
        "pearson_r": float(pearson_r),
        "rmse": float(rmse),
        "p_value": float(p_value),
    }

def determine_hypothesis_status(pearson_r: float) -> str:
    """
    Translate the Pearson correlation coefficient into a hypothesis status
    according to the specification.

    Parameters
    ----------
    pearson_r : float
        Pearson correlation coefficient.

    Returns
    -------
    str
        One of ``'positive'``, ``'null'`` or ``'inconclusive'``.
    """
    if pearson_r > 0.7:
        return "positive"
    if pearson_r < 0.3:
        return "null"
    return "inconclusive"

def _read_data_source_flag() -> str:
    """
    Read the ``data_source_flag.json`` artifact created by
    ``code/ingestion/flag_source.py``.

    Returns
    -------
    str
        Either ``'real'`` or ``'synthetic'``.
    """
    flag_path = Path(get_project_root()) / "data" / "data_source_flag.json"
    if not flag_path.is_file():
        raise FileNotFoundError(
            f"Data source flag not found at {flag_path}. "
            "Ensure that the ingestion step has been executed."
        )
    with flag_path.open("r", encoding="utf-8") as f:
        flag = json.load(f)
    source = flag.get("source")
    if source not in {"real", "synthetic"}:
        raise ValueError(
            f"Unexpected source value '{source}' in {flag_path}. "
            "Expected 'real' or 'synthetic'."
        )
    return source

def main() -> None:
    """
    Entry point for the evaluation stage.

    Behaviour:
    * If the data source is synthetic, the script exits silently without
      creating ``artifacts/reports/evaluation.json``.
    * If the data source is real, metrics are computed, the hypothesis status
      is derived, and the JSON report is written.
    """
    try:
        source = _read_data_source_flag()
    except Exception as exc:
        logger.error(f"Failed to read data source flag: {exc}")
        raise

    if source == "synthetic":
        logger.info(
            "Synthetic data source detected – skipping metric calculation "
            "and evaluation report generation."
        )
        return

    # Real data path – compute metrics
    records = load_featurized_dataset()
    metrics = compute_metrics(records)
    hypothesis_status = determine_hypothesis_status(metrics["pearson_r"])
    metrics["hypothesis_status"] = hypothesis_status

    # Write out the evaluation report
    report_path = (
        Path(get_project_root())
        / "artifacts"
        / "reports"
        / "evaluation.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Evaluation report written to {report_path}")

if __name__ == "__main__":
    main()