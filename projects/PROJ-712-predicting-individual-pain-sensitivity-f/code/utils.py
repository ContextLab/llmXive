"""
Utility module for the PROJ-712 pain sensitivity pipeline.

Provides functions for:
- Global random seed pinning
- Lightweight logging with file handler (project‑owned only)
- SHA‑256 checksum computation
- Artifact hash recording
- Timing helpers
- Simple citation validation (required for pre‑run validation)

The module can also be invoked as a script:
    python -m code.utils --validate-citations
"""

import hashlib
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

import yaml
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Global constants
# ----------------------------------------------------------------------
# All project‑owned files are under the `artifacts/` or `data/` directories.
# We avoid the platform‑owned `state/` directory to prevent shadowing.
LOG_FILE = paths.artifacts("log.txt")
HASH_FILE = paths.artifacts("artifact_hashes.yaml")
DEFAULT_LOG_LEVEL = logging.INFO
MAX_EXECUTION_SECONDS = 6 * 60 * 60  # 6 hours

# ----------------------------------------------------------------------
# Seed handling
# ----------------------------------------------------------------------
def set_global_seed(seed: int = 42) -> None:
    """
    Set the global random seed for reproducibility.

    Affects Python's ``random`` module, NumPy (if imported), and the
    ``PYTHONHASHSEED`` environment variable.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass  # NumPy not available – nothing to seed

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def _configure_logger(logger: logging.Logger, level: int) -> None:
    """Attach console and file handlers to *logger* if they are missing."""
    if logger.handlers:
        # Assume logger is already configured (avoid duplicate handlers)
        return

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Ensure the log directory exists (handled by paths.artifacts, but for safety)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # File handler (project‑owned)
    file_handler = logging.FileHandler(LOG_FILE, mode="a")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.setLevel(level)

def setup_logging(name_or_level: Union[int, str] = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Configure and return a logger.

    * If an *int* is supplied, it is interpreted as the logging level and a
      default logger named ``"pipeline"`` is created.
    * If a *str* is supplied, it is interpreted as the logger name and the
      default level ``DEFAULT_LOG_LEVEL`` is used.

    All log output is written to ``artifacts/log.txt`` and to the
    console.
    """
    if isinstance(name_or_level, int):
        level = name_or_level
        logger_name = "pipeline"
    else:
        level = DEFAULT_LOG_LEVEL
        logger_name = name_or_level

    logger = logging.getLogger(logger_name)
    _configure_logger(logger, level)
    return logger

# ----------------------------------------------------------------------
# Checksum helpers
# ----------------------------------------------------------------------
def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Reads the file in 4 KB chunks to handle large files efficiently.
    """
    path = Path(file_path)
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

# Alias kept for backward compatibility
compute_file_hash = compute_checksum

# ----------------------------------------------------------------------
# Artifact hash recording
# ----------------------------------------------------------------------
def record_artifact_hash(
    file_path: Union[str, Path],
    artifact_name: Optional[str] = None,
    state_file: Optional[Union[str, Path]] = None,
) -> None:
    """
    Record the SHA‑256 hash of an artifact in the project result YAML file.

    Parameters
    ----------
    file_path
        Path to the artifact file.
    artifact_name
        Human‑readable name for the artifact; defaults to the filename.
    state_file
        Path to the state YAML file; defaults to
        ``artifacts/artifact_hashes.yaml``.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Artifact not found: {path}")

    hash_val = compute_checksum(path)
    name = artifact_name or path.name

    # Determine output file location (project‑owned)
    state_path = Path(state_file) if state_file is not None else HASH_FILE

    # Load existing state or start a new dict
    if state_path.is_file():
        with state_path.open("r") as sf:
            state_data = yaml.safe_load(sf) or {}
    else:
        state_data = {}

    # Ensure the top‑level key exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"][name] = {
        "sha256": hash_val,
        "timestamp": get_current_timestamp(),
    }

    # Write back (parent directories are created by llmxive_toolkit.paths)
    with state_path.open("w") as sf:
        yaml.safe_dump(state_data, sf)

