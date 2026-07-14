"""
T040 – Create Comparison Report
--------------------------------
This script builds a ``ComparisonReport`` data artifact that aggregates the
baseline analysis results, the cleaned‑data analysis results and the derived
differences between them.  The report is written to
``data/processed/comparison_report.json`` (the exact location can be
overridden via the configuration system).

The implementation is deliberately tolerant:
* ``setup_logging`` from ``utils`` can be called with no arguments or with
  any combination of ``log_level`` keyword arguments.
* ``run_baseline_analysis`` from ``analysis`` is invoked only when the
  required input files are missing – the function’s signature is flexible
  enough to accept the different call‑patterns used throughout the code
  base.
* Missing optional files (e.g. sensitivity analysis) are handled gracefully.

The script can be executed directly:

    python code/t040_create_comparison_report.py

It will log progress, generate the report and exit with status 0 on success.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Local imports – these names are guaranteed to exist in the repository
from utils import setup_logging  # noqa: F401
from config import get_config
from analysis import run_baseline_analysis  # noqa: F401
from models import ComparisonReport  # Pydantic model defined in code/models.py

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, otherwise return ``None``."""
    if path.is_file():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _ensure_baseline_metrics(raw_dir: Path, baseline_path: Path) -> Dict[str, Any]:
    """
    Make sure ``baseline_metrics.json`` exists.
    If it does not, run the baseline analysis to create it.
    """
    baseline = _load_json(baseline_path)
    if baseline is None:
        logging.info("Baseline metrics not found – generating via run_baseline_analysis")
        # ``run_baseline_analysis`` can be called with (raw_dir, output_file)
        # or with keyword arguments; we use the most generic form.
        try:
            # The function may return a dict or ``None``; we ignore the return
            # value and load the file afterwards.
            run_baseline_analysis(raw_dir=raw_dir, output_file=str(baseline_path))
        except TypeError:
            # Fallback to positional arguments – some call‑sites use this style.
            run_baseline_analysis(str(raw_dir), str(baseline_path))
        baseline = _load_json(baseline_path)
        if baseline is None:
            raise FileNotFoundError(f"Failed to generate baseline metrics at {baseline_path}")
    return baseline


def _ensure_cleaned_metrics(processed_dir: Path, cleaned_path: Path) -> Dict[str, Any]:
    """
    Ensure ``cleaned_metrics.json`` exists.
    The cleaned metrics are produced by the re‑analysis of cleaned variants
    (script ``t023_reanalyze_cleaned_variants.py``).  Rather than duplicate
    that logic we invoke the same entry point if the file is missing.
    """
    cleaned = _load_json(cleaned_path)
    if cleaned is None:
        logging.info("Cleaned metrics not found – generating via re‑analysis")
        # Import inside the function to avoid circular imports at module load time.
        from t023_reanalyze_cleaned_variants import main as reanalyse_main  # noqa: E402
        # ``main`` expects no arguments and writes the file based on config.
        reanalyse_main()
        cleaned = _load_json(cleaned_path)
        if cleaned is None:
            raise FileNotFoundError(f"Failed to generate cleaned metrics at {cleaned_path}")
    return cleaned


def _compute_differences(
    baseline: Dict[str, Any],
    cleaned: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute absolute and relative differences for each metric present in the
    baseline and cleaned dictionaries.  The expected structure of each entry
    is::

        {
            "p_value": float,
            "ci_width": float,
            "effect_size": float
        }

    The function returns a nested mapping::

        {
            "<dataset_id>": {
                "p_value": {"abs": ..., "rel": ...},
                "ci_width": {"abs": ..., "rel": ...},
                "effect_size": {"abs": ..., "rel": ...}
            },
            ...
        }
    """
    diffs: Dict[str, Any] = {}
    for dataset_id, base_metrics in baseline.items():
        clean_metrics = cleaned.get(dataset_id)
        if not clean_metrics:
            # If a cleaned version is missing we simply skip the dataset.
            logging.warning(
                f"Cleaned metrics missing for dataset {dataset_id!r}; skipping diff."
            )
            continue

        diffs[dataset_id] = {}
        for metric_name in ("p_value", "ci_width", "effect_size"):
            base_val = base_metrics.get(metric_name)
            clean_val = clean_metrics.get(metric_name)
            if base_val is None or clean_val is None:
                logging.warning(
                    f"Metric {metric_name!r} missing for dataset {dataset_id!r}; "
                    "recording diff as None."
                )
                diffs[dataset_id][metric_name] = {"abs": None, "rel": None}
                continue

            abs_diff = round(abs(clean_val - base_val), 6)
            # Relative difference is defined as (clean - base) / |base|
            # Guard against division by zero.
            if base_val == 0:
                rel_diff = None
            else:
                rel_diff = round((clean_val - base_val) / abs(base_val), 6)

            diffs[dataset_id][metric_name] = {"abs": abs_diff, "rel": rel_diff}
    return diffs


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Orchestrate the creation of the ``ComparisonReport``.
    The steps are:

    1. Initialise logging.
    2. Resolve configuration – paths to raw data, processed data and optional
       sensitivity analysis.
    3. Ensure that baseline and cleaned metric files exist (generating them if
       necessary).
    4. Load the two metric collections.
    5. Compute absolute and relative differences.
    6. Load any sensitivity‑analysis artifact (optional).
    7. Populate the ``ComparisonReport`` Pydantic model.
    8. Serialise the model to JSON on disk.
    """
    # 1. Logging – tolerant to any signature.
    try:
        logger = setup_logging(log_level="INFO")
    except Exception:  # pragma: no cover – defensive fallback
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    logger.info("Starting ComparisonReport generation (T040)")

    # 2. Configuration
    cfg = get_config()
    raw_dir = Path(cfg.get("RAW_DATA_PATH", "data/raw"))
    processed_dir = Path(cfg.get("PROCESSED_DATA_PATH", "data/processed"))

    baseline_path = Path(cfg.get("BASELINE_METRICS_PATH", processed_dir / "baseline_metrics.json"))
    cleaned_path = Path(cfg.get("CLEANED_METRICS_PATH", processed_dir / "cleaned_metrics.json"))
    sensitivity_path = Path(cfg.get("SENSITIVITY_ANALYSIS_PATH", processed_dir / "sensitivity_analysis.json"))

    # 3. Ensure required metric files exist
    baseline_metrics = _ensure_baseline_metrics(raw_dir, baseline_path)
    cleaned_metrics = _ensure_cleaned_metrics(processed_dir, cleaned_path)

    # 4. Compute differences
    absolute_diff = _compute_differences(baseline_metrics, cleaned_metrics)

    # 5. Relative differences are already part of the structure returned by
    #    ``_compute_differences`` – we expose them under a dedicated key for
    #    downstream consumers.
    relative_diff = {
        ds_id: {
            metric: vals["rel"] for metric, vals in metric_dict.items()
        }
        for ds_id, metric_dict in absolute_diff.items()
    }

    # 6. Optional sensitivity analysis payload
    sensitivity_analysis = _load_json(sensitivity_path) or {}

    # 7. Build the Pydantic model
    report = ComparisonReport(
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=absolute_diff,
        relative_diff=relative_diff,
        sensitivity_analysis=sensitivity_analysis,
    )

    # 8. Serialise to JSON
    output_path = processed_dir / "comparison_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    logger.info(f"Comparison report written to {output_path}")

    # Explicit successful exit
    return None


if __name__ == "__main__":
    main()