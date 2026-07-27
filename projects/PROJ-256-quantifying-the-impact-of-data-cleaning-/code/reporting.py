"""
Reporting utilities for comparing baseline and cleaned analysis metrics.

This module provides functions to:
- Load JSON metric files.
- Compute absolute and relative differences for p‑values, confidence‑interval
  widths, and effect sizes.
- Compute the inconsistency rate (proportion of datasets where statistical
  significance changes after cleaning).
- Generate a consolidated comparison report and write it to disk.

The implementation is deliberately defensive:
* Missing files raise a clear error.
* All numeric outputs are rounded to the precision required by the
  specification (≥3 decimal places for p‑values and effect sizes,
  ≥2 decimal places for CI‑width changes).
* The module does not make any assumptions about the exact nesting of the
  input JSON – it looks for keys ``t_test`` and ``regression`` (or ``linear``)
  and extracts the needed values if present.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper I/O utilities
# --------------------------------------------------------------------------- #
def load_json_file(filepath: str | Path) -> Dict[str, Any]:
    """Load a JSON file and return its content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    logger.debug("Loaded JSON file %s with %d top‑level keys", path, len(data))
    return data

def save_json_file(data: Dict[str, Any], filepath: str | Path) -> None:
    """Write *data* as pretty‑printed JSON to *filepath*."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    logger.info("Saved JSON file %s", path)

# --------------------------------------------------------------------------- #
# Loading specific metric artifacts
# --------------------------------------------------------------------------- #
def _default_metrics_path() -> Tuple[Path, Path]:
    """Return the default (baseline, cleaned) metric file paths."""
    base_dir = Path("data/processed")
    return (base_dir / "baseline_metrics.json", base_dir / "cleaned_metrics.json")

def load_baseline_metrics() -> Dict[str, Any]:
    """Load the baseline metrics JSON."""
    baseline_path, _ = _default_metrics_path()
    return load_json_file(baseline_path)

def load_cleaned_metrics() -> Dict[str, Any]:
    """Load the cleaned metrics JSON."""
    _, cleaned_path = _default_metrics_path()
    return load_json_file(cleaned_path)

# --------------------------------------------------------------------------- #
# Core comparison logic
# --------------------------------------------------------------------------- #
def _extract_p_value(entry: Dict[str, Any]) -> float | None:
    """Extract the p‑value from a metric entry."""
    # Expected location: entry["t_test"]["p_value"]
    try:
        return float(entry["t_test"]["p_value"])
    except Exception:
        return None

def _extract_ci_width(entry: Dict[str, Any]) -> float | None:
    """Extract the confidence‑interval width from a metric entry."""
    try:
        ci = entry["t_test"]["ci"]
        if isinstance(ci, list) and len(ci) == 2:
            low, high = map(float, ci)
            return round(high - low, 2)  # 2‑decimal precision as required
    except Exception:
        pass
    return None

def _extract_effect_size(entry: Dict[str, Any]) -> float | None:
    """Extract an effect‑size metric.

    The spec mentions Cohen's d for t‑tests and R² for regressions.
    We look for common keys.
    """
    # Prefer explicit keys
    for key in ("cohen_d", "effect_size", "r_squared", "r2"):
        if key in entry:
            try:
                return float(entry[key])
            except Exception:
                continue
    # Fallback: look inside a ``regression`` block
    try:
        return float(entry["regression"]["effect_size"])
    except Exception:
        pass
    return None

def calculate_absolute_diff(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Compute absolute differences between cleaned and baseline metrics.

    Returns a dict keyed by dataset name with sub‑keys:
    ``p_value_diff``, ``ci_width_diff``, ``effect_size_diff``.
    All numeric values are rounded to the required precision.
    """
    diffs: Dict[str, Dict[str, Any]] = {}
    for ds_name, base_entry in baseline.items():
        clean_entry = cleaned.get(ds_name)
        if not clean_entry:
            logger.warning("Dataset %s missing from cleaned metrics", ds_name)
            continue

        p_base = _extract_p_value(base_entry)
        p_clean = _extract_p_value(clean_entry)
        ci_base = _extract_ci_width(base_entry)
        ci_clean = _extract_ci_width(clean_entry)
        es_base = _extract_effect_size(base_entry)
        es_clean = _extract_effect_size(clean_entry)

        ds_diff: Dict[str, Any] = {}
        if p_base is not None and p_clean is not None:
            ds_diff["p_value_diff"] = round(abs(p_clean - p_base), 3)
        if ci_base is not None and ci_clean is not None:
            ds_diff["ci_width_diff"] = round(abs(ci_clean - ci_base), 2)
        if es_base is not None and es_clean is not None:
            ds_diff["effect_size_diff"] = round(abs(es_clean - es_base), 3)

        diffs[ds_name] = ds_diff
    return diffs

