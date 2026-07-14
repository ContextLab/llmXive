"""
ast_cloner.py
----------------
Utilities for detecting AST‑based code clones and computing clone density.
This module provides:
* IdentifierNormalizer – a simple AST NodeTransformer that replaces all
  identifier names with generic placeholders (var_0, var_1, …) so that
  Type‑1 clones (exact copies) and Type‑2 clones (renamed identifiers) can
  be detected via string comparison of the normalized source.
* parse_python_file – reads a Python source file, validates that it is
  syntactically correct (raises ``SyntaxError`` on failure) and returns the
  raw text.
* compute_clone_density_batch – scans a directory of ``.py`` files,
  groups files that are clones, and writes a CSV file containing the total
  number of files, the number of files that belong to a clone group, and
  the clone density (clone_files / total_files).  The function accepts
  optional ``input_path`` and ``output_path`` arguments; when called with
  no arguments it falls back to the project‑wide defaults
  ``data/raw`` and ``data/processed/clone_metrics.csv`` respectively.
The implementation is deliberately lightweight and relies only on the
Python standard library so that it can run in constrained CI environments.
"""

from __future__ import annotations

import ast
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class IdentifierNormalizer(ast.NodeTransformer):
    """
    Replace all identifier names (variables, function names, arguments, etc.)
    with generic placeholders ``var_0``, ``var_1`` … to normalise code for
    Type‑2 clone detection.
    """

    def __init__(self) -> None:
        super().__init__()
        self.counter: int = 0
        self.mapping: Dict[str, str] = {}

    def _next_placeholder(self) -> str:
        placeholder = f"var_{self.counter}"
        self.counter += 1
        return placeholder

    def _map_name(self, name: str) -> str:
        if name not in self.mapping:
            self.mapping[name] = self._next_placeholder()
        return self.mapping[name]

    def visit_Name(self, node: ast.Name) -> ast.AST:  # type: ignore[override]
        new_name = self._map_name(node.id)
        return ast.copy_location(ast.Name(id=new_name, ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.AST:  # type: ignore[override]
        new_name = self._map_name(node.arg)
        return ast.copy_location(ast.arg(arg=new_name, annotation=node.annotation, type_comment=node.type_comment), node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # type: ignore[override]
        # Normalise the function name itself
        node.name = self._map_name(node.name)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:  # type: ignore[override]
        node.name = self._map_name(node.name)
        self.generic_visit(node)
        return node

def parse_python_file(file_path: Path) -> str:
    """
    Read a Python file and ensure it is syntactically valid.

    Parameters
    ----------
    file_path: Path
        Path to the ``.py`` file.

    Returns
    -------
    str
        The raw file contents.

    Raises
    ------
    SyntaxError
        If the file cannot be parsed as valid Python.
    """
    source = file_path.read_text(encoding="utf-8")
    try:
        ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        logger.error("Syntax error in %s: %s", file_path, exc)
        # Re‑raise so callers (including tests) can react.
        raise
    return source

def _normalise_source(source: str) -> str:
    """
    Normalise source code by parsing it into an AST, applying the
    ``IdentifierNormalizer`` and unparsing back to source text.
    """
    tree = ast.parse(source)
    normaliser = IdentifierNormalizer()
    normalised_tree = normaliser.visit(tree)
    ast.fix_missing_locations(normalised_tree)
    return ast.unparse(normalised_tree)

def compute_clone_density_batch(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> None:
    """
    Compute clone density for a batch of Python files.

    Parameters
    ----------
    input_path: Path | None
        Directory containing ``.py`` files.  Defaults to ``data/raw``.
    output_path: Path | None
        CSV file to write the results to.  Defaults to
        ``data/processed/clone_metrics.csv``.
    """
    # Resolve defaults
    if input_path is None:
        input_path = Path("data") / "raw"
    if output_path is None:
        output_path = Path("data") / "processed" / "clone_metrics.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Raw sample directory not found: {input_path}")

    # Gather all .py files recursively
    py_files: List[Path] = list(input_path.rglob("*.py"))
    total_files = len(py_files)
    if total_files == 0:
        logger.warning("No Python files found in %s", input_path)
        # Still write a CSV with zeros so downstream scripts do not fail.
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["total_files", "clone_files", "clone_density"])
            writer.writerow([0, 0, 0.0])
        return

    # Normalise each file's source and map normalised source -> list of files
    norm_map: Dict[str, List[Path]] = {}
    for py_file in py_files:
        try:
            raw_source = parse_python_file(py_file)
            norm_source = _normalise_source(raw_source)
            norm_map.setdefault(norm_source, []).append(py_file)
        except SyntaxError:
            # Syntax‑error files are ignored for clone density calculations
            # but could be logged elsewhere (parse_failure_logger).
            continue

    # Determine how many files belong to a clone group (size >= 2)
    clone_files = sum(len(files) for files in norm_map.values() if len(files) >= 2)

    clone_density = clone_files / total_files if total_files > 0 else 0.0

    # Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["total_files", "clone_files", "clone_density"])
        writer.writerow([total_files, clone_files, clone_density])