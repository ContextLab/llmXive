"""
T030 – Dataset Size Binning Sensitivity Analysis
------------------------------------------------
This script implements the sensitivity analysis required by task **T030**.
It loads the baseline and cleaned metric artifacts, extracts the number of
observations for each dataset, groups the datasets into three size bins
(``<50``, ``50‑200`` and ``>200``), computes simple summary statistics for
each bin and writes the results to ``data/processed/dataset_size_sensitivity.json``.

The implementation is deliberately defensive:
* All file‑system interactions create parent directories if they do not exist.
* Missing keys or malformed entries are ignored but logged.
* If a bin receives no datasets a ``CONSTRAINT_VIOLATION`` warning is emitted
  and the script continues.
* If **any** bin contains fewer than one dataset a generic warning is emitted.

The script can be executed directly::

    python code/t030_dataset_size_sensitivity.py

It is also import‑safe – the public functions are listed in ``__all__``.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Local utilities ---------------------------------------------------------

from utils import setup_logging  # type: ignore  # tolerant import per project contract
from config import get_config   # type: ignore

__all__ = [
    "load_json",
    "load_baseline_metrics",
    "load_cleaned_metrics",
    "extract_dataset_info",
    "bin_dataset_size",
    "analyze_size_bin",
    "run_sensitivity_analysis",
    "write_output",
    "main",
]

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load a JSON file and return its content as a dictionary.
    Returns an empty dict if the file does not exist or cannot be parsed.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("File not found: %s", filepath)
    except json.JSONDecodeError as exc:
        logging.error("Invalid JSON in %s: %s", filepath, exc)
    return {}

def load_baseline_metrics() -> List[Dict[str, Any]]:
    """
    Load the baseline metrics artifact.
    Expected format: a list of per‑dataset metric dictionaries.
    """
    config = get_config()
    baseline_path = config.get(
        "BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"
    )
    data = load_json(baseline_path)
    # The artifact may be a dict with a ``datasets`` key or a raw list.
    if isinstance(data, dict) and "datasets" in data:
        return data["datasets"]
    if isinstance(data, list):
        return data
    logging.warning("Baseline metrics format unexpected – returning empty list.")
    return []

def load_cleaned_metrics() -> List[Dict[str, Any]]:
    """
    Load the cleaned metrics artifact.
    Expected format mirrors ``load_baseline_metrics``.
    """
    config = get_config()
    cleaned_path = config.get(
        "CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json"
    )
    data = load_json(cleaned_path)
    if isinstance(data, dict) and "datasets" in data:
        return data["datasets"]
    if isinstance(data, list):
        return data
    logging.warning("Cleaned metrics format unexpected – returning empty list.")
    return []

def extract_dataset_info(
    baseline_entry: Dict[str, Any], cleaned_entry: Dict[str, Any] | None = None
) -> Tuple[str, int, Dict[str, Any]]:
    """
    Pull the dataset identifier and its size (number of rows) from a baseline
    entry.  The size field may appear under several possible keys – we try them
    in order of likelihood.

    Returns:
        (dataset_name, n_rows, baseline_entry)
    """
    # Prefer explicit fields, fall back to generic ones.
    name = (
        baseline_entry.get("dataset_name")
        or baseline_entry.get("name")
        or baseline_entry.get("id")
        or "unknown_dataset"
    )
    size = (
        baseline_entry.get("n_rows")
        or baseline_entry.get("dataset_size")
        or baseline_entry.get("num_samples")
        or baseline_entry.get("size")
        or 0
    )
    if not isinstance(size, int):
        try:
            size = int(size)
        except Exception:
            logging.warning("Non‑integer size for %s – defaulting to 0.", name)
            size = 0
    return name, size, baseline_entry

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset to a size bin.

    Bins:
        - ``small``   : n < 50
        - ``medium``  : 50 ≤ n ≤ 200
        - ``large``   : n > 200
    """
    if n_rows < 50:
        return "small"
    if n_rows <= 200:
        return "medium"
    return "large"

