"""
Reporting utilities for the Quantifying Data Cleaning Impact project.

This module provides functions to load baseline and cleaned metrics,
compute absolute and relative differences, calculate inconsistency rates,
and generate a comparison report saved as JSON.

The implementation is tolerant to missing keys and ensures numeric
precision as required by the specification.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper I/O functions
# ----------------------------------------------------------------------
def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dict."""
    path = Path(filepath)
    if not path.is_file():
        logger.error("File not found: %s", filepath)
        raise FileNotFoundError(f"File not found: {filepath}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    logger.debug("Loaded JSON from %s (keys=%s)", filepath, list(data.keys()))
    return data

def save_json_file(data: Dict[str, Any], filepath: str) -> None:
    """Write *data* to *filepath* as pretty‑printed JSON."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    logger.info("Saved JSON to %s", filepath)

# ----------------------------------------------------------------------
# Load specific metric files
# ----------------------------------------------------------------------
def load_baseline_metrics(path: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Convenience wrapper to load baseline metrics."""
    return load_json_file(path)

def load_cleaned_metrics(path: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Convenience wrapper to load cleaned metrics."""
    return load_json_file(path)

# ----------------------------------------------------------------------
# Metric comparison utilities
# ----------------------------------------------------------------------
def _extract_metric(entry: Dict[str, Any], metric: str) -> Optional[float]:
    """Extract a numeric metric from an entry dict; return None if missing or not a number."""
    value = entry.get(metric)
    if isinstance(value, (int, float)):
        return float(value)
    return None

def calculate_absolute_diff(baseline: Dict[str, Any], cleaned: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute absolute differences for supported metrics.

    Supported keys:
        - t_test.p_value
        - t_test.ci_width
        - linear_regression.r_squared   (or effect_size)
    The function returns a dict with keys like ``p_value_abs_diff``.
    """
    diffs: Dict[str, float] = {}

    # p‑value
    b_p = _extract_metric(baseline.get("t_test", {}), "p_value")
    c_p = _extract_metric(cleaned.get("t_test", {}), "p_value")
    if b_p is not None and c_p is not None:
        diffs["p_value_abs_diff"] = round(abs(c_p - b_p), 3)

    # CI width (assuming ``ci`` is a two‑element list)
    b_ci = baseline.get("t_test", {}).get("ci", [])
    c_ci = cleaned.get("t_test", {}).get("ci", [])
    if isinstance(b_ci, list) and isinstance(c_ci, list) and len(b_ci) == 2 and len(c_ci) == 2:
        b_width = b_ci[1] - b_ci[0]
        c_width = c_ci[1] - c_ci[0]
        diffs["ci_width_abs_diff"] = round(abs(c_width - b_width), 2)

    # effect size / R²
    b_es = _extract_metric(baseline.get("linear_regression", {}), "r_squared")
    c_es = _extract_metric(cleaned.get("linear_regression", {}), "r_squared")
    if b_es is not None and c_es is not None:
        diffs["effect_size_abs_diff"] = round(abs(c_es - b_es), 3)

    logger.debug("Absolute diffs: %s", diffs)
    return diffs

def calculate_relative_diff(baseline: Dict[str, Any], cleaned: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute relative differences ( (cleaned‑baseline) / baseline ) for the same
    metrics as :func:`calculate_absolute_diff`. Results are rounded to three
    decimal places.
    """
    rel: Dict[str, float] = {}

    def _rel(b, c):
        return round((c - b) / b, 3) if b != 0 else float("inf")

    b_p = _extract_metric(baseline.get("t_test", {}), "p_value")
    c_p = _extract_metric(cleaned.get("t_test", {}), "p_value")
    if b_p is not None and c_p is not None:
        rel["p_value_rel_diff"] = _rel(b_p, c_p)

    b_ci = baseline.get("t_test", {}).get("ci", [])
    c_ci = cleaned.get("t_test", {}).get("ci", [])
    if isinstance(b_ci, list) and isinstance(c_ci, list) and len(b_ci) == 2 and len(c_ci) == 2:
        b_width = b_ci[1] - b_ci[0]
        c_width = c_ci[1] - c_ci[0]
        if b_width != 0:
            rel["ci_width_rel_diff"] = round((c_width - b_width) / b_width, 3)

    b_es = _extract_metric(baseline.get("linear_regression", {}), "r_squared")
    c_es = _extract_metric(cleaned.get("linear_regression", {}), "r_squared")
    if b_es is not None and c_es is not None and b_es != 0:
        rel["effect_size_rel_diff"] = _rel(b_es, c_es)

    logger.debug("Relative diffs: %s", rel)
    return rel

def calculate_inconsistency_rate(baseline: Dict[str, Any], cleaned: Dict[str, Any]) -> float:
    """
    Proportion of metrics where significance status changes.
    Significance is defined as p_value < 0.05.
    """
    b_p = _extract_metric(baseline.get("t_test", {}), "p_value")
    c_p = _extract_metric(cleaned.get("t_test", {}), "p_value")
    if b_p is None or c_p is None:
        logger.warning("Missing p_value for inconsistency calculation; returning 0.0")
        return 0.0
    b_sig = b_p < 0.05
    c_sig = c_p < 0.05
    inconsistency = 1.0 if b_sig != c_sig else 0.0
    logger.debug("Inconsistency rate: %s", inconsistency)
    return inconsistency

def aggregate_metrics_for_comparison(baseline: Dict[str, Any], cleaned: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a single dictionary containing all comparison statistics.
    """
    report: Dict[str, Any] = {
        "absolute_diff": calculate_absolute_diff(baseline, cleaned),
        "relative_diff": calculate_relative_diff(baseline, cleaned),
        "inconsistency_rate": calculate_inconsistency_rate(baseline, cleaned),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    logger.info("Aggregated comparison report")
    return report

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def generate_comparison_report(
    baseline_path: str = "data/processed/baseline_metrics.json",
    cleaned_path: str = "data/processed/cleaned_metrics.json",
    output_path: str = "data/processed/comparison_report.json",
) -> None:
    """
    Load baseline and cleaned metric files, compute comparison statistics,
    and write the report to *output_path*.
    """
    logger.info("Generating comparison report")
    baseline = load_baseline_metrics(baseline_path)
    cleaned = load_cleaned_metrics(cleaned_path)
    report = aggregate_metrics_for_comparison(baseline, cleaned)
    save_json_file(report, output_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Generate comparison report between baseline and cleaned metrics.")
    parser.add_argument("--baseline", default="data/processed/baseline_metrics.json", help="Path to baseline metrics JSON")
    parser.add_argument("--cleaned", default="data/processed/cleaned_metrics.json", help="Path to cleaned metrics JSON")
    parser.add_argument("--output", default="data/processed/comparison_report.json", help="Where to write the comparison report")
    args = parser.parse_args()
    generate_comparison_report(args.baseline, args.cleaned, args.output)

if __name__ == "__main__":
    main()