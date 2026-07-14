import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Utility I/O helpers
# ----------------------------------------------------------------------
def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file safely; return empty dict if missing."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return {}

def save_json_file(data: Dict[str, Any], filepath: str) -> None:
    """Write ``data`` to ``filepath`` as pretty‑printed JSON."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON report to {filepath}")

# Backwards‑compatible wrappers used by t027_run_comparison.py
def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Alias for loading baseline metrics JSON."""
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Alias for loading cleaned metrics JSON."""
    return load_json_file(filepath)

# ----------------------------------------------------------------------
# Diff calculation helpers
# ----------------------------------------------------------------------
def calculate_absolute_diff(baseline: Dict[str, Any], cleaned: Dict[str, Any]) -> Dict[str, Any]:
    """Compute absolute differences for numeric leaf values."""
    diff: Dict[str, Any] = {}
    for key, base_val in baseline.items():
        clean_val = cleaned.get(key)
        if isinstance(base_val, (int, float)) and isinstance(clean_val, (int, float)):
            diff[key] = round(abs(clean_val - base_val), 3)
        elif isinstance(base_val, dict) and isinstance(clean_val, dict):
            diff[key] = calculate_absolute_diff(base_val, clean_val)
    return diff

def calculate_relative_diff(baseline: Dict[str, Any], cleaned: Dict[str, Any]) -> Dict[str, Any]:
    """Compute relative (percentage) differences for numeric leaf values."""
    rel: Dict[str, Any] = {}
    for key, base_val in baseline.items():
        clean_val = cleaned.get(key)
        if isinstance(base_val, (int, float)) and isinstance(clean_val, (int, float)):
            if base_val != 0:
                rel[key] = round((clean_val - base_val) / abs(base_val) * 100, 2)
            else:
                rel[key] = None
        elif isinstance(base_val, dict) and isinstance(clean_val, dict):
            rel[key] = calculate_relative_diff(base_val, clean_val)
    return rel

# ----------------------------------------------------------------------
# New metric‑specific calculations required by T027
# ----------------------------------------------------------------------
def _extract_t_test_metrics(entry: Dict[str, Any]) -> Tuple[float, List[float], float]:
    """
    Helper to pull out p‑value, confidence interval and effect size from a
    metric entry. Returns (p_value, ci_list, effect_size). Missing values are
    returned as ``None`` where appropriate.
    """
    t_test = entry.get("t_test", {})
    p = t_test.get("p_value")
    ci = t_test.get("ci")  # expected list like [low, high]
    es = t_test.get("effect_size")
    return p, ci, es

def calculate_metric_shifts(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
    p_threshold: float = 0.05,
) -> Dict[str, Any]:
    """
    Compute per‑dataset shifts required by FR‑006:

    * absolute p‑value shift (rounded to 3 decimals)
    * absolute CI‑width change (rounded to 2 decimals)
    * absolute effect‑size delta (rounded to 3 decimals)
    * overall inconsistency rate (proportion of datasets where significance
      status changes, rounded to 3 decimals)

    Returns a dictionary containing the per‑dataset dictionaries and the
    aggregated inconsistency rate.
    """
    p_shift: Dict[str, float] = {}
    ci_width_change: Dict[str, float] = {}
    effect_delta: Dict[str, float] = {}

    inconsistency_count = 0
    consistency_total = 0

    for dataset_id, base_entry in baseline.items():
        clean_entry = cleaned.get(dataset_id)
        if not isinstance(clean_entry, dict):
            # No cleaned counterpart – skip this dataset
            continue

        base_p, base_ci, base_es = _extract_t_test_metrics(base_entry)
        clean_p, clean_ci, clean_es = _extract_t_test_metrics(clean_entry)

        # Compute p‑value shift
        if isinstance(base_p, (int, float)) and isinstance(clean_p, (int, float)):
            shift = round(abs(clean_p - base_p), 3)
            p_shift[dataset_id] = shift

            # Inconsistency detection
            base_sig = base_p < p_threshold
            clean_sig = clean_p < p_threshold
            inconsistency_count += int(base_sig != clean_sig)
            consistency_total += 1

        # Compute CI‑width change
        if (
            isinstance(base_ci, list)
            and isinstance(clean_ci, list)
            and len(base_ci) == 2
            and len(clean_ci) == 2
        ):
            base_width = base_ci[1] - base_ci[0]
            clean_width = clean_ci[1] - clean_ci[0]
            width_change = round(abs(clean_width - base_width), 2)
            ci_width_change[dataset_id] = width_change

        # Compute effect‑size delta
        if isinstance(base_es, (int, float)) and isinstance(clean_es, (int, float)):
            delta = round(abs(clean_es - base_es), 3)
            effect_delta[dataset_id] = delta

    inconsistency_rate = (
        round(inconsistency_count / consistency_total, 3) if consistency_total > 0 else None
    )

    return {
        "p_value_shift": p_shift,
        "ci_width_change": ci_width_change,
        "effect_size_delta": effect_delta,
        "inconsistency_rate": inconsistency_rate,
    }

# ----------------------------------------------------------------------
# Report generation
# ----------------------------------------------------------------------
def generate_comparison_report(
    baseline_path: str,
    cleaned_path: str,
    output_path: str,
    sensitivity_analysis: Dict[str, Any] = None,
) -> None:
    """
    Build a ``ComparisonReport``‑style dictionary and persist it.

    The ``ComparisonReport`` Pydantic model (defined in ``models.py``) expects
    the following top‑level keys:
        - baseline_metrics
        - cleaned_metrics
        - absolute_diff
        - relative_diff
        - sensitivity_analysis
    In addition, for US3 we also embed the metric‑specific shifts required by
    FR‑006:
        - p_value_shift
        - ci_width_change
        - effect_size_delta
        - inconsistency_rate
    """
    baseline = load_json_file(baseline_path)
    cleaned = load_json_file(cleaned_path)

    # Basic numeric diffs
    abs_diff = calculate_absolute_diff(baseline, cleaned)
    rel_diff = calculate_relative_diff(baseline, cleaned)

    # New FR‑006 metrics
    shift_metrics = calculate_metric_shifts(baseline, cleaned)

    report: Dict[str, Any] = {
        "baseline_metrics": baseline,
        "cleaned_metrics": cleaned,
        "absolute_diff": abs_diff,
        "relative_diff": rel_diff,
        "sensitivity_analysis": sensitivity_analysis or {},
        # FR‑006 specific entries
        "p_value_shift": shift_metrics["p_value_shift"],
        "ci_width_change": shift_metrics["ci_width_change"],
        "effect_size_delta": shift_metrics["effect_size_delta"],
        "inconsistency_rate": shift_metrics["inconsistency_rate"],
    }

    save_json_file(report, output_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """CLI entry point for ad‑hoc generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate comparison report.")
    parser.add_argument("--baseline", required=True, help="Path to baseline_metrics.json")
    parser.add_argument("--cleaned", required=True, help="Path to cleaned_metrics.json")
    parser.add_argument(
        "--output", required=True, help="Path where comparison report will be saved"
    )
    args = parser.parse_args()

    generate_comparison_report(args.baseline, args.cleaned, args.output)