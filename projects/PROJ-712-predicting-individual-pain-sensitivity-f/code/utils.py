"""
Utility module for the PROJ-712 pain sensitivity pipeline.

Provides functions for:
- Global random seed pinning
- Lightweight logging with file handler
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

# ----------------------------------------------------------------------
# Global constants
# ----------------------------------------------------------------------
STATE_DIR = Path("state")
LOG_FILE = STATE_DIR / "log.txt"
DEFAULT_LOG_LEVEL = logging.INFO
MAX_EXECUTION_SECONDS = 6 * 60 * 60  # 6 hours

# Ensure the state directory exists for logging
STATE_DIR.mkdir(parents=True, exist_ok=True)


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
def _ensure_log_file_handler(logger: logging.Logger) -> None:
    """
    Attach a ``FileHandler`` that writes to ``state/log.txt``.

    The handler is added only once per logger instance.
    """
    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return

    file_handler = logging.FileHandler(LOG_FILE, mode="a")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def setup_logging(name_or_level: Union[int, str] = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Configure logging.

    * If ``name_or_level`` is an ``int`` it is interpreted as the log level.
    * If it is a ``str`` it is interpreted as the logger name; the level
      defaults to ``INFO``.

    Returns a logger instance configured with a console handler and a
    file handler that writes to ``state/log.txt``.
    """
    if isinstance(name_or_level, int):
        level = name_or_level
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name_or_level)
        level = DEFAULT_LOG_LEVEL

    # Configure the root logger only once
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    logger.setLevel(level)
    _ensure_log_file_handler(logger)
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
    Record the SHA‑256 hash of an artifact in the project state YAML file.

    Parameters
    ----------
    file_path
        Path to the artifact file.
    artifact_name
        Human‑readable name for the artifact; defaults to the filename.
    state_file
        Path to the state YAML file; defaults to ``state/projects/...yaml``.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Artifact not found: {path}")

    hash_val = compute_checksum(path)
    name = artifact_name or path.name

    # Determine default state file location
    if state_file is None:
        default_state = STATE_DIR / "projects" / "PROJ-712-predicting-individual-pain-sensitivity-f.yaml"
        state_path = Path(default_state)
    else:
        state_path = Path(state_file)

    # Load existing state or start a new dict
    if state_path.is_file():
        with state_path.open("r") as sf:
            state_data = yaml.safe_load(sf) or {}
    else:
        state_data = {}

    # Ensure the top‑level key exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"][name] = {"sha256": hash_val, "timestamp": get_current_timestamp()}

    # Write back
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w") as sf:
        yaml.safe_dump(state_data, sf)


# ----------------------------------------------------------------------
# Timing helpers
# ----------------------------------------------------------------------
def get_current_timestamp() -> str:
    """Return the current UTC timestamp in ISO‑8601 format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def measure_duration(func: Callable) -> Callable:
    """
    Decorator that measures the execution time of ``func`` and logs it.

    The wrapped function receives no extra arguments.
    """

    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger = logging.getLogger(func.__module__ or "__main__")
        logger.info(f"Duration of {func.__name__}: {elapsed:.2f} seconds")
        return result

    return wrapper


def assert_duration_limit(duration_seconds: float, limit_seconds: Optional[float] = None) -> None:
    """
    Verify that ``duration_seconds`` does not exceed ``limit_seconds``.

    The default limit is ``MAX_EXECUTION_SECONDS`` (6 h). Raises
    ``AssertionError`` on violation.
    """
    limit = limit_seconds if limit_seconds is not None else MAX_EXECUTION_SECONDS
    if duration_seconds > limit:
        raise AssertionError(
            f"Execution time {duration_seconds:.2f}s exceeds limit of {limit:.2f}s"
        )


# Simple global timer used by ``start_timer`` / ``stop_timer``
_global_start_time: Optional[float] = None


def start_timer() -> float:
    """Start a global timer for the pipeline."""
    global _global_start_time
    _global_start_time = time.time()
    return _global_start_time


def stop_timer() -> float:
    """
    Stop the global timer and enforce the SC‑005 execution limit.

    Returns the total elapsed time in seconds.
    """
    if _global_start_time is None:
        raise RuntimeError("Timer was not started. Call start_timer() first.")
    elapsed = time.time() - _global_start_time
    assert_duration_limit(elapsed)
    return elapsed


# ----------------------------------------------------------------------
# Citation validation (used by the pre‑run validation script)
# ----------------------------------------------------------------------
def _load_required_citations() -> List[str]:
    """
    Return a list of required citation identifiers.

    For this project we keep a very small hard‑coded list.
    In a real implementation this could be read from a
    ``citations.yaml`` or similar file.
    """
    # Example identifiers – adjust as the project evolves
    return ["doi:10.1234/example1", "doi:10.5678/example2"]


def _load_existing_citations() -> List[str]:
    """
    Load the project's citation file and return the identifiers found.

    The convention is a plain text file ``CITATIONS.bib`` in the
    repository root where each line contains a DOI or similar ID.
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
        from checksums import scan_raw_data_directory, record_checksums_to_state

        raw_dir = Path("data") / "raw"
        state_file = (
            STATE_DIR
            / "projects"
            / "PROJ-712-predicting-individual-pain-sensitivity-f.yaml"
        )

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