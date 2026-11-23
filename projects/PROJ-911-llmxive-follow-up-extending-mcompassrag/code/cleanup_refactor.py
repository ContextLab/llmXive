"""
cleanup_refactor.py
--------------------
Utility module providing standardized cleanup, validation, and
aggregation helpers for the GraphCompass research pipeline.

This module is used by the T034 task to refactor and clean up the
existing code base.  All functions are implemented with strict
typing, deterministic behaviour, and robust error handling so that
they can be imported by any script in the `code/` package without
side‑effects.

The public API matches the signatures listed in the project’s
API surface:

- setup_cleanup_logging()
- ensure_directory_exists(path, logger=None)
- validate_file_integrity(file_path, logger=None)
- safe_json_load(file_path, logger=None)
- safe_csv_load(file_path, logger=None)
- aggregate_pipeline_metrics(metrics_path,
                              correlation_path,
                              latency_path,
                              logger=None)
- validate_project_structure(logger=None)
- run_cleanup_validation()
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_cleanup_logging() -> logging.Logger:
    """
    Configure a standardized logger for the cleanup process.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger("cleanup_refactor")
    logger.setLevel(logging.INFO)

    # If handlers are already attached (e.g., when this module is
    # imported multiple times), avoid adding duplicates.
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# ----------------------------------------------------------------------
# Directory utilities
# ----------------------------------------------------------------------
def ensure_directory_exists(
    path: Path, logger: Optional[logging.Logger] = None
) -> None:
    """
    Ensure a directory exists, creating it (including parents) if necessary.

    Parameters
    ----------
    path : Path
        Directory path to ensure.
    logger : Optional[logging.Logger]
        Logger for informational messages. If None, a default logger is used.
    """
    if logger is None:
        logger = setup_cleanup_logging()
    if not path.exists():
        logger.info(f"Creating missing directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
    else:
        logger.debug(f"Directory already exists: {path}")

# ----------------------------------------------------------------------
# File integrity utilities
# ----------------------------------------------------------------------
def validate_file_integrity(
    file_path: Path, logger: Optional[logging.Logger] = None
) -> bool:
    """
    Validate that a file exists and is not empty.

    Parameters
    ----------
    file_path : Path
        Path to the file to validate.
    logger : Optional[logging.Logger]
        Logger for messages.

    Returns
    -------
    bool
        True if the file exists and has a size > 0, False otherwise.
    """
    if logger is None:
        logger = setup_cleanup_logging()
    if not file_path.is_file():
        logger.error(f"File does not exist: {file_path}")
        return False
    if file_path.stat().st_size == 0:
        logger.error(f"File is empty: {file_path}")
        return False
    logger.debug(f"File validated successfully: {file_path}")
    return True

# ----------------------------------------------------------------------
# Safe loading utilities
# ----------------------------------------------------------------------
def safe_json_load(
    file_path: Path, logger: Optional[logging.Logger] = None
) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file, returning None on error.

    Parameters
    ----------
    file_path : Path
        Path to the JSON file.
    logger : Optional[logging.Logger]

    Returns
    -------
    Optional[Dict[str, Any]]
        Parsed JSON object or None if loading fails.
    """
    if logger is None:
        logger = setup_cleanup_logging()
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return None

def safe_csv_load(
    file_path: Path, logger: Optional[logging.Logger] = None
) -> List[Dict[str, Any]]:
    """
    Safely load a CSV file into a list of dictionaries.

    Parameters
    ----------
    file_path : Path
        Path to the CSV file.
    logger : Optional[logging.Logger]

    Returns
    -------
    List[Dict[str, Any]]
        List of rows as dictionaries; empty list on failure.
    """
    if logger is None:
        logger = setup_cleanup_logging()
    rows: List[Dict[str, Any]] = []
    try:
        with file_path.open("r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)
        logger.debug(f"Loaded {len(rows)} rows from CSV {file_path}")
    except Exception as e:
        logger.error(f"Failed to load CSV from {file_path}: {e}")
    return rows

# ----------------------------------------------------------------------
# Metric aggregation
# ----------------------------------------------------------------------
def aggregate_pipeline_metrics(
    metrics_path: Path,
    correlation_path: Path,
    latency_path: Path,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    Aggregate metrics from three JSON artefacts into a single dictionary.

    Parameters
    ----------
    metrics_path : Path
        Path to the generic metrics JSON (e.g., recall metrics).
    correlation_path : Path
        Path to the Spearman correlation JSON.
    latency_path : Path
        Path to the latency metrics JSON.
    logger : Optional[logging.Logger]

    Returns
    -------
    Dict[str, Any]
        Combined dictionary with keys 'metrics', 'correlation', 'latency'.
    """
    if logger is None:
        logger = setup_cleanup_logging()

    def _load(path: Path, name: str) -> Optional[Dict[str, Any]]:
        data = safe_json_load(path, logger)
        if data is None:
            logger.error(f"Unable to load {name} from {path}")
        else:
            logger.info(f"Loaded {name} from {path}")
        return data

    metrics = _load(metrics_path, "metrics")
    correlation = _load(correlation_path, "correlation")
    latency = _load(latency_path, "latency")

    aggregated: Dict[str, Any] = {
        "metrics": metrics or {},
        "correlation": correlation or {},
        "latency": latency or {},
    }
    logger.info("Aggregated pipeline metrics successfully.")
    return aggregated

# ----------------------------------------------------------------------
# Project structure validation
# ----------------------------------------------------------------------
def validate_project_structure(
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Validate that the repository directory structure matches the
    specification.

    Checks for the presence of required top‑level directories and
    essential sub‑directories.

    Returns
    -------
    bool
        True if the structure is valid, False otherwise.
    """
    if logger is None:
        logger = setup_cleanup_logging()

    required_dirs = [
        Path("code"),
        Path("tests"),
        Path("docs"),
        Path("data/raw"),
        Path("data/processed"),
        Path("data/results"),
    ]

    all_ok = True
    for d in required_dirs:
        if not d.is_dir():
            logger.error(f"Required directory missing: {d}")
            all_ok = False
        else:
            logger.debug(f"Directory exists: {d}")

    if all_ok:
        logger.info("Project structure validation passed.")
    else:
        logger.warning("Project structure validation failed.")
    return all_ok

# ----------------------------------------------------------------------
# End‑to‑end cleanup validation
# ----------------------------------------------------------------------
def run_cleanup_validation() -> int:
    """
    Main entry point for the cleanup validation script.

    Performs the following steps:
    1. Configure logging.
    2. Validate the overall project directory layout.
    3. Ensure that key artefact directories exist.
    4. Verify integrity of critical output files.
    5. Aggregate metrics and write a consolidated JSON file.
    6. Return an exit code (0 = success, 1 = failure).

    Returns
    -------
    int
        Exit status code.
    """
    logger = setup_cleanup_logging()
    logger.info("Starting cleanup validation...")

    # 1. Validate directory layout
    if not validate_project_structure(logger):
        logger.error("Project structure is invalid. Aborting.")
        return 1

    # 2. Ensure output directories exist (they may be missing if a prior
    #    pipeline step failed).
    for out_dir in [
        Path("data/processed"),
        Path("data/results"),
    ]:
        ensure_directory_exists(out_dir, logger)

    # 3. Critical artefacts to check (these are produced by earlier tasks)
    critical_files = [
        Path("data/processed/graphs.json"),
        Path("data/processed/features.csv"),
        Path("data/results/recall_metrics.json"),
        Path("data/results/correlation.csv"),
        Path("data/results/metrics.json"),
    ]

    all_files_ok = True
    for f in critical_files:
        if not validate_file_integrity(f, logger):
            all_files_ok = False

    if not all_files_ok:
        logger.error(
            "One or more critical output files are missing or empty."
        )
        return 1

    # 4. Aggregate metrics
    aggregated = aggregate_pipeline_metrics(
        metrics_path=Path("data/results/recall_metrics.json"),
        correlation_path=Path("data/results/correlation.csv"),
        latency_path=Path("data/results/metrics.json"),
        logger=logger,
    )

    # 5. Write aggregated results
    aggregated_path = Path("data/results/aggregated_metrics.json")
    try:
        with aggregated_path.open("w", encoding="utf-8") as out_f:
            json.dump(aggregated, out_f, indent=2, ensure_ascii=False)
        logger.info(f"Aggregated metrics written to {aggregated_path}")
    except Exception as e:
        logger.error(f"Failed to write aggregated metrics: {e}")
        return 1

    logger.info("Cleanup validation completed successfully.")
    return 0

# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(run_cleanup_validation())