# ----------------------------------------------------------------------
# Timing helpers
# ----------------------------------------------------------------------
def get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO‑8601 format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def measure_duration(arg: Union[Callable, float]) -> Union[Callable, float]:
    """
    Dual‑purpose helper:

    * If *arg* is a callable, returns a wrapped function that logs its
      execution time (acts as a decorator).
    * If *arg* is a start‑time float, returns the elapsed seconds.
    """
    if callable(arg):
        func = arg

        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger = logging.getLogger(func.__module__ or "__main__")
            logger.info(f"Duration of {func.__name__}: {elapsed:.2f} seconds")
            return result

        return wrapper
    else:
        # Assume *arg* is a start timestamp
        start_time = float(arg)
        return time.time() - start_time

def assert_duration_limit(duration_seconds: float, limit_seconds: Optional[float] = None) -> None:
    """
    Verify that *duration_seconds* does not exceed *limit_seconds*.

    The default limit is ``MAX_EXECUTION_SECONDS`` (6 h). Raises
    ``AssertionError`` on violation with a message that includes the
    Constitution principle identifier.
    """
    limit = limit_seconds if limit_seconds is not None else MAX_EXECUTION_SECONDS
    if duration_seconds > limit:
        raise AssertionError(
            f"SC-005 VIOLATION: Execution time {duration_seconds:.2f}s exceeds limit of {limit:.2f}s"
        )

# Simple global timer used by ``start_timer`` / ``stop_timer``
_start_time: Optional[float] = None

def start_timer() -> float:
    """Start a global timer for the pipeline."""
    global _start_time
    _start_time = time.time()
    return _start_time

def stop_timer() -> float:
    """
    Stop the global timer and enforce the SC‑005 execution limit.

    Returns the total elapsed time in seconds.
    """
    if _start_time is None:
        raise RuntimeError("Timer was not started. Call start_timer() first.")
    elapsed = time.time() - _start_time
    assert_duration_limit(elapsed)
    return elapsed

def validate_pipeline_duration(start_time: float) -> float:
    """
    Convenience wrapper used by tests: compute elapsed since
    ``start_time`` and enforce the duration limit.

    Returns the elapsed seconds.
    """
    elapsed = time.time() - start_time
    assert_duration_limit(elapsed)
    return elapsed

# ----------------------------------------------------------------------
# Citation validation (used by the pre‑run validation script)
# ----------------------------------------------------------------------
def _load_required_citations() -> List[str]:
    """
    Return a list of required citation identifiers.
    """
    return ["doi:10.1234/example1", "doi:10.5678/example2"]

def _load_existing_citations() -> List[str]:
    """
    Load the project's citation file and return the identifiers found.
    The convention is a plain text file ``CITATIONS.bib`` in the
    repository root.
    """
    citations_path = Path("CITATIONS.bib")
    if not citations_path.is_file():
        return []
    with citations_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def validate_citations() -> bool:
    """
    Validate that all required citations are present.

    Returns ``True`` if validation succeeds; otherwise prints a
    message and returns ``False``.
    """
    required = set(_load_required_citations())
    present = set(_load_existing_citations())

    missing = required - present
    if missing:
        logger = setup_logging(__name__)
        logger.error("Missing required citations:")
        for cid in sorted(missing):
            logger.error(f"  - {cid}")
        return False
    return True

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Utility commands for the PROJ‑712 pipeline."
    )
    parser.add_argument(
        "--validate-citations",
        action="store_true",
        help="Check that required citations are present in CITATIONS.bib",
    )
    parser.add_argument(
        "--verify-checksums",
        action="store_true",
        help="Compute and record checksums for files in data/raw/",
    )

    args = parser.parse_args()

    # Initialise a basic logger for CLI feedback
    _ = setup_logging()

    if args.validate_citations:
        success = validate_citations()
        if not success:
            exit(1)
        else:
            print("All required citations are present.")
            exit(0)

    if args.verify_checksums:
        # Lazy import to avoid circular dependencies
        try:
            from checksums import scan_raw_data_directory, record_checksums_to_state
        except ImportError:
            print("Error: code.checksums module not found.")
            exit(1)

        raw_dir = Path("data") / "raw"
        state_file = HASH_FILE

        if not raw_dir.is_dir():
            print(f"Raw data directory not found: {raw_dir}")
            exit(1)

        checksums = {}
        for file_path in scan_raw_data_directory(raw_dir):
            checksums[str(file_path)] = compute_checksum(file_path)

        record_checksums_to_state(checksums, state_file)
        print(f"Recorded checksums for {len(checksums)} files.")
        exit(0)

    parser.print_help()
    exit(0)

if __name__ == "__main__":
    _cli()