"""
audit_t0_files.py

This module audits the ``code/`` directory for any legacy scripts whose
filenames match the pattern ``t0*.py``.  Those scripts were used in an early
prototype of the pipeline and should be migrated or removed.  The audit
produces a JSON report listing the relative paths of all matching files.
The report is written to ``data/processed/t0_files_audit.json`` – a location
that is not ignored by the repository and is therefore persisted for later
verification steps.

The module provides three public helpers:

* ``find_t0_files(base_dir: Path) -> List[str]``
  Walks ``base_dir`` (default: the ``code/`` package directory) and returns
  a list of POSIX‑style relative file paths that match the ``t0*.py`` glob.

* ``write_audit_report(file_list: List[str], output_path: Path) -> None``
  Serialises ``file_list`` as JSON to ``output_path``.  The function creates
  the parent directory if it does not already exist.

* ``main()`` – a thin CLI entry point that logs progress, runs the audit,
  writes the report and prints a short summary to stdout.

The script can be executed directly::

    python code/audit_t0_files.py

or invoked from the quick‑start run‑book if desired.
"""

import json
import logging
from pathlib import Path
from typing import List

# Import the project's flexible logging helper.  The helper is tolerant of
# both positional and keyword arguments (see ``code/utils.py``).
from utils import setup_logging

logger = logging.getLogger(__name__)

def find_t0_files(base_dir: Path = Path(__file__).parent) -> List[str]:
    """
    Recursively search ``base_dir`` for files whose name matches the
    pattern ``t0*.py`` and return their paths relative to ``base_dir``.

    Parameters
    ----------
    base_dir: Path
        Directory to search.  Defaults to the ``code/`` package directory.

    Returns
    -------
    List[str]
        List of POSIX‑style relative file paths (e.g. ``'t012_run_baseline_analysis.py'``).
    """
    logger.debug("Scanning for t0*.py files in %s", base_dir)
    matches: List[str] = []
    for path in base_dir.rglob("t0*.py"):
        # Ensure we only capture files directly under ``code/`` or its
        # sub‑directories (ignore hidden directories, etc.).
        if path.is_file():
            rel_path = path.relative_to(base_dir).as_posix()
            matches.append(rel_path)
    logger.info("Found %d t0*.py file(s).", len(matches))
    return matches

def write_audit_report(file_list: List[str],
                      output_path: Path = Path("data/processed/t0_files_audit.json")) -> None:
    """
    Write the audit ``file_list`` to ``output_path`` as pretty‑printed JSON.
    The function creates the parent directory if necessary.

    Parameters
    ----------
    file_list: List[str]
        List of relative file paths to record.
    output_path: Path
        Destination for the JSON report.  Defaults to
        ``data/processed/t0_files_audit.json``.
    """
    logger.debug("Writing audit report to %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"t0_files": file_list}, f, indent=2, sort_keys=True)
    logger.info("Audit report written (%d entries).", len(file_list))

def main() -> None:
    """
    CLI entry point: configure logging, run the audit and persist the report.
    """
    # The project's ``setup_logging`` helper accepts a variety of call signatures.
    # We use the keyword form here for clarity.
    setup_logging(log_level="INFO")
    logger.info("Starting t0*.py audit.")
    t0_files = find_t0_files()
    write_audit_report(t0_files)
    # Print a concise human‑readable summary for interactive runs.
    print(f"Audit complete – {len(t0_files)} t0*.py file(s) found.")
    if t0_files:
        for f in t0_files:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
