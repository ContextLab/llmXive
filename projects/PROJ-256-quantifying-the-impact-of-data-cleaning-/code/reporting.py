"""
Reporting utilities for the data cleaning impact project.

This module provides functions to load and save JSON artefacts, generate
comparison reports, and, importantly for task T1219, to correctly consume
cleaning‑function metadata and write ``cleaned_metrics.json`` with the exact
required fields:

- ``rows_removed`` (numeric)
- ``missing_before`` (numeric)
- ``missing_after`` (numeric)
- ``variance_reduction`` (numeric)

The implementation is deliberately lightweight and does not make any
assumptions about the surrounding pipeline beyond the paths used
throughout the repository. All paths are configurable via ``code/config.py``,
but sensible defaults are provided to keep the module usable in isolation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

# ----------------------------------------------------------------------
# Logging setup (uses the shared ``setup_logging`` utility if available)
# ----------------------------------------------------------------------
try:
    # ``setup_logging`` may accept either a positional log level or a named
    # argument; we accept both signatures.
    from utils import setup_logging  # type: ignore
    logger = setup_logging(log_level="INFO")
except Exception:
    # Fallback – a very simple logger configuration that never fails.
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions for generic JSON I/O
# ----------------------------------------------------------------------
def load_json_file(path: Union[str, Path]) -> Any:
    """Load a JSON file and return the decoded Python object."""
    path = Path(path)
    if not path.is_file():
        logger.warning(f"JSON file not found: {path}")
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(data: Any, path: Union[str, Path]) -> None:
    """Write *data* as pretty‑printed JSON to *path*."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=False)
    logger.info(f"Wrote JSON artefact to {path}")

# ----------------------------------------------------------------------
# Specific loaders for the artefacts used throughout the pipeline
# ----------------------------------------------------------------------
DEFAULT_BASELINE_PATH = Path("data/processed/baseline_metrics.json")
DEFAULT_CLEANED_PATH = Path("data/processed/cleaned_metrics.json")
DEFAULT_NULL_FPR_PATH = Path("data/processed/null_fpr_metrics.json")

def load_baseline_metrics(path: Union[str, Path] = DEFAULT_BASELINE_PATH) -> List[Dict[str, Any]]:
    """Load baseline metrics; returns an empty list if the file is missing."""
    data = load_json_file(path)
    return data if isinstance(data, list) else []

def load_cleaned_metrics(path: Union[str, Path] = DEFAULT_CLEANED_PATH) -> List[Dict[str, Any]]:
    """Load cleaned metrics; returns an empty list if the file is missing."""
    data = load_json_file(path)
    return data if isinstance(data, list) else []

def load_null_fpr_metrics(path: Union[str, Path] = DEFAULT_NULL_FPR_PATH) -> List[Dict[str, Any]]:
    """Load null‑FPR metrics; returns an empty list if the file is missing."""
    data = load_json_file(path)
    return data if isinstance(data, list) else []

# ----------------------------------------------------------------------
# Calculation helpers (simple implementations – the heavy‑lifting is done
# elsewhere in the pipeline)
# ----------------------------------------------------------------------
def calculate_absolute_diff(a: float, b: float) -> float:
    return abs(a - b)

def calculate_relative_diff(a: float, b: float) -> float:
    if a == 0:
        return 0.0
    return abs(a - b) / abs(a)

def calculate_inconsistency_rate(metrics: List[Dict[str, Any]]) -> float:
    """Placeholder: proportion of entries where the confidence intervals do not overlap."""
    # A real implementation would inspect the CI fields; here we simply count
    # entries that contain a key ``ci_overlap`` set to ``False``.
    if not metrics:
        return 0.0
    inconsistent = sum(1 for m in metrics if not m.get("ci_overlap", True))
    return inconsistent / len(metrics)

def calculate_fpr(null_fpr_metrics: List[Dict[str, Any]]) -> float:
    """Calculate the overall false‑positive‑rate from the null‑FPR artefact."""
    if not null_fpr_metrics:
        return 0.0
    # Assume each entry has a numeric ``fpr`` field.
    return sum(m.get("fpr", 0.0) for m in null_fpr_metrics) / len(null_fpr_metrics)

# ----------------------------------------------------------------------
# Core function required by T1219
# ----------------------------------------------------------------------
REQUIRED_CLEANED_FIELDS = [
    "rows_removed",
    "missing_before",
    "missing_after",
    "variance_reduction",
]

