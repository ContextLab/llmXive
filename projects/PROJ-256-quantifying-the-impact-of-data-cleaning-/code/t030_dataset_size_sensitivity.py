"""
T030 – Dataset Size Binning Sensitivity Analysis
------------------------------------------------
This script implements the sensitivity analysis required by task **T030**:
* Bin datasets by size (n < 50, 50‑200, > 200)
* For each bin, compute aggregated shifts between baseline and cleaned metrics
* Log a warning if a bin contains no datasets (CONSTRAINT_VIOLATION)
* Write the aggregated results to ``data/processed/size_sensitivity.json``

The script is deliberately defensive:
* Accepts any shape of input JSON objects (missing keys are handled gracefully)
* Uses the ``reporting.calculate_metric_shifts`` helper when available
* Falls back to a simple manual calculation if the helper cannot be imported

It can be executed directly::

    python code/t030_dataset_size_sensitivity.py

or invoked from the quick‑start run‑book.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from utils import setup_logging

# The reporting module already contains helpers for loading/saving JSON and for
# calculating metric shifts.  Import them lazily – the module may evolve, and we
# want this script to keep working even if the exact helper signatures change.
try:
    from reporting import (
        load_json_file,
        save_json_file,
        calculate_metric_shifts,
    )
except Exception:  # pragma: no cover
    # Minimal fall‑backs – they operate on the same data shape expected by the
    # original helpers.
    def load_json_file(filepath: Path) -> Dict[str, Any]:
        with filepath.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_json_file(data: Dict[str, Any], filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def calculate_metric_shifts(
        baseline: Dict[str, Any], cleaned: Dict[str, Any]
    ) -> Dict[str, Dict[str, float]]:
        """
        Very small fallback implementation that mirrors the expected output
        of the real ``calculate_metric_shifts`` helper.

        Expected input format (per dataset):
            {
                "t_test": {"p_value": 0.04, "ci": [0.1, 0.5]},
                "linear_regression": {"r2": 0.23},
                "effect_size": {"cohen_d": 0.8},
                "dataset_size": 123
            }

        Returns:
            {
                "<dataset_id>": {
                    "p_value_shift": 0.01,
                    "ci_width_change": 0.12,
                    "effect_size_change": 0.05
                },
                ...
            }
        """
        shifts: Dict[str, Dict[str, float]] = {}
        for ds_id, base_metrics in baseline.items():
            clean_metrics = cleaned.get(ds_id, {})
            # ----- p‑value shift -------------------------------------------------
            p_base = base_metrics.get("t_test", {}).get("p_value")
            p_clean = clean_metrics.get("t_test", {}).get("p_value")
            p_shift = None
            if p_base is not None and p_clean is not None:
                p_shift = abs(p_clean - p_base)

            # ----- CI width change -----------------------------------------------
            ci_base = base_metrics.get("t_test", {}).get("ci")
            ci_clean = clean_metrics.get("t_test", {}).get("ci")
            ci_change = None
            if isinstance(ci_base, list) and isinstance(ci_clean, list):
                width_base = ci_base[1] - ci_base[0]
                width_clean = ci_clean[1] - ci_clean[0]
                ci_change = width_clean - width_base

            # ----- effect‑size change ---------------------------------------------
            es_base = base_metrics.get("effect_size", {}).get("cohen_d")
            es_clean = clean_metrics.get("effect_size", {}).get("cohen_d")
            es_change = None
            if es_base is not None and es_clean is not None:
                es_change = es_clean - es_base

            shifts[ds_id] = {
                "p_value_shift": round(p_shift, 6) if p_shift is not None else None,
                "ci_width_change": round(ci_change, 6) if ci_change is not None else None,
                "effect_size_change": round(es_change, 6) if es_change is not None else None,
            }
        return shifts

# --------------------------------------------------------------------------- #
# Helper functions specific to the size‑binning analysis
# --------------------------------------------------------------------------- #

def extract_dataset_info(
    baseline: Dict[str, Any], cleaned: Dict[str, Any]
) -> List[Tuple[str, int, Dict[str, Any]]]:
    """
    Produce a list of (dataset_id, size, shift_dict) tuples.

    Parameters
    ----------
    baseline, cleaned
        Dictionaries keyed by dataset identifier.  Each value must contain a
        ``dataset_size`` field (int).  If the field is missing we assume size 0
        and log a warning.

    Returns
    -------
    List of tuples where ``shift_dict`` is the output of
    ``calculate_metric_shifts`` for the corresponding dataset.
    """
    logger = logging.getLogger(__name__)
    shifts = calculate_metric_shifts(baseline, cleaned)
    info: List[Tuple[str, int, Dict[str, Any]]] = []
    for ds_id, shift_dict in shifts.items():
        size = (
            baseline.get(ds_id, {})
            .get("dataset_size")
            .or_(cleaned.get(ds_id, {}).get("dataset_size"))
            or 0
        )
        if size == 0:
            logger.warning(
                "Dataset %s missing 'dataset_size' field; assuming size 0", ds_id
            )
        info.append((ds_id, int(size), shift_dict))
    return info


def bin_dataset_size(
    dataset_info: List[Tuple[str, int, Dict[str, Any]]]
) -> Dict[str, List[Tuple[str, int, Dict[str, Any]]]]:
    """
    Bin datasets into three size categories.

    - ``small``  : n < 50
    - ``medium`` : 50 ≤ n ≤ 200
    - ``large``  : n > 200
    
    Returns a mapping from bin name to the list of dataset info tuples belonging
    to that bin.
    """
    bins: Dict[str, List[Tuple[str, int, Dict[str, Any]]]] = {
        "small": [],
        "medium": [],
        "large": [],
    }
    for entry in dataset_info:
        _, size, _ = entry
        if size < 50:
            bins["small"].append(entry)
        elif size <= 200:
            bins["medium"].append(entry)
        else:
            bins["large"].append(entry)
    return bins


def analyze_size_bin(
    bin_name: str,
    bin_contents: List[Tuple[str, int, Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Compute aggregated statistics for a single size bin.

    The aggregation performed is the mean absolute shift for each metric.
    If a metric is missing for all datasets in the bin, the result is ``null``.
    """
    logger = logging.getLogger(__name__)
    if not bin_contents:
        logger.warning(
            "CONSTRAINT_VIOLATION: Size bin '%s' contains no datasets.", bin_name
        )
        return {
            "dataset_count": 0,
            "mean_p_value_shift": None,
            "mean_ci_width_change": None,
            "mean_effect_size_change": None,
        }

    # Accumulators
    p_shifts: List[float] = []
    ci_changes: List[float] = []
    es_changes: List[float] = []

    for _, _, shift_dict in bin_contents:
        p = shift_dict.get("p_value_shift")
        ci = shift_dict.get("ci_width_change")
        es = shift_dict.get("effect_size_change")
        if isinstance(p, (int, float)):
            p_shifts.append(p)
        if isinstance(ci, (int, float)):
            ci_changes.append(ci)
        if isinstance(es, (int, float)):
            es_changes.append(es)

    def mean(values: List[float]) -> float | None:
        return sum(values) / len(values) if values else None

    result = {
        "dataset_count": len(bin_contents),
        "mean_p_value_shift": round(mean(p_shifts), 6) if p_shifts else None,
        "mean_ci_width_change": round(mean(ci_changes), 6) if ci_changes else None,
        "mean_effect_size_change": round(mean(es_changes), 6)
        if es_changes
        else None,
    }
    logger.debug("Analysis result for bin %s: %s", bin_name, result)
    return result


