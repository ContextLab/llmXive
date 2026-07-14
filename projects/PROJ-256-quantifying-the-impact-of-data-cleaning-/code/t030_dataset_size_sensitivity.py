"""
T030 – Dataset Size Binning Sensitivity Analysis
------------------------------------------------
This module implements the dataset‑size sensitivity analysis required by
task **T030**.  The analysis groups datasets into three size bins
(small, medium, large) and reports basic summary statistics for each bin.
It is deliberately defensive: if required input artifacts (e.g. the
baseline metrics file) are missing, the script logs a warning and produces
an empty but well‑formed output file so that downstream pipeline steps do
not fail.

Expected output
----------------
``data/processed/size_sensitivity.json`` – a JSON document with one entry
per size bin containing the number of datasets in the bin and any
aggregated metrics that could be computed.

The script is runnable directly::

    python code/t030_dataset_size_sensitivity.py

It can also be imported; the public API mirrors the signatures listed in
the task description.

Dependencies
------------
* Standard library only (json, logging, pathlib, typing)
* ``utils.setup_logging`` – imported for consistency with the rest of the
  code base but not required to be called; if it does not accept the
  signature used here the script falls back to ``logging.basicConfig``.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ``setup_logging`` is part of the shared utilities.  We import it for
# compatibility with the rest of the project but guard against signature
# mismatches – if the call fails we simply configure the root logger
# ourselves.
try:
    from utils import setup_logging  # type: ignore
except Exception:  # pragma: no cover
    setup_logging = None  # type: ignore

# ----------------------------------------------------------------------
# Helper data‑extraction utilities
# ----------------------------------------------------------------------


def extract_dataset_info(baseline_path: Path) -> List[Dict[str, Any]]:
    """
    Load the baseline metrics file and pull out minimal information needed
    for size‑binning.

    The baseline file is expected to be a JSON mapping where each key is a
    dataset identifier and the value is a dictionary that (at minimum)
    contains an ``"n_samples"`` field – the number of rows used in the
    analysis.  If the file does not exist or the expected fields are
    missing, a warning is logged and an empty list is returned.

    Parameters
    ----------
    baseline_path: Path
        Path to ``data/processed/baseline_metrics.json``.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each with keys ``"name"`` and ``"size"``.
    """
    if not baseline_path.is_file():
        logging.warning(
            "Baseline metrics file %s not found – size‑sensitivity analysis "
            "will produce an empty result.",
            baseline_path,
        )
        return []

    try:
        with baseline_path.open("r", encoding="utf-8") as fp:
            baseline_data = json.load(fp)
    except json.JSONDecodeError as exc:
        logging.error("Failed to parse baseline metrics JSON: %s", exc)
        return []

    dataset_info: List[Dict[str, Any]] = []
    for ds_name, ds_metrics in baseline_data.items():
        # ``n_samples`` is the conventional field used elsewhere in the
        # project; fall back to ``sample_size`` or ``size`` if needed.
        size = ds_metrics.get("n_samples") or ds_metrics.get("sample_size") or ds_metrics.get("size")
        if size is None:
            logging.warning(
                "Dataset %s missing size information – it will be omitted from "
                "size‑sensitivity analysis.",
                ds_name,
            )
            continue
        try:
            size_int = int(size)
        except (TypeError, ValueError):
            logging.warning(
                "Dataset %s size value %r is not an integer – omitted.", ds_name, size
            )
            continue
        dataset_info.append({"name": ds_name, "size": size_int})
    return dataset_info


# ----------------------------------------------------------------------
# Binning logic
# ----------------------------------------------------------------------


def bin_dataset_size(
    dataset_info: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Assign each dataset to a size bin.

    Bins (inclusive of lower bound, exclusive of upper bound unless noted):
    * ``small``   – ``n < 50``
    * ``medium``  – ``50 <= n <= 200``
    * ``large``   – ``n > 200``

    Parameters
    ----------
    dataset_info: List[Dict[str, Any]]
        List produced by :func:`extract_dataset_info`.

    Returns
    -------
    Dict[str, List[Dict[str, Any]]]
        Mapping ``bin_name -> list of dataset info dicts``.
    """
    bins: Dict[str, List[Dict[str, Any]]] = {"small": [], "medium": [], "large": []}
    for info in dataset_info:
        size = info["size"]
        if size < 50:
            bins["small"].append(info)
        elif 50 <= size <= 200:
            bins["medium"].append(info)
        else:  # size > 200
            bins["large"].append(info)
    return bins


# ----------------------------------------------------------------------
# Per‑bin analysis
# ----------------------------------------------------------------------