def _coerce_numeric(value: Any) -> float:
    """Coerce *value* to a float; non‑numeric values become 0.0."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def write_cleaned_metrics(
    metadata_list: List[Dict[str, Any]],
    output_path: Union[str, Path] = DEFAULT_CLEANED_PATH,
) -> List[Dict[str, Any]]:
    """
    Consume a list of *metadata* dictionaries produced by the cleaning
    functions and write ``cleaned_metrics.json`` containing **exactly** the
    required numeric fields.

    Parameters
    ----------
    metadata_list:
        List of dictionaries. Each dictionary may contain many keys, but
        only the four required fields are retained (and coerced to numeric
        types).

    output_path:
        Destination file. Parent directories are created automatically.

    Returns
    -------
    The list of cleaned dictionaries that were written to disk.
    """
    cleaned_records: List[Dict[str, Any]] = []
    for idx, raw in enumerate(metadata_list):
        record: Dict[str, Any] = {}
        for field in REQUIRED_CLEANED_FIELDS:
            record[field] = _coerce_numeric(raw.get(field, 0))
        cleaned_records.append(record)

    save_json_file(cleaned_records, output_path)
    logger.info(
        f"cleaned_metrics.json written with {len(cleaned_records)} records to {output_path}"
    )
    return cleaned_records

# ----------------------------------------------------------------------
# Comparison report generation (uses the cleaned metrics produced above)
# ----------------------------------------------------------------------
def generate_comparison_report(
    baseline_metrics: List[Dict[str, Any]],
    cleaned_metrics: List[Dict[str, Any]],
    output_path: Union[str, Path] = Path("data/processed/comparison_report.json"),
) -> Dict[str, Any]:
    """
    Produce a simple comparison report that pairs each baseline entry with
    its corresponding cleaned entry (by index) and stores absolute / relative
    differences for the numeric fields that appear in both artefacts.

    The function is deliberately tolerant: if the two lists differ in length,
    excess entries are ignored.
    """
    report: Dict[str, Any] = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "baseline_metrics": baseline_metrics,
        "cleaned_metrics": cleaned_metrics,
        "comparisons": [],
    }

    for base, clean in zip(baseline_metrics, cleaned_metrics):
        comparison: Dict[str, Any] = {"baseline": base, "cleaned": clean, "diffs": {}}
        for key in set(base.keys()).intersection(clean.keys()):
            try:
                base_val = _coerce_numeric(base[key])
                clean_val = _coerce_numeric(clean[key])
                comparison["diffs"][key] = {
                    "abs_diff": calculate_absolute_diff(base_val, clean_val),
                    "rel_diff": calculate_relative_diff(base_val, clean_val),
                }
            except Exception as exc:
                logger.debug(f"Unable to compare key {key}: {exc}")
        report["comparisons"].append(comparison)

    save_json_file(report, output_path)
    logger.info(f"Comparison report written to {output_path}")
    return report

# ----------------------------------------------------------------------
# FPR report generation (simple wrapper)
# ----------------------------------------------------------------------
def generate_fpr_report(
    null_fpr_metrics: List[Dict[str, Any]],
    output_path: Union[str, Path] = Path("data/processed/fpr_report.json"),
) -> Dict[str, Any]:
    """
    Write a tiny report containing the overall false‑positive‑rate.
    """
    fpr_value = calculate_fpr(null_fpr_metrics)
    report = {"fpr": fpr_value, "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z"}
    save_json_file(report, output_path)
    logger.info(f"FPR report written to {output_path}")
    return report

# ----------------------------------------------------------------------
# Placeholder artefact writer (used when upstream steps are optional)
# ----------------------------------------------------------------------
def write_placeholder_artefacts() -> None:
    """
    Ensure that all expected JSON artefacts exist, even if they are empty.
    This function is useful for quick‑start validation where later stages
    may be skipped.
    """
    for path in [
        DEFAULT_BASELINE_PATH,
        DEFAULT_CLEANED_PATH,
        DEFAULT_NULL_FPR_PATH,
        Path("data/processed/comparison_report.json"),
    ]:
        if not path.is_file():
            save_json_file([], path)

# ----------------------------------------------------------------------
# Public API export list (helps static analysers)
# ----------------------------------------------------------------------
__all__ = [
    "load_json_file",
    "save_json_file",
    "load_baseline_metrics",
    "load_cleaned_metrics",
    "load_null_fpr_metrics",
    "calculate_absolute_diff",
    "calculate_relative_diff",
    "calculate_inconsistency_rate",
    "calculate_fpr",
    "write_cleaned_metrics",
    "generate_comparison_report",
    "generate_fpr_report",
    "write_placeholder_artefacts",
]