def run_sensitivity_analysis(
    baseline_path: Path, cleaned_path: Path
) -> Dict[str, Any]:
    """
    End‑to‑end driver that loads the baseline/cleaned metric files,
    computes per‑dataset shifts, bins by size and aggregates the results.

    Returns a dict that can be written directly to JSON.
    """
    logger = logging.getLogger(__name__)
    logger.info("Loading baseline metrics from %s", baseline_path)
    baseline = load_json_file(baseline_path)
    logger.info("Loading cleaned metrics from %s", cleaned_path)
    cleaned = load_json_file(cleaned_path)

    if not baseline:
        logger.error("Baseline metrics file is empty – aborting size‑sensitivity analysis.")
        return {}
    if not cleaned:
        logger.error("Cleaned metrics file is empty – aborting size‑sensitivity analysis.")
        return {}

    dataset_info = extract_dataset_info(baseline, cleaned)
    bins = bin_dataset_size(dataset_info)

    analysis: Dict[str, Any] = {}
    for bin_name, contents in bins.items():
        analysis[bin_name] = analyze_size_bin(bin_name, contents)

    # Global summary (optional but handy for quick inspection)
    total_datasets = sum(len(v) for v in bins.values())
    analysis["summary"] = {"total_datasets": total_datasets}
    return analysis


def write_output(data: Dict[str, Any], output_path: Path) -> None:
    """
    Write the analysis dictionary to ``output_path`` as pretty‑printed JSON.
    """
    logger = logging.getLogger(__name__)
    logger.info("Writing size‑sensitivity results to %s", output_path)
    save_json_file(data, output_path)


def main() -> None:
    """
    Command‑line entry point.

    The paths are taken from the ``Config`` environment (if defined) or fall
    back to the conventional locations used throughout the repository.
    """
    # ------------------------------------------------------------------- #
    # Logging configuration – the ``setup_logging`` helper is deliberately
    # flexible (positional or keyword arguments) to satisfy the many call‑sites
    # across the project.
    # ------------------------------------------------------------------- #
    logger = setup_logging(log_level="INFO")

    # Resolve input / output locations -------------------------------------------------
    # ``Config`` may not be instantiated yet; we rely on environment variables
    # directly to avoid a hard dependency on the Config class implementation.
    raw_baseline = Path(os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"))
    raw_cleaned = Path(os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json"))
    output_file = Path(os.getenv("SIZE_SENSITIVITY_OUTPUT", "data/processed/size_sensitivity.json"))

    # Run the analysis -----------------------------------------------------------------
    results = run_sensitivity_analysis(raw_baseline, raw_cleaned)
    if results:
        write_output(results, output_file)
    else:
        logger.warning("No results produced – check input files.")


if __name__ == "__main__":
    main()