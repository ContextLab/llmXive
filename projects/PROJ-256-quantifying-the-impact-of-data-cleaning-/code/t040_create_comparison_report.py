"""
T040 – Create Comparison Report
--------------------------------
This script builds a `ComparisonReport` data structure that captures the
differences between the baseline analysis results and the cleaned‑data
analysis results.  It reads the two metric JSON files produced by earlier
pipeline stages, computes absolute and relative differences for every
numeric metric, attaches an (optional) sensitivity‑analysis payload and
writes the final report to ``data/processed/comparison_report.json``.

The script is deliberately defensive:
  * It logs useful progress information.
  * It aborts with a non‑zero exit code if required input files are
    missing.
  * It tolerates non‑numeric entries by skipping them rather than raising
    an exception.
  * It creates missing parent directories for the output file.

The implementation follows the public API surface of the project:
  * ``setup_logging`` and ``pin_random_seed`` are imported from ``utils``.
  * ``ComparisonReport`` is imported from ``models``.
  * No new third‑party dependencies are introduced.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Project imports – these exist according to the API surface description
from utils import setup_logging, pin_random_seed
from models import ComparisonReport


def _load_json(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def _numeric_diff(baseline: float, cleaned: float) -> Dict[str, float]:
    """Return absolute and relative differences between two numbers."""
    abs_diff = abs(cleaned - baseline)
    # Guard against division by zero for relative diff
    rel_diff = abs_diff / (abs(baseline) if baseline != 0 else 1.0)
    return {
        "absolute": round(abs_diff, 3),
        "relative": round(rel_diff, 3),
    }


def _compute_differences(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
) -> Dict[str, Dict[str, float]]:
    """
    Walk through the metric dictionaries and compute numeric differences.

    The function only processes leaf values that are ``int`` or ``float``.
    Nested dictionaries are traversed recursively; non‑numeric leaves are
    ignored.
    """
    diffs: Dict[str, Dict[str, float]] = {}

    def _recurse(
        b_node: Any,
        c_node: Any,
        prefix: str = "",
    ) -> None:
        if isinstance(b_node, dict) and isinstance(c_node, dict):
            # Recurse into shared keys
            for key in b_node.keys() & c_node.keys():
                new_prefix = f"{prefix}.{key}" if prefix else key
                _recurse(b_node[key], c_node[key], new_prefix)
            return

        # Leaf node – compute diff if both are numeric
        if isinstance(b_node, (int, float)) and isinstance(c_node, (int, float)):
            diffs[prefix] = _numeric_diff(float(b_node), float(c_node))

    _recurse(baseline_metrics, cleaned_metrics)
    return diffs


def main() -> int:
    """
    Entry point for the comparison‑report generation script.

    Returns
    -------
    int
        Exit status – ``0`` on success, non‑zero on failure.
    """
    logger: logging.Logger = setup_logging(log_level="INFO")
    pin_random_seed(42)  # deterministic behaviour for any stochastic steps

    # Expected input artefacts
    baseline_path = Path("data/processed/baseline_metrics.json")
    cleaned_path = Path("data/processed/cleaned_metrics.json")

    if not baseline_path.is_file():
        logger.error("Baseline metrics file not found: %s", baseline_path)
        return 1
    if not cleaned_path.is_file():
        logger.error("Cleaned metrics file not found: %s", cleaned_path)
        return 1

    logger.info("Loading baseline metrics from %s", baseline_path)
    baseline_metrics = _load_json(baseline_path)
    logger.info("Loading cleaned metrics from %s", cleaned_path)
    cleaned_metrics = _load_json(cleaned_path)

    logger.info("Computing absolute and relative differences")
    diffs = _compute_differences(baseline_metrics, cleaned_metrics)

    # Sensitivity analysis payload – optional.  If a dedicated artefact exists
    # we include it, otherwise we store an empty dict.
    sensitivity_path = Path("data/processed/sensitivity_analysis.json")
    if sensitivity_path.is_file():
        logger.info("Loading sensitivity analysis from %s", sensitivity_path)
        sensitivity_analysis = _load_json(sensitivity_path)
    else:
        logger.debug("No sensitivity analysis artefact found; using empty dict")
        sensitivity_analysis = {}

    # Assemble the ComparisonReport model
    report = ComparisonReport(
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=diffs,
        relative_diff={k: v["relative"] for k, v in diffs.items()},
        sensitivity_analysis=sensitivity_analysis,
    )

    output_path = Path("data/processed/comparison_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report.dict(), f, indent=2)

    logger.info("Comparison report written to %s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())