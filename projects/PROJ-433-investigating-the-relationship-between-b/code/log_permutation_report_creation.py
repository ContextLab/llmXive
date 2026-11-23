"""Log creation of the permutation report.

This script runs the existing permutation report generation routine
(``code/permutation_report.py``) and then records a log entry in
``data/analysis_log.txt`` indicating that the report has been created.

The log format follows the existing convention used throughout the
project, e.g.:

    [2026-10-09 04:01:06] INFO: Permutation report created at data/results/permutation_report.png
"""

import logging
from datetime import datetime
from pathlib import Path

# Import the main function that creates the permutation report.
# The imported module is expected to expose a ``main`` function that
# generates the PNG file at ``data/results/permutation_report.png``.
# It may return the path to the created file; if it does not, we fall
# back to the known location.
from permutation_report import main as generate_permutation_report

def _log_permutation_report_creation(report_path: Path) -> None:
    """Append a log line to ``data/analysis_log.txt``."""
    log_file = Path("data/analysis_log.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Ensure the log directory exists; the file will be created if missing.
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] INFO: Permutation report created at {report_path}\n")

def main() -> None:
    """Run the permutation report generation and log its creation."""
    # Run the existing report generation script.
    # The function may return the path of the generated PNG; if it does
    # not, we use the standard expected location.
    try:
        result = generate_permutation_report()
    except Exception as exc:
        # If the underlying script fails, propagate the error so that the
        # pipeline aborts – we do not silently swallow failures.
        raise RuntimeError("Permutation report generation failed") from exc

    # Determine the report file path.
    if isinstance(result, (str, Path)):
        report_path = Path(result)
    else:
        # Default location used by the original implementation.
        report_path = Path("data/results/permutation_report.png")

    # Verify that the report file exists before logging.
    if not report_path.is_file():
        raise FileNotFoundError(f"Expected permutation report at {report_path} not found")

    # Write the log entry.
    _log_permutation_report_creation(report_path)

if __name__ == "__main__":
    # Configure a basic logger for any unexpected issues.
    logging.basicConfig(level=logging.INFO)
    main()
