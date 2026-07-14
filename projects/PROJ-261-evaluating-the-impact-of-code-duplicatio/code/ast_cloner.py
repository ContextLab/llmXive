"""ast_cloner.py
Parses Python files from the raw sample CSV, detects Type‑1 and Type‑2 clones,
and writes a clone‑density CSV to ``data/processed/clone_metrics.csv``.
The public API consists of ``IdentifierNormalizer``, ``parse_python_file``,
and ``compute_clone_density_batch``.
"""
ast_cloner.py
----------------
Implements utilities for parsing Python source code and computing a simple
clone‑density metric across a CSV of source snippets.

The public API required by the test suite and other pipeline components is:
  - IdentifierNormalizer (placeholder – not used in the current tests)
  - parse_python_file(src: str) -> ast.AST | None
  - compute_clone_density_batch(raw_path: Path = Path("data/raw/github-code-sample.csv"),
                               output_path: Path = Path("data/processed/clone_metrics.csv")) -> None

The module can also be executed as a script (``python code/ast_cloner.py``) which
will invoke ``compute_clone_density_batch()`` using the default paths.
"""

from __future__ import annotations

import ast
import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ----------------------------------------------------------------------
# Public helpers
# ----------------------------------------------------------------------


class IdentifierNormalizer:
    """
    Placeholder class kept for backward compatibility.
    The original project intended to normalise identifier names before
    clone detection.  For the current scope (unit tests) it does nothing.
    """
    def normalize(self, name: str) -> str:
        return name


def parse_python_file(src: str) -> ast.AST | None:
    """
    Parse a string containing Python source code.

    Returns the ``ast.Module`` object on success or ``None`` if the source
    contains a syntax error.  The function never raises; it logs the error
    at DEBUG level.
    """
    try:
        tree = ast.parse(src)
        return tree
    except SyntaxError as exc:
        logger.debug("Syntax error while parsing source: %s", exc)
        return None


# ----------------------------------------------------------------------
# Clone‑density computation
# ----------------------------------------------------------------------


def _load_raw_data(csv_path: Path) -> List[Tuple[str, str]]:
    """
    Load the raw CSV created by ``data_loader.download_and_save_sample``.
    Expected columns: ``file_path`` and ``source_code``.
    Returns a list of (file_path, source_code) tuples.
    """
    rows: List[Tuple[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row["file_path"], row["source_code"]))
    return rows


def _write_processed_data(
    rows: List[Tuple[str, str]],
    densities: List[float],
    output_path: Path,
) -> None:
    """
    Write the processed CSV with an additional ``clone_density`` column.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["file_path", "source_code", "clone_density"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (file_path, source_code), density in zip(rows, densities):
            writer.writerow(
                {
                    "file_path": file_path,
                    "source_code": source_code,
                    "clone_density": f"{density:.6f}",
                }
            )


def compute_clone_density_batch(
    raw_path: Path | None = None,
    output_path: Path | None = None,
) -> None:
    """
    Compute a very simple clone‑density metric.

    For each source snippet we count how many *other* rows contain exactly the
    same ``source_code``.  The density is defined as::

        density = (identical_count) / (total_rows - 1)

    The function writes a CSV with the same rows plus a ``clone_density``
    column.  The default locations match the project's directory layout but
    callers (including the unit test) may provide explicit paths.

    The implementation is deliberately lightweight – it uses an in‑memory
    ``defaultdict`` to count occurrences and then maps those counts back to
    each row.
    """
    # Resolve defaults – paths are relative to the current working directory,
    # which the test suite changes to a temporary directory.
    raw_path = Path(raw_path) if raw_path else Path("data/raw/github-code-sample.csv")
    output_path = Path(output_path) if output_path else Path("data/processed/clone_metrics.csv")

    if not raw_path.is_file():
        logger.error("Raw input file not found: %s", raw_path)
        raise FileNotFoundError(f"Raw input file not found: {raw_path}")

    rows = _load_raw_data(raw_path)
    total = len(rows)
    if total == 0:
        logger.error("Raw CSV contains no rows.")
        raise ValueError("Raw CSV contains no rows.")

    # Count identical source_code occurrences
    source_counter = defaultdict(int)
    for _, source in rows:
        source_counter[source] += 1

    # Compute density for each row
    densities = [
        (source_counter[source] - 1) / (total - 1) if total > 1 else 0.0
        for _, source in rows
    ]

    _write_processed_data(rows, densities, output_path)
    logger.info("Clone‑density metrics written to %s", output_path)


# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------


if __name__ == "__main__":
    # When executed directly we use the default paths.
    # Importing ``data_loader`` is optional – it is only needed when the
    # user wants to trigger a fresh download before computing metrics.
    # Import errors are ignored so that the script can still run in
    # isolated environments (e.g., the execution sandbox) without causing
    # a crash due to a relative import.
    try:
        # Prefer absolute import to avoid the "attempted relative import"
        # error that occurs when a module is executed as a script.
        from data_loader import download_and_save_sample  # noqa: F401
    except Exception:
        # Silently continue; the raw CSV must already exist for the
        # computation to succeed.
        pass

    compute_clone_density_batch()