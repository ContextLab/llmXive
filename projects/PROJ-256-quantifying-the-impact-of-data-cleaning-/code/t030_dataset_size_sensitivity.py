"""
T030 – Dataset size binning sensitivity analysis

This script reads the baseline and cleaned metric JSON files, extracts the
number of observations for each dataset, bins the datasets by size
(n < 50, 50 – 200, > 200) and computes aggregate statistics per bin.
It logs a warning if any bin contains fewer than one dataset
(CONSTRAINT_VIOLATION) and always writes its results to
``data/processed/dataset_size_sensitivity.json``.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils import setup_logging

logger = setup_logging("INFO")

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
BASELINE_PATH = Path("data/processed/baseline_metrics.json")
CLEANED_PATH = Path("data/processed/cleaned_metrics.json")
OUTPUT_PATH = Path("data/processed/dataset_size_sensitivity.json")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_baseline_metrics() -> List[Dict[str, Any]]:
    """Load baseline metrics; return empty list if file missing."""
    if not BASELINE_PATH.is_file():
        logger.warning(f"Baseline metrics file not found at {BASELINE_PATH}. Returning empty list.")
        return []
    with BASELINE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Expecting a mapping of dataset name -> metric dict
    return [{"dataset_name": k, **v} for k, v in data.items()]

def load_cleaned_metrics() -> List[Dict[str, Any]]:
    """Load cleaned metrics; return empty list if file missing."""
    if not CLEANED_PATH.is_file():
        logger.warning(f"Cleaned metrics file not found at {CLEANED_PATH}. Returning empty list.")
        return []
    with CLEANED_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [{"dataset_name": k, **v} for k, v in data.items()]

def extract_dataset_info(metrics: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    """
    From a list of metric dictionaries, pull (dataset_name, n_samples).
    The expected key for sample size is ``n_samples``; if absent we try
    ``sample_size`` or fall back to 0.
    """
    info = []
    for entry in metrics:
        name = entry.get("dataset_name", "unknown")
        n = entry.get("n_samples") or entry.get("sample_size") or 0
        try:
            n = int(n)
        except Exception:
            n = 0
        info.append((name, n))
    return info

def bin_dataset_size(info: List[Tuple[str, int]]) -> Dict[str, List[Tuple[str, int]]]:
    """
    Bin datasets according to size:
    - ``small`` : n < 50
    - ``medium``: 50 <= n <= 200
    - ``large`` : n > 200
    Returns a dict mapping bin label to list of (name, n) tuples.
    """
    bins = {"small": [], "medium": [], "large": []}
    for name, n in info:
        if n < 50:
            bins["small"].append((name, n))
        elif 50 <= n <= 200:
            bins["medium"].append((name, n))
        else:
            bins["large"].append((name, n))
    return bins

def analyze_size_bin(
    bin_name: str,
    entries: List[Tuple[str, int]],
    baseline_lookup: Dict[str, Dict[str, Any]],
    cleaned_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute aggregate statistics for a single size bin.

    For each dataset present in the bin we calculate the absolute p‑value
    shift (|p_cleaned – p_baseline|).  The function returns the mean shift,
    median shift and the count of datasets in the bin.
    """
    if not entries:
        logger.warning(
            f"CONSTRAINT_VIOLATION: Size bin '{bin_name}' contains no datasets."
        )
        return {"count": 0, "mean_shift": None, "median_shift": None}

    shifts = []
    for name, _ in entries:
        base = baseline_lookup.get(name, {})
        clean = cleaned_lookup.get(name, {})
        base_p = base.get("t_test", {}).get("p_value")
        clean_p = clean.get("t_test", {}).get("p_value")
        if base_p is not None and clean_p is not None:
            try:
                shift = abs(float(clean_p) - float(base_p))
                shifts.append(shift)
            except Exception:
                continue

    if not shifts:
        return {"count": len(entries), "mean_shift": None, "median_shift": None}

    mean_shift = sum(shifts) / len(shifts)
    median_shift = sorted(shifts)[len(shifts) // 2]

    return {
        "count": len(entries),
        "mean_shift": round(mean_shift, 3),
        "median_shift": round(median_shift, 3),
    }

def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Orchestrates the full sensitivity analysis workflow.
    Returns a dictionary ready to be persisted as JSON.
    """
    baseline_metrics = load_baseline_metrics()
    cleaned_metrics = load_cleaned_metrics()

    # Build quick‑lookup dicts by dataset name.
    baseline_lookup = {m["dataset_name"]: m for m in baseline_metrics}
    cleaned_lookup = {m["dataset_name"]: m for m in cleaned_metrics}

    # Extract size information from *both* sets (they should align).
    size_info = extract_dataset_info(baseline_metrics or cleaned_metrics)

    binned = bin_dataset_size(size_info)

    # Log warning if any bin lacks datasets.
    for bin_name, entries in binned.items():
        if len(entries) == 0:
            logger.warning(
                f"CONSTRAINT_VIOLATION: No datasets fall into size bin '{bin_name}'."
            )
        else:
            logger.info(f"Size bin '{bin_name}' contains {len(entries)} dataset(s).")

    # Compute per‑bin statistics.
    results = {}
    for bin_name, entries in binned.items():
        results[bin_name] = analyze_size_bin(
            bin_name, entries, baseline_lookup, cleaned_lookup
        )
    return results

def write_output(data: Dict[str, Any]) -> None:
    """Write the sensitivity analysis results to the declared output path."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Dataset size sensitivity analysis written to {OUTPUT_PATH}")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    logger.info("Starting dataset size sensitivity analysis (T030).")
    analysis_results = run_sensitivity_analysis()
    write_output(analysis_results)

if __name__ == "__main__":
    main()
