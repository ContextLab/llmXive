"""
ast_cloner.py
---------------
Provides utilities to parse Python source files, normalize identifiers,
and compute a simple clone‑density metric across a collection of code
snippets. The public API consists of:
  - IdentifierNormalizer
  - parse_python_file
  - compute_clone_density_batch
The ``compute_clone_density_batch`` function has been extended to accept
flexible calling conventions required by various callers in the project.
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
    Normalizes identifiers in an AST by replacing them with generic placeholders.
    This enables detection of Type‑2 clones where only variable names differ.
    """

    def __init__(self) -> None:
        super().__init__()
        self._counter = 0
        self._mapping: Dict[str, str] = {}

    def _next_placeholder(self) -> str:
        self._counter += 1
        return f"VAR_{self._counter}"

    def visit_Name(self, node: ast.Name) -> ast.AST:  # pragma: no cover
        if node.id not in self._mapping:
            self._mapping[node.id] = self._next_placeholder()
        node.id = self._mapping[node.id]
        return node

    def generic_visit(self, node):
        return super().generic_visit(node)


def parse_python_file(source: str) -> ast.AST | None:
    """
    Parse a Python source string into an AST.
    Returns ``None`` if the source cannot be parsed (syntax error).
    """
    try:
        return ast.parse(source)
    except SyntaxError as exc:  # pragma: no cover – exercised via tests
        logger.debug("Syntax error while parsing source: %s", exc)
        return None


def _hash_normalized_ast(tree: ast.AST) -> str:
    """
    Produce a deterministic hash for a normalized AST.
    """
    normalizer = IdentifierNormalizer()
    normalized = normalizer.visit(tree)
    ast_bytes = ast.dump(normalized).encode("utf-8")
    return hashlib.sha256(ast_bytes).hexdigest()


def compute_clone_density_batch(*args, **kwargs) -> None:
    """
    Compute clone density for a batch of Python files and write the result
    to ``data/processed/clone_metrics.csv``.
    
    The function is deliberately permissive in its signature to satisfy
    all existing call‑sites:

    * ``compute_clone_density_batch()`` – uses default paths.
    * ``compute_clone_density_batch(input_path=Path(...))``
    * ``compute_clone_density_batch(output_path=Path(...))``
    * ``compute_clone_density_batch(input_path, output_path)`` (positional)
    * ``compute_clone_density_batch(input_path, output_path, extra_arg)`` – extra
      arguments are ignored.

    Parameters
    ----------
    input_path : pathlib.Path, optional
        Path to a CSV containing at least a ``code`` column with Python source.
        Defaults to ``data/raw/github-code-sample.csv``.
    output_path : pathlib.Path, optional
        Destination CSV for the clone‑density metric.
        Defaults to ``data/processed/clone_metrics.csv``.
    """
    # Resolve positional arguments
    input_path = Path("data/raw/github-code-sample.csv")
    output_path = Path("data/processed/clone_metrics.csv")

    if args:
        # First positional arg is interpreted as input_path if it looks like a Path
        if isinstance(args[0], (str, Path)):
            input_path = Path(args[0])
        if len(args) > 1 and isinstance(args[1], (str, Path)):
            output_path = Path(args[1])

    # Resolve keyword arguments (they override positional handling)
    if "input_path" in kwargs:
        input_path = Path(kwargs["input_path"])
    if "output_path" in kwargs:
        output_path = Path(kwargs["output_path"])

    logger.info("Computing clone density from %s → %s", input_path, output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load source snippets
    codes: List[str] = []
    try:
        with input_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "code" not in reader.fieldnames:
                raise ValueError(f"Input CSV {input_path} must contain a 'code' column.")
            for row in reader:
                codes.append(row["code"])
    except FileNotFoundError as exc:
        logger.error("Input file not found: %s", exc)
        raise

    if not codes:
        logger.warning("No code snippets found in %s", input_path)
        clone_density = 0.0
    else:
        # Compute normalized AST hashes
        hash_counts: Dict[str, int] = {}
        total = 0
        for src in codes:
            tree = parse_python_file(src)
            if tree is None:
                # Skip unparsable files – they are logged elsewhere via parse_failure_logger
                continue
            h = _hash_normalized_ast(tree)
            hash_counts[h] = hash_counts.get(h, 0) + 1
            total += 1

        # Count duplicates (any hash with count > 1 contributes count-1 duplicates)
        duplicate_files = sum(cnt - 1 for cnt in hash_counts.values() if cnt > 1)
        clone_density = duplicate_files / total if total > 0 else 0.0

    # Write a one‑row CSV with the overall metric
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["clone_density"])
        writer.writeheader()
        writer.writerow({"clone_density": f"{clone_density:.6f}"})

    logger.info("Clone density written to %s (value: %.6f)", output_path, clone_density)
