"""
t027_run_comparison.py
======================

Small wrapper script that invokes the comparison logic implemented in
``code/reporting.py``.  The script is part of the quick‑start pipeline and
therefore must be executable as ``python code/t027_run_comparison.py``.
"""

import logging
import sys
from pathlib import Path

# Import the tolerant logging helper from utils (it already accepts various signatures)
from utils import setup_logging

# Import the functions we need from reporting
from reporting import load_baseline_metrics, load_cleaned_metrics, generate_comparison_report, save_json_file

def main() -> int:
    """
    Execute the comparison step.

    Returns
    -------
    int
        Exit status (0 = success, non‑zero = error).
    """
    # Initialise logging – the helper is deliberately permissive.
    logger = setup_logging("INFO")

    # Resolve the default output location for the comparison report.
    output_path = Path("data/processed/comparison_report.json")

    # Load the two metric artefacts.
    baseline = load_baseline_metrics()
    cleaned = load_cleaned_metrics()

    if not baseline:
        logger.error("Baseline metrics not found – cannot generate comparison report.")
        return 1
    if not cleaned:
        logger.error("Cleaned metrics not found – cannot generate comparison report.")
        return 1

    # Build the report.
    report = generate_comparison_report(baseline, cleaned)

    # Persist the report.
    try:
        save_json_file(report, str(output_path))
    except Exception as exc:
        logger.exception("Failed to write comparison report: %s", exc)
        return 1

    logger.info("Comparison report written to %s", output_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())