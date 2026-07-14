"""
ast_cloner.py
---------------
Provides utilities to parse Python files, normalize identifiers, and compute
clone density across a collection of source files.

The public API consists of:
  - IdentifierNormalizer
  - parse_python_file
  - compute_clone_density_batch
The ``compute_clone_density_batch`` function is deliberately flexible:
it accepts positional or keyword arguments for ``input_path`` and
``output_path`` (or none, in which case sensible defaults are used).
"""

from __future__ import annotations

import ast
import csv
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)

class IdentifierNormalizer(ast.NodeTransformer):
    """
    Normalises identifier names in an AST to generic placeholders.
    This enables detection of Type‑2 clones (parameterised copies) by
    stripping away concrete variable/function names while preserving
    structural information.
    """
    def __init__(self) -> None:
        super().__init__()
        self._counter = 0
        self._mapping: dict[str, str] = {}

    def _generic_name(self) -> str:
        name = f"var_{self._counter}"
        self._counter += 1
        return name

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id not in self._mapping:
            self._mapping[node.id] = self._generic_name()
        node.id = self._mapping[node.id]
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if node.name not in self._mapping:
            self._mapping[node.name] = self._generic_name()
        node.name = self._mapping[node.name]
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self.visit_FunctionDef(node)  # reuse logic

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        if node.name not in self._mapping:
            self._mapping[node.name] = self._generic_name()
        node.name = self._mapping[node.name]
        self.generic_visit(node)
        return node

def parse_python_file(file_path: Path) -> str:
    """
    Reads a Python source file and returns its textual content.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to read %s: %s", file_path, exc)
        raise

def _resolve_paths(*args, **kwargs) -> Tuple[Path, Path]:
    """
    Helper that interprets the flexible calling conventions for
    ``compute_clone_density_batch``.

    Supported signatures:
      compute_clone_density_batch()
      compute_clone_density_batch(input_path=Path(...))
      compute_clone_density_batch(output_path=Path(...))
      compute_clone_density_batch(input_path, output_path)
      compute_clone_density_batch(input_path, output_path, ...)  # extra ignored
    """
    # defaults
    default_input = Path("data/raw")
    default_output = Path("data/processed/clone_metrics.csv")

    input_path: Path | None = None
    output_path: Path | None = None

    # Positional arguments
    if args:
        if len(args) >= 1:
            input_path = Path(args[0])
        if len(args) >= 2:
            output_path = Path(args[1])

    # Keyword arguments
    if "input_path" in kwargs:
        input_path = Path(kwargs["input_path"])
    if "output_path" in kwargs:
        output_path = Path(kwargs["output_path"])

    if input_path is None:
        input_path = default_input
    if output_path is None:
        output_path = default_output

    return input_path, output_path

def compute_clone_density_batch(*args, **kwargs) -> None:
    """
    Computes clone density for all Python files under ``input_path`` and writes a
    CSV summary to ``output_path``.

    The function is tolerant of various calling conventions (positional,
    keyword, or none) to satisfy all existing callers.
    """
    input_path, output_path = _resolve_paths(*args, **kwargs)

    rows: List[Dict[str, str]] = []
    ast_strings: List[Tuple[int, str]] = []  # (row_index, ast_dump)

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Gather all *.py files recursively
    py_files = list(input_path.rglob("*.py"))
    if not py_files:
        logger.warning("No Python files found under %s", input_path)
        # Still write an empty CSV with headers
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["total_files", "clone_files", "clone_density"])
            writer.writerow([0, 0, 0.0])
        return

    # Mapping from normalized source representation to list of file paths
    normalized_map: dict[str, List[Path]] = {}
    total_parsed = 0

    for file_path in py_files:
        try:
            source = parse_python_file(file_path)
            tree = ast.parse(source)
            # Normalise identifiers for Type‑2 clone detection
            normaliser = IdentifierNormalizer()
            normalised_tree = normaliser.visit(tree)
            # ast.unparse requires Python 3.9+
            normalised_src = ast.unparse(normalised_tree)
            normalized_map.setdefault(normalised_src, []).append(file_path)
            total_parsed += 1
        except SyntaxError as exc:
            logger.error("Syntax error in %s: %s", file_path, exc)
            # Skip files that cannot be parsed; they will be logged elsewhere
            continue
        except Exception as exc:
            logger.exception("Unexpected error processing %s: %s", file_path, exc)
            continue

    # Determine clone groups (size > 1)
    clone_groups = {k: v for k, v in normalized_map.items() if len(v) > 1}
    clone_files = sum(len(paths) for paths in clone_groups.values())
    clone_density = clone_files / total_parsed if total_parsed else 0.0

    # Write summary CSV
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["total_files", "clone_files", "clone_density"])
        writer.writerow([total_parsed, clone_files, f"{clone_density:.6f}"])

    logger.info(
        "Clone density computation finished: %d total, %d clone files, density %.4f",
        total_parsed,
        clone_files,
        clone_density,
    )
