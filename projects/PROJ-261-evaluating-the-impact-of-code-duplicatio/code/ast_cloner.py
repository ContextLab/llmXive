"""
ast_cloner.py
----------------
Implements utilities for parsing Python source code, normalising ASTs and
computing a simple clone‑density metric across a CSV of code snippets.

Public API
----------
- IdentifierNormalizer: class used to normalise identifiers in an AST.
- parse_python_file(path: Path) -> ast.AST | None: parses a file, returns
  the AST or ``None`` if a syntax error occurs (the error is logged).
- compute_clone_density_batch(input_path: Path, output_path: Path | None = None) -> Path:
  reads a CSV with columns ``id`` and ``code``, computes clone density for
  each row, writes the results to ``output_path`` (or a default location) and
  returns the path of the written file.

The implementation is deliberately lightweight and has no external
dependencies beyond the Python standard library. It is tolerant of a wide
range of call signatures (positional, keyword, defaults) to satisfy the
contract described in the task description.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import logging
from collections import Counter
from pathlib import Path
from typing import Optional

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Helper: parse_failure_logger integration
# ----------------------------------------------------------------------
try:
    # The parse_failure_logger module is part of the project and provides
    # a ``log_parse_failure`` function that records the path of a file that
    # could not be parsed.
    from parse_failure_logger import log_parse_failure
except Exception:  # pragma: no cover
    # In environments where the module is not available (e.g. isolated
    # unit‑test runs) we fall back to a no‑op implementation.
    def log_parse_failure(_path: Path, _error: Exception) -> None:  # type: ignore
        logger.debug("parse_failure_logger not available – ignoring parse failure.")

# ----------------------------------------------------------------------
# Identifier normaliser
# ----------------------------------------------------------------------
class IdentifierNormalizer(ast.NodeTransformer):
    """
    Normalises identifier names in an AST so that syntactically identical
    fragments that differ only by variable/function names are considered
    clones (Type‑2 clones).

    The normalisation strategy is simple: every ``ast.Name`` node is
    replaced with a deterministic placeholder based on its order of
    appearance.
    """

    def __init__(self) -> None:
        super().__init__()
        self._counter = 0
        self._mapping: dict[str, str] = {}

    def _next_placeholder(self) -> str:
        self._counter += 1
        return f"__id{self._counter}__"

    def visit_Name(self, node: ast.Name) -> ast.AST:  # noqa: D401
        """Replace the identifier with a placeholder."""
        if node.id not in self._mapping:
            self._mapping[node.id] = self._next_placeholder()
        node.id = self._mapping[node.id]
        return node

    def generic_visit(self, node):
        """Override generic_visit to ensure we walk the tree."""
        return super().generic_visit(node)

# ----------------------------------------------------------------------
# Core parsing function
# ----------------------------------------------------------------------
def parse_python_file(path: Path) -> Optional[ast.AST]:
    """
    Parse a Python file and return its AST.

    If a ``SyntaxError`` (or any ``Exception``) occurs, the error is logged
    via ``log_parse_failure`` and ``None`` is returned.
    """
    try:
        source = path.read_text(encoding="utf-8")
        return ast.parse(source)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to parse %s: %s", path, exc)
        # Record the failure for downstream analysis.
        log_parse_failure(path, exc)
        return None

# ----------------------------------------------------------------------
# Clone‑density computation
# ----------------------------------------------------------------------
def _normalise_ast(tree: ast.AST) -> str:
    """
    Return a deterministic string representation of an AST after normalising
    identifiers. The representation is suitable for hashing/comparison.
    """
    normaliser = IdentifierNormalizer()
    normalised_tree = normaliser.visit(tree)
    ast.fix_missing_locations(normalised_tree)
    # ``ast.dump`` with ``include_attributes=False`` gives a stable string.
    return ast.dump(normalised_tree, include_attributes=False)

def compute_clone_density_batch(
    input_path: Path,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Compute clone density for each row in a CSV file.

    Parameters
    ----------
    input_path: Path
        Path to the CSV containing at least the columns ``id`` and ``code``.
    output_path: Path | None
        Destination for the output CSV.  If omitted, the file is written
        alongside ``input_path`` with the name ``clone_metrics.csv``.

    Returns
    -------
    Path
        The path of the CSV that was written.
    """
    # ------------------------------------------------------------------
    # Resolve arguments (support positional, keyword and defaults)
    # ------------------------------------------------------------------
    if not isinstance(input_path, Path):
        raise TypeError("input_path must be a pathlib.Path")
    if output_path is None:
        output_path = input_path.parent / "clone_metrics.csv"

    # ------------------------------------------------------------------
    # Load raw rows
    # ------------------------------------------------------------------
    rows = []
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    total_rows = len(rows)
    if total_rows == 0:
        logger.info("No rows to process in %s", input_path)
        # Still write an empty output file with header.
        with output_path.open("w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(
                f_out, fieldnames=["id", "code", "clone_density"]
            )
            writer.writeheader()
        return output_path

    # ------------------------------------------------------------------
    # Parse each snippet, normalise its AST, and build a frequency map.
    # ------------------------------------------------------------------
    normalised_strings = []
    valid_indices = []  # indices of rows that parsed successfully
    for idx, row in enumerate(rows):
        code = row.get("code", "")
        # Write the snippet to a temporary file so ``parse_python_file`` can
        # reuse its logging behaviour.
        tmp_path = input_path.parent / f"__tmp_{idx}.py"
        tmp_path.write_text(code, encoding="utf-8")
        tree = parse_python_file(tmp_path)
        tmp_path.unlink(missing_ok=True)  # clean up
        if tree is None:
            # Parsing failed – leave ``clone_density`` empty for this row.
            normalised_strings.append(None)
        else:
            normalised_strings.append(_normalise_ast(tree))
            valid_indices.append(idx)

    # ------------------------------------------------------------------
    # Compute frequencies of each normalised AST among the successfully
    # parsed rows.
    # ------------------------------------------------------------------
    freq_counter = Counter(s for s in normalised_strings if s is not None)

    # ------------------------------------------------------------------
    # Write output CSV
    # ------------------------------------------------------------------
    with output_path.open("w", newline="", encoding="utf-8") as f_out:
        fieldnames = ["id", "code", "clone_density"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(rows):
            norm = normalised_strings[idx]
            if norm is None:
                # Syntax error – we record an empty string for density.
                density = ""
            else:
                # Clone density = (frequency of this pattern - 1) / total_rows
                density = (freq_counter[norm] - 1) / total_rows
            writer.writerow(
                {
                    "id": row.get("id", ""),
                    "code": row.get("code", ""),
                    "clone_density": density,
                }
            )
    logger.info("Clone‑density CSV written to %s", output_path)
    return output_path