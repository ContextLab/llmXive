"""
Dataset Size Binning Sensitivity Analysis (Task T030)

This script analyses how the size of a dataset influences the shift in statistical
metrics after cleaning. It reads the baseline and cleaned metric artifacts,
groups datasets into size bins (n < 50, 50‑200, > 200) and computes summary
statistics for each bin. The results are written to
``data/processed/dataset_size_sensitivity.json``.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

# Local utilities ---------------------------------------------------------

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def _load_metrics(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file that contains a list of per‑dataset metric dicts."""
    if not path.is_file():
        logging.getLogger().warning(f"Metrics file not found: {path}")
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Some scripts store a single dict with a ``datasets`` key
            data = data.get("datasets", [])
        return data if isinstance(data, list) else []
    except Exception as exc:
        logging.getLogger().error(f"Failed to read metrics from {path}: {exc}")
        return []

def extract_dataset_info(baseline_path: Path) -> List[Dict[str, Any]]:
    """
    Extract minimal dataset information required for binning.

    Each entry in the returned list contains at least:
        - ``name``: identifier of the dataset (from the metric entry)
        - ``n_rows``: number of rows (int, defaults to 0 if missing)
        - ``baseline_metrics``: the full metric dict for later use
    """
    baseline_metrics = _load_metrics(baseline_path)
    info = []
    for entry in baseline_metrics:
        name = entry.get("dataset_name") or entry.get("name") or "unknown"
        n_rows = entry.get("n_rows") or entry.get("sample_size") or 0
        info.append(
            {
                "name": name,
                "n_rows": int(n_rows),
                "baseline_metrics": entry,
            }
        )
    return info

def bin_dataset_size(info_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Bin datasets according to their row count.

    Bins:
        - ``small`` : n < 50
        - ``medium``: 50 <= n <= 200
        - ``large`` : n > 200
    """
    bins: Dict[str, List[Dict[str, Any]]] = {"small": [], "medium": [], "large": []}
    for info in info_list:
        n = info["n_rows"]
        if n < 50:
            bins["small"].append(info)
        elif 50 <= n <= 200:
            bins["medium"].append(info)
        else:
            bins["large"].append(info)
    return bins

def analyze_size_bin(
    bin_name: str,
    bin_contents: List[Dict[str, Any]],
    cleaned_metrics_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute summary statistics for a single size bin.

    For each dataset we compute the absolute p‑value shift between the baseline
    and the cleaned version (if a cleaned entry exists). The function returns
    the mean shift, median shift and the number of datasets in the bin.
    """
    shifts: List[float] = []
    for info in bin_contents:
        dataset_name = info["name"]
        baseline = info["baseline_metrics"]
        cleaned = cleaned_metrics_lookup.get(dataset_name)
        if not cleaned:
            continue
        # Extract p‑values – the exact JSON structure varies, so we look for common keys
        base_p = (
            baseline.get("t_test", {})
            .get("p_value")
            or baseline.get("p_value")
            or 1.0
        )
        clean_p = (
            cleaned.get("t_test", {})
            .get("p_value")
            or cleaned.get("p_value")
            or 1.0
        )
        try:
            shift = abs(float(clean_p) - float(base_p))
            shifts.append(shift)
        except Exception:
            continue

    if not shifts:
        avg_shift = median_shift = 0.0
    else:
        avg_shift = sum(shifts) / len(shifts)
        sorted_shifts = sorted(shifts)
        mid = len(sorted_shifts) // 2
        median_shift = (
            (sorted_shifts[mid - 1] + sorted_shifts[mid]) / 2.0
            if len(sorted_shifts) % 2 == 0
            else sorted_shifts[mid]
        )

    return {
        "bin": bin_name,
        "dataset_count": len(bin_contents),
        "average_p_value_shift": round(avg_shift, 3),
        "median_p_value_shift": round(median_shift, 3),
    }

def run_sensitivity_analysis(
    baseline_path: Path, cleaned_path: Path
) -> List[Dict[str, Any]]:
    """
    Orchestrates the full sensitivity analysis.

    Returns a list of per‑bin summary dictionaries.
    """
    logger = logging.getLogger(__name__)

    # Load metrics
    baseline_info = extract_dataset_info(baseline_path)
    cleaned_metrics = _load_metrics(cleaned_path)
    cleaned_lookup = {
        (m.get("dataset_name") or m.get("name") or f"idx_{i}"): m
        for i, m in enumerate(cleaned_metrics)
    }

    # Bin datasets by size
    size_bins = bin_dataset_size(baseline_info)

    # Log warnings if any bin is empty (constraint violation)
    for bin_name, contents in size_bins.items():
        if not contents:
            logger.warning(
                f"CONSTRAINT_VIOLATION: No datasets fall into size bin '{bin_name}'."
            )

    # Analyse each bin
    results = []
    for bin_name, contents in size_bins.items():
        result = analyze_size_bin(bin_name, contents, cleaned_lookup)
        results.append(result)

    return results

def write_output(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the analysis results to JSON with pretty formatting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"size_bin_analysis": results}, f, indent=2)
    logging.getLogger().info(f"Dataset size sensitivity analysis written to {output_path}")

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    Entry‑point for the T030 sensitivity analysis.

    Expected environment / config variables (via ``config.Config`` or defaults):
        - ``BASELINE_METRICS_PATH`` : path to baseline_metrics.json
        - ``CLEANED_METRICS_PATH`` : path to cleaned_metrics.json
        - ``SIZE_SENSITIVITY_OUTPUT``: path for the output JSON
    """
    # Initialise logging – the wrapper in utils.setup_logging is tolerant of
    # the many signatures used throughout the project.
    logger = setup_logging(log_level="INFO")
    logger.info("Starting dataset size binning sensitivity analysis (T030)")

    # Resolve paths (allowing overrides via environment variables)
    from config import get_config

    cfg = get_config()
    baseline_path = Path(
        cfg.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    )
    cleaned_path = Path(
        cfg.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    )
    output_path = Path(
        cfg.get(
            "SIZE_SENSITIVITY_OUTPUT",
            "data/processed/dataset_size_sensitivity.json",
        )
    )

    results = run_sensitivity_analysis(baseline_path, cleaned_path)
    write_output(results, output_path)

if __name__ == "__main__":
    main()