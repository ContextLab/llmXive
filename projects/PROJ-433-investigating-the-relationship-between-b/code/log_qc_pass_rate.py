"""Compute QC pass rate after preprocessing and log the result.

This script reads the preprocessing log file ``data/preprocess_log.txt`` for
entries that indicate whether a subject passed QC.  It expects lines that
contain the token ``QC PASS`` for successful subjects and ``QC FAIL`` for
subjects that were excluded.  The total number of subjects is inferred from
the number of lines that contain either token.

After computing the percentage of subjects that passed QC, the script logs
a message of the form::

    SC-001: X% subjects passed fMRIPrep QC

to ``data/analysis_log.txt`` using the shared logger defined in
``code.utils.setup_logger``.
"""

import logging
from pathlib import Path

from utils import setup_logger

# Paths to the relevant log files
PREPROCESS_LOG = Path("data/preprocess_log.txt")
ANALYSIS_LOG = Path("data/analysis_log.txt")

def _parse_qc_log(log_path: Path) -> tuple[int, int]:
    """Parse the preprocessing log and count passed / total subjects.

    Parameters
    ----------
    log_path: Path
        Path to ``data/preprocess_log.txt``.

    Returns
    -------
    passed: int
        Number of subjects that passed QC.
    total: int
        Total number of subjects for which a QC entry exists.
    """
    passed = 0
    total = 0
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "QC PASS" in line:
                passed += 1
                total += 1
            elif "QC FAIL" in line:
                total += 1
    return passed, total

def _log_qc_pass_rate(passed: int, total: int, logger: logging.Logger) -> None:
    """Log the QC pass rate using the shared logger.

    The message follows the specification required for SC‑001.
    """
    percent = (passed / total) * 100 if total > 0 else 0.0
    # One decimal place is sufficient for reporting
    logger.info(f"SC-001: {percent:.1f}% subjects passed fMRIPrep QC")

def main() -> None:
    """Entry point for the script."""
    # Ensure the analysis log file exists so the logger can write to it
    ANALYSIS_LOG.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_LOG.touch(exist_ok=True)

    logger = setup_logger(name=__name__, log_file=str(ANALYSIS_LOG))

    if not PREPROCESS_LOG.is_file():
        logger.error(f"Preprocess log file not found at {PREPROCESS_LOG}")
        raise FileNotFoundError(f"{PREPROCESS_LOG} does not exist")

    passed, total = _parse_qc_log(PREPROCESS_LOG)
    _log_qc_pass_rate(passed, total, logger)

if __name__ == "__main__":
    main()