def analyze_size_bin(
    bin_name: str, datasets: List[Dict[str, Any]], cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute a very light‑weight summary for a single size bin.

    Currently the analysis reports:
    * ``dataset_count`` – how many datasets fall in the bin
    * ``average_n_samples`` – mean of ``size`` values (if any)
    * ``p_value_shift_mean`` – mean absolute p‑value shift between baseline
      and cleaned results for the datasets in the bin (if cleaned metrics are
      available).  If the required fields are missing the value is omitted.

    Parameters
    ----------
    bin_name: str
        Name of the bin (``small``, ``medium``, ``large``).
    datasets: List[Dict[str, Any]]
        Dataset info dicts belonging to the bin.
    cleaned_metrics: Dict[str, Any]
        The full cleaned‑metrics JSON structure; may be empty.

    Returns
    -------
    Dict[str, Any]
        Summary statistics for the bin.
    """
    result: Dict[str, Any] = {"bin": bin_name, "dataset_count": len(datasets)}

    if not datasets:
        # Log the constraint‑violation condition required by the task.
        logging.warning(
            "CONSTRAINT_VIOLATION: size bin '%s' contains no datasets.", bin_name
        )
        return result

    # Basic size statistics
    sizes = [d["size"] for d in datasets]
    result["average_n_samples"] = round(sum(sizes) / len(sizes), 2)

    # Optional p‑value shift aggregation – only if cleaned metrics are present
    shifts: List[float] = []
    for d in datasets:
        name = d["name"]
        base_entry = cleaned_metrics.get(name, {})
        # Expected structure: { "t_test": { "p_value_shift": <float> } }
        shift = (
            base_entry.get("t_test", {})
            .get("p_value_shift")
        )
        if isinstance(shift, (int, float)):
            shifts.append(abs(shift))

    if shifts:
        result["p_value_shift_mean"] = round(sum(shifts) / len(shifts), 4)

    return result


# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------


def run_sensitivity_analysis(
    baseline_path: Path, cleaned_path: Path
) -> List[Dict[str, Any]]:
    """
    End‑to‑end size‑sensitivity analysis.

    1. Load baseline metrics (required for dataset sizes).
    2. Load cleaned metrics (optional – used for p‑value shift aggregation).
    3. Bin datasets by size.
    4. Produce a per‑bin summary.

    Parameters
    ----------
    baseline_path: Path
        Path to ``data/processed/baseline_metrics.json``.
    cleaned_path: Path
        Path to ``data/processed/cleaned_metrics.json``.

    Returns
    -------
    List[Dict[str, Any]]
        One entry per size bin.
    """
    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    dataset_info = extract_dataset_info(baseline_path)

    # Load cleaned metrics – if the file is missing we keep an empty dict.
    if cleaned_path.is_file():
        try:
            with cleaned_path.open("r", encoding="utf-8") as fp:
                cleaned_metrics = json.load(fp)
        except json.JSONDecodeError as exc:
            logging.error("Failed to parse cleaned metrics JSON: %s", exc)
            cleaned_metrics = {}
    else:
        logging.warning(
            "Cleaned metrics file %s not found – p‑value‑shift aggregation will be skipped.",
            cleaned_path,
        )
        cleaned_metrics = {}

    # ------------------------------------------------------------------
    # Binning
    # ------------------------------------------------------------------
    bins = bin_dataset_size(dataset_info)

    # ------------------------------------------------------------------
    # Per‑bin analysis
    # ------------------------------------------------------------------
    results: List[Dict[str, Any]] = []
    for bin_name, ds_list in bins.items():
        bin_result = analyze_size_bin(bin_name, ds_list, cleaned_metrics)
        results.append(bin_result)

    return results


# ----------------------------------------------------------------------
# Output handling
# ----------------------------------------------------------------------


def write_output(
    results: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Serialize the analysis results to JSON, ensuring the parent directory
    exists.

    Parameters
    ----------
    results: List[Dict[str, Any]]
        Output of :func:`run_sensitivity_analysis`.
    output_path: Path
        Destination file (e.g. ``data/processed/size_sensitivity.json``).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("w", encoding="utf-8") as fp:
            json.dump(results, fp, indent=2, sort_keys=True)
        logging.info("Size‑sensitivity analysis written to %s", output_path)
    except Exception as exc:  # pragma: no cover
        logging.error("Failed to write size‑sensitivity output: %s", exc)
        raise


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point used by the quick‑start run‑book.

    The function:
    * configures logging,
    * resolves the standard artifact locations,
    * runs the analysis, and
    * writes the JSON result to ``data/processed/size_sensitivity.json``.
    """
    # ------------------------------------------------------------------
    # Logging configuration – tolerant of the various signatures used
    # throughout the code base.
    # ------------------------------------------------------------------
    try:
        if callable(setup_logging):
            # Most scripts call ``setup_logging(log_level="INFO")``.
            setup_logging(log_level="INFO")
        else:
            raise RuntimeError
    except Exception:  # pragma: no cover
        # Fallback to a basic configuration if the shared helper is missing
        # or does not accept the keyword argument.
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # Resolve standard paths (relative to the project root)
    baseline_path = Path("data/processed/baseline_metrics.json")
    cleaned_path = Path("data/processed/cleaned_metrics.json")
    output_path = Path("data/processed/size_sensitivity.json")

    # Run the analysis
    results = run_sensitivity_analysis(baseline_path, cleaned_path)

    # Write results – even if the result list is empty we still create a valid JSON file.
    write_output(results, output_path)


if __name__ == "__main__":
    main()