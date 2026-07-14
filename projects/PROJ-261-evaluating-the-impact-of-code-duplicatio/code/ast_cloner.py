"""
ast_cloner.py
----------------
Provides utilities to parse Python source code and compute a simple
clone‑density metric based on the proportion of AST nodes that belong to
duplicated code fragments.  For the purposes of this research project the
metric is deliberately lightweight – it merely counts total AST nodes per
file and reports the fraction of nodes that appear in more than one file.
The implementation is pure‑Python and has no external dependencies beyond
the standard library.

Public API
----------
* IdentifierNormalizer – normalises AST identifiers (used by the original
  implementation; retained for compatibility).
* parse_python_file – parses a Python source string into an ``ast.Module``.
* compute_clone_density_batch – orchestrates the batch computation; accepts
  flexible signatures to satisfy callers (see contract notes).
"""
from __future__ import annotations

import ast
import csv
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, List, Tuple

from config import get_all_config

logger = logging.getLogger(__name__)


class IdentifierNormalizer(ast.NodeTransformer):
    """
    Normalises identifiers in an AST so that syntactically identical
    fragments with different names are considered clones (Type‑2 clones).
    The transformer replaces all identifier names with a placeholder.
    """

    def visit_Name(self, node: ast.Name) -> ast.AST:  # pragma: no cover
        return ast.copy_location(ast.Name(id="_ID_", ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.AST:  # pragma: no cover
        return ast.copy_location(ast.arg(arg="_ARG_", annotation=node.annotation), node)


def parse_python_file(source: str) -> ast.Module:
    """
    Parse a Python source string into an ``ast.Module``.

    Parameters
    ----------
    source: str
        The Python source code.

    Returns
    -------
    ast.Module
    """
    return ast.parse(source)


def _read_raw_dataset(csv_path: Path) -> List[Tuple[str, str]]:
    """
    Read the raw CSV produced by :func:`data_loader.download_and_save_sample`.
    Expected columns: ``file_path`` and ``content``.

    Returns
    -------
    List[Tuple[str, str]]
        List of (file_path, source_code) tuples.
    """
    records = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append((row["file_path"], row["content"]))
    return records


def _write_clone_metrics(
    rows: List[Tuple[str, int, float]], output_path: Path
) -> None:
    """
    Write clone‑density metrics to CSV.

    Parameters
    ----------
    rows: List[Tuple[str, int, float]]
        Each tuple contains (file_path, node_count, clone_density).
    output_path: Path
        Destination CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "node_count", "clone_density"])
        writer.writerows(rows)


def compute_clone_density_batch(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """
    Compute a lightweight clone‑density metric for every Python file in the
    supplied CSV.  The function is deliberately tolerant to the calling
    patterns used throughout the project:

    * ``compute_clone_density_batch()`` – no arguments.
    * ``compute_clone_density_batch(input_path)`` – positional input only.
    * ``compute_clone_density_batch(input_path=…, output_path=…)`` – keyword args.

    If *input_path* is omitted, the default location
    ``data/raw/github-code-sample.csv`` is used.  If *output_path* is omitted,
    the results are written to ``data/processed/clone_metrics.csv``.

    Returns
    -------
    Path
        The path to the generated CSV file.
    """
    cfg = get_all_config()
    default_input = Path("data/raw/github-code-sample.csv")
    default_output = Path("data/processed/clone_metrics.csv")

    input_path = Path(input_path) if input_path else default_input
    output_path = Path(output_path) if output_path else default_output

    logger.info("Computing clone density from %s → %s", input_path, output_path)

    records = _read_raw_dataset(input_path)

    # ------------------------------------------------------------------
    # Simple clone‑density heuristic:
    #   * Parse each file's AST.
    #   * Count total nodes per file.
    #   * Build a global Counter of the string representation of each node.
    #   * Nodes that appear in more than one file are considered “cloned”.
    #   * Clone density = (cloned_node_count / total_node_count) per file.
    # ------------------------------------------------------------------
    total_node_counter = Counter()
    file_node_maps: List[Tuple[str, Counter]] = []

    for file_path, source in records:
        try:
            tree = parse_python_file(source)
        except SyntaxError as exc:
            logger.warning("Syntax error in %s: %s – skipping", file_path, exc)
            continue

        node_strings = [ast.dump(node) for node in ast.walk(tree)]
        counter = Counter(node_strings)
        file_node_maps.append((file_path, counter))
        total_node_counter.update(counter)

    # Identify cloned nodes (appear in ≥2 files)
    cloned_nodes = {node for node, cnt in total_node_counter.items() if cnt > 1}

    output_rows: List[Tuple[str, int, float]] = []
    for file_path, counter in file_node_maps:
        total_nodes = sum(counter.values())
        cloned_in_file = sum(cnt for node, cnt in counter.items() if node in cloned_nodes)
        density = cloned_in_file / total_nodes if total_nodes > 0 else 0.0
        output_rows.append((file_path, total_nodes, density))

    _write_clone_metrics(output_rows, output_path)

    logger.info("Clone‑density CSV written to %s", output_path)
    return output_path