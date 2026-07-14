import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.
    If the file does not exist or is empty, an empty dict is returned.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                logger.warning(
                    "JSON content at %s is not a dict; returning empty dict.", file_path
                )
                return {}
    except FileNotFoundError:
        logger.warning("File %s not found; returning empty dict.", file_path)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON from %s: %s", file_path, e)
        return {}

def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """
    Write a dictionary to a JSON file with pretty formatting.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, sort_keys=True)
    logger.info("Saved JSON file to %s", file_path)

# ----------------------------------------------------------------------
# Loading functions (kept for backward‑compatibility)
# ----------------------------------------------------------------------
def load_baseline_metrics(
    path: str = "data/processed/baseline_metrics.json",
) -> Dict[str, Any]:
    return _load_json_file(path)

def load_cleaned_metrics(
    path: str = "data/processed/cleaned_metrics.json",
) -> Dict[str, Any]:
    return _load_json_file(path)

def load_sensitivity_analysis(
    path: str = "data/processed/sensitivity_analysis.json",
) -> Dict[str, Any]:
    return _load_json_file(path)

# ----------------------------------------------------------------------
# Core comparison logic
# ----------------------------------------------------------------------
def _is_number(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)

def compute_metric_shifts(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> Tuple[Dict[str, float], Dict[str, Optional[float]]]:
    """
    Compute absolute and relative differences between two metric dictionaries.

    Returns:
        absolute_diff: dict of |cleaned - baseline|
        relative_diff: dict of absolute_diff / baseline (None if baseline == 0)
    """
    absolute_diff: Dict[str, float] = {}
    relative_diff: Dict[str, Optional[float]] = {}

    for key, base_val in baseline.items():
        clean_val = cleaned.get(key)
        if _is_number(base_val) and _is_number(clean_val):
            abs_diff = abs(clean_val - base_val)
            absolute_diff[key] = round(abs_diff, 5)
            if base_val != 0:
                rel = round(abs_diff / abs(base_val), 5)
            else:
                rel = None
            relative_diff[key] = rel
        else:
            # Non‑numeric entries are ignored for diff calculations
            logger.debug(
                "Skipping non‑numeric metric key %s for diff calculation.", key
            )
    return absolute_diff, relative_diff

def compute_inconsistency_rate(
    baseline: Dict[str, Any], cleaned: Dict[str, Any], significance_key: str = "p_value"
) -> Optional[float]:
    """
    Compute the proportion of metrics where the significance status changes
    between baseline and cleaned (i.e., p <= 0.05 flips to >0.05 or vice‑versa).

    Returns None if the required key is missing in either dict.
    """
    base_p = baseline.get(significance_key)
    clean_p = cleaned.get(significance_key)

    if base_p is None or clean_p is None:
        logger.warning(
            "Significance key %s missing from one of the metric dicts; cannot compute inconsistency rate.",
            significance_key,
        )
        return None

    def _is_significant(p: Any) -> bool:
        return _is_number(p) and p <= 0.05

    inconsistency = _is_significant(base_p) != _is_significant(clean_p)
    return 1.0 if inconsistency else 0.0

# ----------------------------------------------------------------------
# Public API – create comparison report
# ----------------------------------------------------------------------
def create_comparison_report(
    baseline_path: str = "data/processed/baseline_metrics.json",
    cleaned_path: str = "data/processed/cleaned_metrics.json",
    sensitivity_path: str = "data/processed/sensitivity_analysis.json",
    output_path: str = "data/processed/comparison_report.json",
) -> None:
    """
    Assemble a ComparisonReport JSON artifact that contains:
    - baseline_metrics
    - cleaned_metrics
    - absolute_diff
    - relative_diff
    - sensitivity_analysis (if available)

    The function is tolerant of missing input files; missing sections are
    represented as empty dictionaries in the final report.
    """
    logger.info("Loading baseline metrics from %s", baseline_path)
    baseline = load_baseline_metrics(baseline_path)

    logger.info("Loading cleaned metrics from %s", cleaned_path)
    cleaned = load_cleaned_metrics(cleaned_path)

    logger.info("Loading sensitivity analysis from %s", sensitivity_path)
    sensitivity = load_sensitivity_analysis(sensitivity_path)

    logger.info("Computing metric shifts")
    absolute_diff, relative_diff = compute_metric_shifts(baseline, cleaned)

    logger.info("Computing inconsistency rate (p‑value status change)")
    inconsistency_rate = compute_inconsistency_rate(baseline, cleaned)

    # Assemble the report dictionary
    report: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "baseline_metrics": baseline,
        "cleaned_metrics": cleaned,
        "absolute_diff": absolute_diff,
        "relative_diff": relative_diff,
        "sensitivity_analysis": sensitivity,
    }

    if inconsistency_rate is not None:
        report["inconsistency_rate"] = inconsistency_rate

    # Write the report to disk
    save_json_file(output_path, report)
    logger.info("Comparison report written to %s", output_path)

# ----------------------------------------------------------------------
# Backward‑compatible wrapper (used by older scripts)
# ----------------------------------------------------------------------
def generate_comparison_report(*args, **kwargs) -> None:
    """
    Historical name kept for compatibility. Delegates to create_comparison_report.
    """
    logger.debug(
        "generate_comparison_report called with args=%s kwargs=%s", args, kwargs
    )
    create_comparison_report(*args, **kwargs)
