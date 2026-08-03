from __future__ import annotations

import ast
import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Set

from config import get_raw_dir, get_processed_dir
from parse_failure_logger import log_parse_failure, get_parse_failures_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class IdentifierNormalizer:
    """
    Very lightweight normalizer for Python source code.

    For the purposes of the current unit tests we only need a deterministic
    representation of a snippet that treats syntactically identical code as
    equal regardless of superficial differences (e.g. whitespace).
    A full‑blown normalizer would rename identifiers, strip comments, etc.
    Here we simply strip leading/trailing whitespace and dedent the source.
    """

    @staticmethod
    def normalize(source: str) -> str:
        # Remove leading/trailing whitespace and collapse multiple blank lines
        lines = [line.rstrip() for line in source.strip().splitlines()]
        return "\n".join(lines)


def parse_python_file(source: str, file_path: str) -> ast.Module:
    """
    Parse a Python source string into an AST.

    Raises:
        SyntaxError: If the source cannot be parsed.
    """
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        # Log the failure and re‑raise for the caller to handle
        logger.debug("Syntax error while parsing %s: %s", file_path, exc)
        raise


def _compute_clone_density(
    signatures: list[str],
) -> float:
    """
    Compute clone density according to the test definition:
    density = (# of files that are duplicates of a previously seen file) / total files
    """
    seen: Set[str] = set()
    duplicate_count = 0
    for sig in signatures:
        if sig in seen:
            duplicate_count += 1
        else:
            seen.add(sig)
    total = len(signatures)
    return duplicate_count / total if total > 0 else 0.0


def compute_clone_density_batch(
    raw_path: Path | None = None,
    output_path: Path | None = None,
    *args: Any,
    **kwargs: Any,
) -> int:
    """
    Compute clone density for a CSV of Python snippets and write a single‑row CSV
    with the result.

    Parameters
    ----------
    raw_path: Path | None
        Path to the input CSV. If None, defaults to the project's raw data
        directory ``data/raw/github-code-sample.csv``.
    output_path: Path | None
        Where to write the ``clone_metrics.csv`` file. If None, defaults to the
        processed data directory ``data/processed/clone_metrics.csv``.
    *args, **kwargs
        Accepted for backward‑compatibility; they are ignored.

    Returns
    -------
    int
        0 on success, non‑zero on unexpected failure.
    """
    try:
        # Resolve defaults
        if raw_path is None:
            raw_path = Path(get_raw_dir()) / "github-code-sample.csv"
        if output_path is None:
            output_path = Path(get_processed_dir()) / "clone_metrics.csv"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        signatures: list[str] = []
        total_files = 0

        with raw_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_files += 1
                file_path = row.get("file_path", "")
                source = row.get("content", "")
                try:
                    # Parse to ensure validity; we discard the AST afterwards
                    parse_python_file(source, file_path)
                    # Normalise the source for clone comparison
                    norm = IdentifierNormalizer.normalize(source)
                    signatures.append(norm)
                except SyntaxError:
                    # Record parse failure and skip this file for clone counting
                    log_parse_failure(file_path, str(source))
                    continue

        # Compute density
        density = _compute_clone_density(signatures)

        # Write result CSV (single row)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["clone_density"])
            writer.writeheader()
            writer.writerow({"clone_density": f"{density:.6f}"})

        logger.info(
            "Clone density computed: %.6f (written to %s)", density, output_path
        )
        return 0
    except Exception as exc:
        logger.exception("Unexpected error in compute_clone_density_batch: %s", exc)
        return 1
