"""
T040 – Create Comparison Report
--------------------------------
This script builds a ``ComparisonReport`` object that aggregates the baseline
analysis results, the cleaned‑data analysis results and the derived metric
differences.  The report is written to ``data/processed/comparison_report.json``.

The implementation follows the public API of the project:

* ``load_baseline_metrics`` and ``load_cleaned_metrics`` – helpers in
  ``code/reporting.py`` that read the JSON artifacts produced by the baseline
  and cleaned‑variant analyses.
* ``calculate_absolute_diff`` and ``calculate_relative_diff`` – also from
  ``code/reporting.py``; they return dictionaries that map metric names to the
  absolute / relative change between the two analyses.
* ``ComparisonReport`` – a Pydantic model defined in ``code/models.py`` with the
  fields ``baseline_metrics``, ``cleaned_metrics``, ``absolute_diff``,
  ``relative_diff`` and ``sensitivity_analysis``.
* ``setup_logging`` – a tolerant helper from ``code/utils.py`` that can be called
  with a variety of positional / keyword signatures.

The script is deliberately defensive:

* It verifies that the required input files exist and are non‑empty.
* It logs useful information (paths, number of metrics, any missing data).
* It writes the output JSON atomically (writes to a temporary file then renames).

The script can be invoked directly:

``python code/t040_create_comparison_report.py``

or indirectly via the quick‑start pipeline.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from utils import setup_logging
from reporting import (
    load_baseline_metrics,
    load_cleaned_metrics,
    calculate_absolute_diff,
    calculate_relative_diff,
    save_json_file,
)
from models import ComparisonReport


DEFAULT_BASELINE_PATH = Path("data/processed/baseline_metrics.json")
DEFAULT_CLEANED_PATH = Path("data/processed/cleaned_metrics.json")
DEFAULT_OUTPUT_PATH = Path("data/processed/comparison_report.json")


def _ensure_file_nonempty(path: Path) -> Dict[str, Any]:
    """
    Load a JSON file and ensure it contains a non‑empty dictionary.

    Parameters
    ----------
    path: Path
        Path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON content.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file is empty or does not contain a mapping.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        raise ValueError(f"File {path} is empty or does not contain a JSON object.")
    return data


def generate_comparison_report(
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    cleaned_path: Path = DEFAULT_CLEANED_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> ComparisonReport:
    """
    Construct a ``ComparisonReport`` instance from baseline and cleaned metrics,
    compute absolute and relative differences, and persist the report to disk.

    Parameters
    ----------
    baseline_path: Path
        Path to ``baseline_metrics.json``.
    cleaned_path: Path
        Path to ``cleaned_metrics.json``.
    output_path: Path
        Destination for the generated report.

    Returns
    -------
    ComparisonReport
        The populated Pydantic model.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Loading baseline metrics from %s", baseline_path)
    baseline_metrics = _ensure_file_nonempty(baseline_path)

    logger.debug("Loading cleaned metrics from %s", cleaned_path)
    cleaned_metrics = _ensure_file_nonempty(cleaned_path)

    logger.debug("Calculating absolute differences")
    absolute_diff = calculate_absolute_diff(baseline_metrics, cleaned_metrics)

    logger.debug("Calculating relative differences")
    relative_diff = calculate_relative_diff(baseline_metrics, cleaned_metrics)

    # ``sensitivity_analysis`` is optional – other scripts may populate it.
    # If the reporting module provides a helper we would call it here; otherwise
    # we store an empty dict as a placeholder.
    sensitivity_analysis: Dict[str, Any] = {}

    logger.debug("Instantiating ComparisonReport model")
    report = ComparisonReport(
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=absolute_diff,
        relative_diff=relative_diff,
        sensitivity_analysis=sensitivity_analysis,
    )

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically – first to a temporary file then rename.
    temp_path = output_path.with_suffix(".tmp")
    logger.debug("Writing comparison report to temporary file %s", temp_path)
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2, sort_keys=True)
    temp_path.replace(output_path)
    logger.info("Comparison report written to %s", output_path)

    return report


def main() -> None:
    """
    Entry‑point for the script. Sets up logging and triggers the report
    generation.
    """
    # ``setup_logging`` is deliberately permissive – it accepts a variety of
    # calling conventions used throughout the code base.
    logger = setup_logging(log_level="INFO")
    logger.info("Starting comparison‑report generation (T040)")
    try:
        generate_comparison_report()
        logger.info("T040 completed successfully")
    except Exception as exc:  # pragma: no cover – top‑level guard
        logger.exception("Failed to generate comparison report: %s", exc)
        raise


if __name__ == "__main__":
    main()