def calculate_relative_diff(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Compute relative differences (|clean‑base| / |base|) for each metric.

    Returns a dict keyed by dataset name with sub‑keys:
    ``p_value_rel``, ``ci_width_rel``, ``effect_size_rel``.
    Results are rounded to three decimal places.
    """
    rels: Dict[str, Dict[str, Any]] = {}
    for ds_name, base_entry in baseline.items():
        clean_entry = cleaned.get(ds_name)
        if not clean_entry:
            continue

        p_base = _extract_p_value(base_entry)
        p_clean = _extract_p_value(clean_entry)
        ci_base = _extract_ci_width(base_entry)
        ci_clean = _extract_ci_width(clean_entry)
        es_base = _extract_effect_size(base_entry)
        es_clean = _extract_effect_size(clean_entry)

        ds_rel: Dict[str, Any] = {}
        if p_base and p_base != 0:
            ds_rel["p_value_rel"] = round(abs(p_clean - p_base) / abs(p_base), 3)
        if ci_base and ci_base != 0:
            ds_rel["ci_width_rel"] = round(abs(ci_clean - ci_base) / abs(ci_base), 3)
        if es_base and es_base != 0:
            ds_rel["effect_size_rel"] = round(abs(es_clean - es_base) / abs(es_base), 3)

        rels[ds_name] = ds_rel
    return rels

def calculate_inconsistency_rate(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
    alpha: float = 0.05,
) -> float:
    """Proportion of datasets where significance status changes after cleaning.

    Significance is defined as p‑value < *alpha*.
    """
    total = 0
    changed = 0
    for ds_name, base_entry in baseline.items():
        clean_entry = cleaned.get(ds_name)
        if not clean_entry:
            continue
        p_base = _extract_p_value(base_entry)
        p_clean = _extract_p_value(clean_entry)
        if p_base is None or p_clean is None:
            continue
        total += 1
        sig_base = p_base < alpha
        sig_clean = p_clean < alpha
        if sig_base != sig_clean:
            changed += 1
    if total == 0:
        logger.warning("No datasets with comparable p‑values for inconsistency rate")
        return 0.0
    rate = round(changed / total, 3)
    logger.info("Inconsistency rate: %d / %d = %.3f", changed, total, rate)
    return rate

def generate_comparison_report() -> Dict[str, Any]:
    """Create a full comparison report.

    The report contains:
    - ``absolute_diff``: output of :func:`calculate_absolute_diff`
    - ``relative_diff``: output of :func:`calculate_relative_diff`
    - ``inconsistency_rate``: output of :func:`calculate_inconsistency_rate`
    - ``metadata``: timestamps and source file locations
    """
    baseline = load_baseline_metrics()
    cleaned = load_cleaned_metrics()

    report: Dict[str, Any] = {
        "absolute_diff": calculate_absolute_diff(baseline, cleaned),
        "relative_diff": calculate_relative_diff(baseline, cleaned),
        "inconsistency_rate": calculate_inconsistency_rate(baseline, cleaned),
        "metadata": {
            "baseline_path": str(Path("data/processed/baseline_metrics.json")),
            "cleaned_path": str(Path("data/processed/cleaned_metrics.json")),
        },
    }
    logger.debug("Generated comparison report with %d datasets", len(report["absolute_diff"]))
    return report

# --------------------------------------------------------------------------- #
# Script entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """Entry point for ``python code/reporting.py``.

    The function generates the comparison report and stores it at
    ``data/processed/comparison_report.json``.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger.info("Generating comparison report...")
    report = generate_comparison_report()
    output_path = Path("data/processed/comparison_report.json")
    save_json_file(report, output_path)
    logger.info("Comparison report written to %s", output_path)

if __name__ == "__main__":
    main()
