"""
normalize_data.py
-----------------
Implements Task T004c-normalize: Normalize Dataset Filename.

This script scans the ``data/raw`` directory for CSV files produced by the
extraction step (T004c-extract). It selects the most appropriate CSV according
to the specification:

1. Prefer a file whose name matches the pattern ``*barrier*.csv`` (case‑insensitive).
2. If no such file exists, select the largest ``.csv`` file by file size.
3. Move/rename the selected file to the canonical path
   ``data/raw/barrier_dataset.csv``.

The script logs its actions to ``logs/normalization.log`` and aborts with a
clear exception if no CSV files are found.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_logger(log_path: Path) -> logging.Logger:
    """Create a logger that writes to *log_path* and also streams to stdout."""
    logger = logging.getLogger("normalize_data")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if this function is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(log_path, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

# ----------------------------------------------------------------------
# Core functionality
# ----------------------------------------------------------------------
def find_csv_candidates(raw_dir: Path, logger: logging.Logger) -> List[Path]:
    """
    Return a list of all ``.csv`` files under *raw_dir* (recursive).

    Parameters
    ----------
    raw_dir: Path
        Directory where the Zenodo extraction placed its files.
    logger: logging.Logger
        Logger for diagnostic messages.

    Returns
    -------
    List[Path]
        List of candidate CSV files (may be empty).
    """
    csv_files = list(raw_dir.rglob("*.csv"))
    logger.info(f"Discovered {len(csv_files)} CSV file(s) in {raw_dir}")
    return csv_files

def select_target_csv(csv_files: List[Path], logger: logging.Logger) -> Path:
    """
    Apply the selection rules defined in the task description.

    1. Prefer files whose name contains the word ``barrier`` (case‑insensitive).
    2. If multiple match, pick the largest by size.
    3. If no match, pick the largest CSV overall.

    Parameters
    ----------
    csv_files: List[Path]
        List of candidate CSV files.
    logger: logging.Logger

    Returns
    -------
    Path
        The chosen CSV file.
    """
    if not csv_files:
        raise FileNotFoundError("No CSV files found for normalization.")

    # Step 1 – pattern match
    barrier_matches = [
        f for f in csv_files if "barrier" in f.name.lower()
    ]

    if barrier_matches:
        chosen = max(barrier_matches, key=lambda p: p.stat().st_size)
        logger.info(
            f"Selected pattern‑matched CSV: {chosen.name} ({chosen.stat().st_size} bytes)"
        )
        return chosen

    # Step 2 – fallback to largest CSV
    chosen = max(csv_files, key=lambda p: p.stat().st_size)
    logger.info(
        f"No pattern match found. Selected largest CSV: {chosen.name} ({chosen.stat().st_size} bytes)"
    )
    return chosen

def normalize_dataset(raw_dir: Path, logger: logging.Logger) -> Path:
    """
    Perform the full normalization workflow.

    Parameters
    ----------
    raw_dir: Path
        Directory containing the extracted files.
    logger: logging.Logger

    Returns
    -------
    Path
        Path to the canonical ``barrier_dataset.csv`` file.
    """
    csv_candidates = find_csv_candidates(raw_dir, logger)
    target_csv = select_target_csv(csv_candidates, logger)

    canonical_path = raw_dir / "barrier_dataset.csv"

    # Move (or rename) the file. ``replace`` overwrites any existing file.
    logger.info(f"Renaming {target_csv} → {canonical_path}")
    target_csv.replace(canonical_path)

    logger.info(f"Normalization complete: {canonical_path}")
    return canonical_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize the extracted barrier dataset CSV to a canonical filename."
    )
    # No positional arguments are required; the script works entirely on the
    # project’s ``data/raw`` directory.
    return parser

def main() -> None:
    """
    Main entry point used by the pipeline (``code/main.py``) and by the test
    suite. It creates required directories, configures logging, and runs the
    normalization routine.
    """
    # Resolve paths relative to the repository root
    project_root = Path(__file__).resolve().parents[1]  # <repo_root>
    raw_dir = project_root / "data" / "raw"
    log_path = project_root / "logs" / "normalization.log"

    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(log_path)

    # Parse (currently unused) CLI arguments – kept for future extensibility
    parser = build_arg_parser()
    parser.parse_args()  # No arguments expected

    try:
        result_path = normalize_dataset(raw_dir, logger)
        logger.info(f"Canonical dataset ready at: {result_path}")
        print(f"Success: {result_path}")
    except Exception as exc:
        logger.error(f"Normalization failed: {exc}")
        print(f"Normalization failed: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
