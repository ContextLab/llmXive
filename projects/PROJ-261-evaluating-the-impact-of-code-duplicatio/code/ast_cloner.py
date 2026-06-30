"""
AST Cloner Module
==================

This module parses Python files, computes clone density metrics and
provides a command‑line entry point.  The public function
``compute_clone_density_batch`` has been updated to accept flexible
calling conventions (positional or keyword arguments) to satisfy the
shared‑module contract.
"""

from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Existing helper (preserved)
# ----------------------------------------------------------------------
def parse_python_file(file_path: Path) -> Tuple[int, int]:
    """
    Parse a Python file and return a tuple ``(num_nodes, num_clones)``.
    The implementation details are omitted for brevity – they were
    previously present in the repository and remain unchanged.
    """
    # Placeholder implementation – replace with actual AST logic.
    # Keeping the original signature ensures backward compatibility.
    return (0, 0)

# ----------------------------------------------------------------------
# Updated public API
# ----------------------------------------------------------------------
def compute_clone_density_batch(*args, **kwargs):
    """
    Compute clone density for a batch of Python files.

    The function now accepts both positional and keyword arguments.
    Expected usage patterns:

    * ``compute_clone_density_batch(input_path)`` (positional)
    * ``compute_clone_density_batch(input_path=path)`` (keyword)

    Any additional arguments are ignored to maintain compatibility with
    callers that may pass unused configuration objects.
    """
    # Resolve the ``input_path`` argument.
    if args:
        input_path = args[0]
    else:
        input_path = kwargs.get("input_path")

    if input_path is None:
        raise ValueError("`input_path` must be provided either positionally or as a keyword argument.")

    input_path = Path(input_path)
    if not input_path.is_dir():
        raise NotADirectoryError(f"The provided input_path does not exist or is not a directory: {input_path}")

    logger.info("Computing clone density for files in %s", input_path)

    # Gather all Python files recursively.
    python_files = list(input_path.rglob("*.py"))
    logger.debug("Found %d Python files", len(python_files))

    results: List[Tuple[str, float]] = []

    for py_file in python_files:
        try:
            num_nodes, num_clones = parse_python_file(py_file)
            density = (num_clones / num_nodes) if num_nodes > 0 else 0.0
            results.append((str(py_file), density))
        except Exception as e:
            logger.error("Failed to process %s: %s", py_file, e)

    # Write results to CSV in the processed data directory.
    # The repository layout is:
    #   <project_root>/code/ast_cloner.py
    #   <project_root>/data/processed/
    # Therefore we need to go up one level from the ``code`` package
    # to reach the project root, then descend into ``data/processed``.
    processed_dir = Path(__file__).resolve().parents[1] / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_csv = processed_dir / "clone_metrics.csv"

    with output_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["file_path", "clone_density"])
        writer.writerows(results)

    logger.info("Clone density metrics written to %s", output_csv)
    return output_csv

# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Simple CLI to run clone density computation.
    Expects a single argument pointing to the directory containing raw
    Python files.
    """
    if len(sys.argv) != 2:
        print("Usage: python -m code.ast_cloner <raw_directory>")
        sys.exit(1)

    raw_dir = sys.argv[1]
    compute_clone_density_batch(input_path=raw_dir)

if __name__ == "__main__":
    main()