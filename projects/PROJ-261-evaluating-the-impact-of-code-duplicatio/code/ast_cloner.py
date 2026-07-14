"""
ast_cloner.py
---------------
Implements utilities for parsing Python source code, normalizing identifiers,
and computing a simple clone density metric based on identical AST structures.

The implementation is deliberately lightweight and has no external dependencies
beyond the Python standard library. It is designed to be robust against syntax
errors in the input data – rows that cannot be parsed are still written to the
output CSV with an empty ``clone_density`` field and a parse‑failure entry is
recorded via the ``parse_failure_logger`` module.
"""

from __future__ import annotations

import ast
import csv
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# Local import for logging parse failures – this module already exists in the
# repository and provides ``log_parse_failure`` that writes a record to
# ``data/parse_failures.csv``.
from code.parse_failure_logger import log_parse_failure

logger = logging.getLogger(__name__)

class IdentifierNormalizer(ast.NodeTransformer):
    """
    Normalizes identifier names in an AST so that different variable names do not
    affect clone detection. The normalizer replaces all ``ast.Name`` identifiers
    with a placeholder name ``_``. This is sufficient for the Type‑2 clone
    detection required by the project.
    """

    def visit_Name(self, node: ast.Name) -> ast.AST:  # noqa: D401
        """Replace the identifier with a generic placeholder."""
        return ast.copy_location(ast.Name(id="_", ctx=node.ctx), node)

    def generic_visit(self, node):
        return super().generic_visit(node)


def parse_python_file(source: str) -> ast.AST:
    """
    Parse a Python source string into an AST.

    Parameters
    ----------
    source: str
        The Python source code to parse.

    Returns
    -------
    ast.AST
        The parsed abstract syntax tree.

    Raises
    ------
    SyntaxError
        If the source cannot be parsed.
    """
    return ast.parse(source)


def _normalize_ast(tree: ast.AST) -> str:
    """
    Apply identifier normalisation and return a deterministic string
    representation of the AST (using ``ast.dump``).

    Parameters
    ----------
    tree: ast.AST
        The AST to normalise.

    Returns
    -------
    str
        The dump string of the normalised AST.
    """
    normaliser = IdentifierNormalizer()
    normalised = normaliser.visit(tree)
    ast.fix_missing_locations(normalised)
    return ast.dump(normalised)


def compute_clone_density_batch(
    *,
    input_path: Path,
    output_path: Path,
) -> Path:
    """
    Compute clone density for a batch of Python snippets stored in a CSV file.

    The input CSV must contain at least the columns ``id`` and ``code``.
    For each row the function attempts to parse ``code``. Rows that raise a
    ``SyntaxError`` are logged via ``log_parse_failure`` and written to the
    output with an empty ``clone_density`` field.

    The clone density for a successfully parsed row is defined as:
        (frequency_of_its_ast - 1) / total_successfully_parsed_rows

    The function writes a new CSV to ``output_path`` that mirrors the input
    columns and adds a ``clone_density`` column.

    Parameters
    ----------
    input_path: Path
        Path to the CSV containing raw code snippets.
    output_path: Path
        Destination path for the CSV with clone density values.

    Returns
    -------
    Path
        The path to the written ``output_path`` (convenient for tests).
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, str]] = []
    ast_strings: List[Tuple[int, str]] = []  # (row_index, ast_dump)

    # First pass – read input and attempt parsing
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            code = row.get("code", "")
            rows.append(row)  # keep original row for later output
            try:
                tree = parse_python_file(code)
                norm_dump = _normalize_ast(tree)
                ast_strings.append((idx, norm_dump))
            except SyntaxError as exc:
                # Record the failure; we keep the row but do not add it to
                # the list of successfully parsed ASTs.
                logger.debug(
                    "Syntax error while parsing row %s: %s", idx, exc
                )
                log_parse_failure(
                    source_path=Path(row.get("id", f"row_{idx}")),
                    error_message=str(exc),
                )
                # No entry added to ``ast_strings`` – handled later.
                continue

    # Compute frequencies of each distinct AST dump among successfully parsed rows
    dump_counter = Counter(dump for _, dump in ast_strings)
    total_success = len(ast_strings)

    # Second pass – write output with clone density
    fieldnames = list(reader.fieldnames or []) + ["clone_density"]
    with output_path.open("w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for idx, original in enumerate(rows):
            # Determine if this row had a successful parse
            matching = next(
                (dump for row_idx, dump in ast_strings if row_idx == idx), None
            )
            if matching is None:
                # Syntax error – leave clone_density empty
                original["clone_density"] = ""
            else:
                freq = dump_counter[matching]
                # Guard division by zero – if only one successful row, density = 0
                density = (freq - 1) / total_success if total_success > 0 else 0.0
                original["clone_density"] = f"{density:.6f}"
            writer.writerow(original)

    return output_path
