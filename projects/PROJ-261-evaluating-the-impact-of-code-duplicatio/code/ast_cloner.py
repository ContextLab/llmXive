"""
ast_cloner.py
---------------
Provides utilities for parsing Python source files with the ``ast`` module,
detecting simple Type‑1 (exact) and Type‑2 (renamed identifiers) clones, and
computing a *clone density* metric.

The public function ``compute_clone_density_batch`` is deliberately tolerant
to a variety of call signatures (no arguments, positional ``input_path``,
keyword ``input_path=…``) to satisfy the contract required by many callers.
"""

from __future__ import annotations

import ast
import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Iterable, List, Tuple

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _read_raw_csv(csv_path: Path) -> List[Tuple[str, str]]:
    """
    Reads ``data/raw/github-code-sample.csv`` which is expected to have two
    columns: ``file_path`` and ``code``. Returns a list of tuples.
    """
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((row["file_path"], row["code"]))
    return rows

def parse_python_file(source: str) -> ast.AST | None:
    """
    Parse a Python source string into an ``ast.AST``. Returns ``None`` if the
    source cannot be parsed (syntax error). The caller is expected to log
    parse failures via ``parse_failure_logger`` if desired.
    """
    try:
        return ast.parse(source)
    except SyntaxError:
        logger.debug("Syntax error while parsing source")
        return None

def _canonicalize_ast(node: ast.AST) -> str:
    """
    Produce a simple string representation of an AST node that is
    *insensitive* to identifier names – this is used for Type‑2 clone
    detection. The implementation walks the tree and replaces ``Name`` and
    ``arg`` identifiers with a placeholder token.
    """
    class NameReplacer(ast.NodeTransformer):
        def visit_Name(self, n: ast.Name) -> ast.AST:  # noqa: N802
            return ast.copy_location(ast.Name(id="_VAR_", ctx=n.ctx), n)

        def visit_arg(self, n: ast.arg) -> ast.AST:  # noqa: N802
            return ast.copy_location(ast.arg(arg="_ARG_", annotation=n.annotation), n)

    stripped = NameReplacer().visit(node)
    ast.fix_missing_locations(stripped)
    return ast.dump(stripped, annotate_fields=False, include_attributes=False)

def _detect_clones(
    ast_trees: List[Tuple[str, ast.AST]]
) -> Tuple[int, int]:
    """
    Very lightweight clone detector:

    * Type‑1 clones – identical AST dumps.
    * Type‑2 clones – identical after identifier canonicalisation.

    Returns a tuple ``(type1_count, type2_count)`` where each count is the
    number of *pairs* of files that are clones of the respective type.
    """
    type1_counter = defaultdict(list)
    type2_counter = defaultdict(list)

    for path, tree in ast_trees:
        dump = ast.dump(tree, annotate_fields=False, include_attributes=False)
        type1_counter[dump].append(path)

        canon = _canonicalize_ast(tree)
        type2_counter[canon].append(path)

    def _pair_count(groups: dict) -> int:
        total = 0
        for items in groups.values():
            n = len(items)
            if n > 1:
                total += n * (n - 1) // 2
        return total

    return _pair_count(type1_counter), _pair_count(type2_counter)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def compute_clone_density_batch(*args, **kwargs) -> None:
    """
    Compute clone density for the dataset and write ``clone_metrics.csv``.

    The function is deliberately permissive in its signature to satisfy
    all callers:

    * ``compute_clone_density_batch()`` – uses the default
      ``data/raw/github-code-sample.csv``.
    * ``compute_clone_density_batch(input_path)`` – positional argument.
    * ``compute_clone_density_batch(input_path=path)`` – keyword argument.

    The output CSV has the columns:

    ``file_path,clone_density,type1_clones,type2_clones``
    """
    # Resolve the input path from the flexible signature
    if args:
        input_path = Path(args[0])
    else:
        input_path = Path(kwargs.get("input_path", "data/raw/github-code-sample.csv"))

    logger.info("Computing clone density from %s", input_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    rows = _read_raw_csv(input_path)

    # Parse each source file; keep track of failures for downstream logging
    parsed: List[Tuple[str, ast.AST]] = []
    total_lines = 0
    for file_path, code in rows:
        tree = parse_python_file(code)
        if tree is not None:
            parsed.append((file_path, tree))
            total_lines += len(code.splitlines())
        else:
            logger.debug("Skipping file with parse error: %s", file_path)

    type1_pairs, type2_pairs = _detect_clones(parsed)

    # Clone density = (number of clone pairs * 2) / total lines
    # (each pair touches two files). Guard against division by zero.
    clone_density = (
        (type1_pairs + type2_pairs) * 2 / total_lines if total_lines > 0 else 0.0
    )

    output_path = Path("data/processed/clone_metrics.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file_path", "clone_density", "type1_clones", "type2_clones"],
        )
        writer.writeheader()
        for file_path, _ in parsed:
            writer.writerow(
                {
                    "file_path": file_path,
                    "clone_density": f"{clone_density:.6f}",
                    "type1_clones": type1_pairs,
                    "type2_clones": type2_pairs,
                }
            )

    logger.info(
        "Clone density computation finished – %d files processed, output written to %s",
        len(parsed),
        output_path,
    )