def analyze_size_bin(
    bin_name: str,
    entries: List[Tuple[Dict[str, Any], Dict[str, Any] | None]],
) -> Dict[str, Any]:
    """
    Compute simple aggregated statistics for a single size bin.

    Currently we compute:
        * ``dataset_count`` – number of datasets in the bin
        * ``mean_p_value_shift`` – average absolute difference in p‑values
          between cleaned and baseline (if cleaned metrics are supplied)
        * ``mean_ci_width_change`` – average absolute change in CI width
          (if the relevant fields exist)

    The function is tolerant of missing values – any metric that cannot be
    computed is omitted from the aggregation.
    """
    p_shifts: List[float] = []
    ci_changes: List[float] = []

    for baseline_entry, cleaned_entry in entries:
        # Baseline p‑value
        base_p = baseline_entry.get("p_value")
        if cleaned_entry is not None:
            clean_p = cleaned_entry.get("p_value")
            if isinstance(base_p, (int, float)) and isinstance(
                clean_p, (int, float)
            ):
                p_shifts.append(abs(clean_p - base_p))

        # CI width change – we expect a ``ci`` field like [low, high]
        base_ci = baseline_entry.get("ci")
        if cleaned_entry is not None:
            clean_ci = cleaned_entry.get("ci")
            if (
                isinstance(base_ci, (list, tuple))
                and isinstance(clean_ci, (list, tuple))
                and len(base_ci) == 2
                and len(clean_ci) == 2
            ):
                base_width = base_ci[1] - base_ci[0]
                clean_width = clean_ci[1] - clean_ci[0]
                ci_changes.append(abs(clean_width - base_width))

    result: Dict[str, Any] = {"dataset_count": len(entries)}
    if p_shifts:
        result["mean_p_value_shift"] = round(sum(p_shifts) / len(p_shifts), 3)
    if ci_changes:
        result["mean_ci_width_change"] = round(sum(ci_changes) / len(ci_changes), 3)
    return result

def run_sensitivity_analysis(
    baseline_metrics: List[Dict[str, Any]],
    cleaned_metrics: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Perform the full size‑bin sensitivity analysis.

    Steps:
        1. Pair baseline and cleaned entries by dataset name.
        2. Extract size information from the baseline entry.
        3. Bin each dataset.
        4. Aggregate per‑bin statistics via ``analyze_size_bin``.
    """
    # Build a lookup for cleaned metrics keyed by dataset identifier.
    cleaned_lookup: Dict[str, Dict[str, Any]] = {}
    for entry in cleaned_metrics:
        key = (
            entry.get("dataset_name")
            or entry.get("name")
            or entry.get("id")
            or ""
        )
        if key:
            cleaned_lookup[key] = entry

    # Organise entries per bin.
    bins: Dict[str, List[Tuple[Dict[str, Any], Dict[str, Any] | None]]] = {
        "small": [],
        "medium": [],
        "large": [],
    }

    for base_entry in baseline_metrics:
        name, size, _ = extract_dataset_info(base_entry)
        bin_name = bin_dataset_size(size)
        cleaned_entry = cleaned_lookup.get(name)
        bins[bin_name].append((base_entry, cleaned_entry))

    # Analyse each bin.
    analysis: Dict[str, Any] = {}
    for bin_name, entries in bins.items():
        if not entries:
            logging.warning(
                "CONSTRAINT_VIOLATION: size bin '%s' received no datasets.", bin_name
            )
        analysis[bin_name] = analyze_size_bin(bin_name, entries)

    # Global warning if any bin is empty.
    empty_bins = [b for b, v in bins.items() if not v]
    if empty_bins:
        logging.warning(
            "Size binning produced empty bins %s – results may be sparse.", empty_bins
        )
    return {"size_bins": analysis, "total_datasets": len(baseline_metrics)}

def write_output(result: Dict[str, Any], output_path: str) -> None:
    """
    Serialize ``result`` to ``output_path`` as pretty‑printed JSON.
    The parent directory is created automatically.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    logging.info("Dataset‑size sensitivity analysis written to %s", output_path)

# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------

def main() -> None:
    """
    Orchestrates the size‑bin sensitivity analysis.
    """
    # Initialise logging – the project’s ``setup_logging`` accepts a log level
    # argument but also works without one, so we call it with the default.
    logger = setup_logging("INFO")
    if isinstance(logger, logging.Logger):
        # ``setup_logging`` may return a logger or ``None``; we ensure a logger.
        logging.getLogger().handlers = logger.handlers
        logging.getLogger().setLevel(logger.level)

    logging.info("Starting dataset size binning sensitivity analysis (T030)")

    baseline = load_baseline_metrics()
    if not baseline:
        logging.error("No baseline metrics found – aborting T030.")
        return

    cleaned = load_cleaned_metrics()
    if not cleaned:
        logging.error("No cleaned metrics found – aborting T030.")
        return

    result = run_sensitivity_analysis(baseline, cleaned)

    config = get_config()
    output_path = config.get(
        "SIZE_SENSITIVITY_OUTPUT_PATH",
        "data/processed/dataset_size_sensitivity.json",
    )
    write_output(result, output_path)

if __name__ == "__main__":
    main()