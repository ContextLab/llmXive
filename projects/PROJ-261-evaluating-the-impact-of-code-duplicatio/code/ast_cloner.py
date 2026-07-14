"""
ast_cloner.py
---------------
Provides utilities to parse Python source files, normalize identifiers,
and compute a simple clone‑density metric across a corpus.
The implementation is deliberately lightweight so that it can run on the
modest CI resources used for this project while still producing a real
measurement.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)

class IdentifierNormalizer(ast.NodeTransformer):
    """
    Normalises all identifier names (variables, function names, etc.) to a
    generic placeholder so that syntactically identical code that only
    differs by naming is recognised as a Type‑2 clone.
    """
    def visit_Name(self, node: ast.Name) -> ast.AST:  # pragma: no cover
        return ast.copy_location(ast.Name(id="__VAR__", ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.AST:  # pragma: no cover
        return ast.copy_location(ast.arg(arg="__ARG__", annotation=node.annotation), node)

def parse_python_file(source: str) -> ast.AST:
    """
    Parse a Python source string and return its normalized AST.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logger.error("Syntax error while parsing source: %s", exc)
        raise
    normaliser = IdentifierNormalizer()
    normalized = normaliser.visit(tree)
    ast.fix_missing_locations(normalized)
    return normalized

def _hash_normalized_ast(tree: ast.AST) -> str:
    """
    Produce a deterministic hash for a normalized AST.
    """
    dump = ast.dump(tree, include_attributes=False)
    return hashlib.sha256(dump.encode("utf-8")).hexdigest()

def _load_corpus(
    input_path: Path,
) -> List[Tuple[str, str]]:
    """
    Load a CSV corpus. Expected columns: ``file_path`` and ``code``.
    Returns a list of (file_path, source_code) tuples.
    """
    if not input_path.is_file():
        logger.warning("Input corpus %s does not exist – returning empty list.", input_path)
        return []
    rows: List[Tuple[str, str]] = []
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"file_path", "code"}
        if not required.issubset(reader.fieldnames or []):
            logger.error("Input CSV %s missing required columns %s", input_path, required)
            raise ValueError("Invalid input CSV format")
        for row in reader:
            rows.append((row["file_path"], row["code"]))
    return rows

def compute_clone_density_batch(
    input_path: Path | None = None,
    output_path: Path | None = None,
    *args,
    **kwargs,
) -> None:
    """
    Compute a very simple clone‑density metric for a corpus of Python files.

    Parameters are deliberately flexible:
    * ``input_path`` – optional Path to a CSV file containing ``file_path`` and ``code`` columns.
    * ``output_path`` – optional Path where the resulting CSV will be written.
    * Positional arguments are interpreted in order (input_path, output_path) for backward
      compatibility with older call‑sites.
    * Keyword arguments are also accepted.

    If neither ``input_path`` nor ``output_path`` is supplied the function falls back
    to the default locations used throughout the project:

        input_path  = Path("data/raw/github-code-sample.csv")
        output_path = Path("data/processed/clone_metrics.csv")
    """
    # Resolve positional arguments for legacy signatures
    if args:
        if len(args) >= 1 and input_path is None:
            input_path = args[0]
        if len(args) >= 2 and output_path is None:
            output_path = args[1]

    # Resolve keyword arguments (already handled by the signature)

    # Apply defaults
    if input_path is None:
        input_path = Path("data/raw/github-code-sample.csv")
    if output_path is None:
        output_path = Path("data/processed/clone_metrics.csv")

    logger.info("Computing clone density from %s → %s", input_path, output_path)

    corpus = _load_corpus(input_path)
    total = len(corpus)
    if total == 0:
        logger.warning("Empty corpus – writing zero density.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["clone_density"])
            writer.writeheader()
            writer.writerow({"clone_density": 0.0})
        return

    # Normalise each file and compute hash
    hash_counts: Dict[str, int] = {}
    for _, source in corpus:
        try:
            norm_ast = parse_python_file(source)
        except SyntaxError:
            # Skip files that cannot be parsed – they are logged elsewhere.
            continue
        h = _hash_normalized_ast(norm_ast)
        hash_counts[h] = hash_counts.get(h, 0) + 1

    # Clone density = (total files - number of unique hashes) / total files
    unique = len(hash_counts)
    clone_density = (total - unique) / total

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["clone_density"])
        writer.writeheader()
        writer.writerow({"clone_density": clone_density})

    logger.info("Clone density computed: %.4f", clone_density)
