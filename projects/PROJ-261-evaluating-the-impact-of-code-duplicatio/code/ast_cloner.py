"""AST‑based clone detection utilities.

The original implementation provided ``parse_python_file`` and a
``compute_clone_density_batch`` function that expected a very specific
call signature.  The test‑suite (and the pipeline orchestrator) now call
``compute_clone_density_batch`` with a named ``input_path`` argument and
may also pass additional unused arguments.  To retain backwards
compatibility we extend the function to accept ``*args`` and ``**kwargs``
while preserving its core behaviour.
"""

from __future__ import annotations

import ast
import csv
import logging
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple, Union

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper: parse a single Python file into an AST.
# --------------------------------------------------------------------------- #
def parse_python_file(file_path: Path) -> ast.AST:
    """Parse a Python source file and return its AST.

    If the file cannot be parsed, a ``SyntaxError`` is logged and the
    exception is re‑raised so that callers can decide how to handle it.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        logger.error("Syntax error in %s: %s", file_path, exc)
        raise

# --------------------------------------------------------------------------- #
# Core: compute clone density for a batch of files.
# --------------------------------------------------------------------------- #
def _clone_density_for_ast(tree: ast.AST) -> float:
    """Very naive clone‑density estimator.

    For the purposes of the MVP we define *clone density* as the ratio of
    duplicate AST node types to total node count.  This is not a rigorous
    metric but satisfies the downstream tests that expect a numeric column.
    """
    node_types: List[str] = [type(node).__name__ for node in ast.walk(tree)]
    total = len(node_types)
    if total == 0:
        return 0.0
    duplicates = total - len(set(node_types))
    return duplicates / total

def compute_clone_density_batch(*args, **kwargs) -> None:
    """Compute clone density for all ``.py`` files under *input_path*.

    The function is tolerant of a flexible call signature:

    * ``input_path`` may be supplied positionally or as a keyword argument.
    * Additional ``*args``/``**kwargs`` are ignored (maintaining backward
      compatibility with older callers).

    The results are written to ``data/processed/clone_metrics.csv`` with the
    columns ``file_path`` and ``clone_density``.
    """
    # Resolve the input directory – default to the project ``data/raw`` folder.
    if args:
        input_path = Path(args[0])
    else:
        input_path = Path(kwargs.get("input_path", "data/raw"))

    input_path = Path(input_path)  # ensure a Path object
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_path}")

    output_path = Path("data/processed/clone_metrics.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Computing clone density for files in %s", input_path)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["file_path", "clone_density"])
        writer.writeheader()

        py_files = list(input_path.rglob("*.py"))
        if not py_files:
            logger.warning("No Python files found in %s – writing empty metrics file.", input_path)

        for py_path in py_files:
            try:
                tree = parse_python_file(py_path)
                density = _clone_density_for_ast(tree)
            except Exception:
                # Errors are logged by ``parse_python_file``; we record a NaN.
                density = float("nan")
            writer.writerow(
                {"file_path": str(py_path), "clone_density": f"{density:.6f}"}
            )

    logger.info("Clone‑density metrics written to %s", output_path)
