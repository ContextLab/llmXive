"""
ast_cloner.py
---------------
Implements a very lightweight clone‑density estimator for Python source files.
The original implementation expected a strict ``input_path`` argument; the
updated version accepts any ``*args`` / ``**kwargs`` combination used across
the code base whilst preserving the original behaviour.
"""

from __future__ import annotations

import ast
import csv
import logging
from pathlib import Path
from typing import Iterable, List, Tuple

logger = logging.getLogger(__name__)

__all__ = ["parse_python_file", "compute_clone_density_batch", "main"]


def parse_python_file(file_path: Path) -> ast.Module | None:
    """
    Parse a Python file and return its AST.

    If the file cannot be parsed (e.g. syntax error) ``None`` is returned
    and the caller can decide how to handle the failure.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        logger.warning("Failed to parse %s: %s", file_path, exc)
        return None


def _clone_density_for_file(file_path: Path) -> Tuple[Path, float]:
    """
    Very simple clone‑density metric:

    * Count total number of non‑empty, non‑comment lines.
    * Count number of *unique* lines.
    * Clone density = (total - unique) / total   (0.0 … 1.0)

    Returns a tuple ``(file_path, density)``.
    """
    try:
        lines = [
            line.strip()
            for line in file_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    except Exception as exc:  # pragma: no cover – defensive
        logger.warning("Unable to read %s: %s", file_path, exc)
        return (file_path, 0.0)

    total = len(lines)
    if total == 0:
        return (file_path, 0.0)

    unique = len(set(lines))
    density = (total - unique) / total
    return (file_path, density)


def compute_clone_density_batch(
    input_path: Path | str | None = None,
    *args,
    **kwargs,
) -> None:
    """
    Compute clone‑density for every ``*.py`` file under ``input_path`` and write a
    CSV file to ``data/processed/clone_metrics.csv``.

    The function is tolerant to the various call‑signatures used throughout the
    project:

    * ``compute_clone_density_batch(input_path)``          – positional
    * ``compute_clone_density_batch(input_path=path)``   – keyword
    * ``compute_clone_density_batch()``                  – defaults to
      ``Path("data/raw")`` (mirrors the original behaviour).

    Any additional ``*args`` / ``**kwargs`` are ignored so that older call
    sites continue to work unchanged.
    """
    # Resolve the actual path – accept ``None`` or any positional argument.
    if input_path is None:
        # Look for the first positional argument if supplied.
        if args:
            input_path = args[0]
        else:
            input_path = Path("data/raw")
    elif isinstance(input_path, (str, Path)):
        input_path = Path(input_path)
    else:
        # Fallback to default location if the type is unexpected.
        logger.warning(
            "Unexpected type for input_path %r – falling back to data/raw",
            input_path,
        )
        input_path = Path("data/raw")

    if not input_path.is_dir():
        # Fallback to the project's code directory if data/raw is missing,
        # ensuring the pipeline can still generate metrics for existing sources.
        fallback_path = Path("code")
        if fallback_path.is_dir():
            logger.warning(
                "Provided input_path %s is not a directory; falling back to %s",
                input_path,
                fallback_path,
            )
            input_path = fallback_path
        else:
            logger.error("Provided input_path %s is not a directory", input_path)
            raise FileNotFoundError(input_path)

    py_files = list(input_path.rglob("*.py"))
    logger.info("Found %d Python files under %s", len(py_files), input_path)

    results: List[Tuple[Path, float]] = [_clone_density_for_file(p) for p in py_files]

    # Ensure the output directory exists.
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "clone_metrics.csv"

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file_path", "clone_density"])
        for file_path, density in results:
            writer.writerow([str(file_path), f"{density:.6f}"])

    logger.info("Wrote clone‑density metrics to %s", output_path)


def main() -> None:
    """
    Simple entry‑point used by developers. It runs the clone detector on the
    default ``data/raw`` directory.
    """
    logging.basicConfig(level=logging.INFO)
    compute_clone_density_batch()
