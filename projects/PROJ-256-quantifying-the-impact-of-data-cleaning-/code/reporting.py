import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from models import ComparisonReport

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# JSON I/O helpers
# ----------------------------------------------------------------------


def load_json_file(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return its content as a dict.
    If the file does not exist, returns an empty dict and logs a warning.
    """
    p = Path(path)
    if not p.is_file():
        logger.warning(f"JSON file {p} not found – returning empty dict.")
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """
    Write ``data`` as JSON to ``path``. Parent directories are created
    automatically.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


# ----------------------------------------------------------------------
# Metric loading
# ----------------------------------------------------------------------


def load_baseline_metrics() -> Dict[str, Any]:
    return load_json_file(Path("data/processed/baseline_metrics.json"))


def load_cleaned_metrics() -> Dict[str, Any]:
    return load_json_file(Path("data/processed/cleaned_metrics.json"))


def load_sensitivity_analysis() -> Dict[str, Any]:
    """
    Sensitivity analysis results are stored in
    ``data/processed/sensitivity_analysis.json`` by other pipeline steps.
    If the file is missing we simply return an empty dict.
    """
    return load_json_file(Path("data/processed/sensitivity_analysis.json"))


# ----------------------------------------------------------------------
# Difference calculations
# ----------------------------------------------------------------------


def _extract_numeric_metric(
    metrics: Dict[str, Any], dataset: str, metric_path: List[str]
) -> Optional[float]:
    """
    Helper to walk a nested dict (``metrics``) following ``metric_path``.
    Returns ``None`` if any intermediate key is missing or the final value is
    not a number.
    """
    cur = metrics.get(dataset, {})
    for key in metric_path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    if isinstance(cur, (int, float)):
        return float(cur)
    return None


def calculate_absolute_diff(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
    metric_path: List[str],
) -> Dict[str, float]:
    """
    Compute absolute differences for a specific metric across all datasets.

    Parameters
    ----------
    baseline, cleaned : dict
        Metric dictionaries keyed by dataset name.
    metric_path : list of str
        Path to the leaf metric (e.g., ["t_test", "p_value"]).

    Returns
    -------
    dict
        Mapping ``dataset_name -> absolute_difference`` (rounded to 3 dp).
    """
    diffs: Dict[str, float] = {}
    for ds in baseline.keys():
        b_val = _extract_numeric_metric(baseline, ds, metric_path)
        c_val = _extract_numeric_metric(cleaned, ds, metric_path)
        if b_val is None or c_val is None:
            continue
        diffs[ds] = round(abs(c_val - b_val), 3)
    return diffs


def calculate_relative_diff(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
    metric_path: List[str],
) -> Dict[str, Optional[float]]:
    """
    Compute relative differences ( (cleaned - baseline) / baseline ) for a metric.
    Returns ``None`` when baseline value is zero or missing.
    """
    rel_diffs: Dict[str, Optional[float]] = {}
    for ds in baseline.keys():
        b_val = _extract_numeric_metric(baseline, ds, metric_path)
        c_val = _extract_numeric_metric(cleaned, ds, metric_path)
        if b_val is None or c_val is None or b_val == 0:
            rel_diffs[ds] = None
            continue
        rel_diffs[ds] = round((c_val - b_val) / b_val, 3)
    return rel_diffs


# ----------------------------------------------------------------------
# Aggregation helpers
# ----------------------------------------------------------------------


def aggregate_metrics_for_comparison(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a nested dictionary containing absolute and relative differences
    for the three core metrics used throughout the project:
    * p‑value
    * confidence‑interval width
    * effect‑size (Cohen's d)

    The function is tolerant of missing values.
    """
    agg: Dict[str, Any] = {
        "p_value": {
            "absolute": calculate_absolute_diff(baseline, cleaned, ["t_test", "p_value"]),
            "relative": calculate_relative_diff(baseline, cleaned, ["t_test", "p_value"]),
        },
        "ci_width": {
            "absolute": calculate_absolute_diff(baseline, cleaned, ["t_test", "ci"]),
            "relative": calculate_relative_diff(baseline, cleaned, ["t_test", "ci"]),
        },
        "effect_size": {
            "absolute": calculate_absolute_diff(baseline, cleaned, ["effect_size", "cohen_d"]),
            "relative": calculate_relative_diff(baseline, cleaned, ["effect_size", "cohen_d"]),
        },
    }
    return agg


# ----------------------------------------------------------------------
# ComparisonReport construction
# ----------------------------------------------------------------------


def create_comparison_report() -> ComparisonReport:
    """
    Assemble a :class:`ComparisonReport` instance from the artifacts produced
    by earlier pipeline steps.
    """
    baseline = load_baseline_metrics()
    cleaned = load_cleaned_metrics()
    sensitivity = load_sensitivity_analysis()

    diff_agg = aggregate_metrics_for_comparison(baseline, cleaned)

    report = ComparisonReport(
        generated_at=datetime.utcnow().isoformat() + "Z",
        baseline_metrics=baseline,
        cleaned_metrics=cleaned,
        absolute_diff=diff_agg,
        relative_diff=diff_agg,  # both dicts contain sub‑dicts; callers can pick needed part
        sensitivity_analysis=sensitivity,
    )
    return report


def main() -> None:
    """
    Entry point used by the quick‑start run‑book. Writes the report to
    ``data/processed/comparison_report.json``.
    """
    logger = setup_logging("INFO")  # type: ignore  # noqa: F821 – imported via utils
    report = create_comparison_report()
    output_path = Path("data/processed/comparison_report.json")
    save_json_file(report.dict(), output_path)
    logger.info(f"Comparison report written to {output_path}")
