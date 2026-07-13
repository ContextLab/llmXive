from __future__ import annotations

import ast
import csv
import hashlib
import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional, Union

from parse_failure_logger import init_logger, log_parse_failure

# ----------------------------------------------------------------------
# Logger setup
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    init_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _ensure_processed_dir() -> Path:
    """Make sure the processed data directory exists and return its Path."""
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def _hash_source(source: str) -> str:
    """Return a deterministic SHA‑256 hash for the given source string."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()

class _NormalizeNamesTransformer(ast.NodeTransformer):
    """
    Normalise identifier names in an AST so that structurally identical
    code with different variable / argument names hashes to the same value.
    """

    def __init__(self):
        super().__init__()
        self._counter = 0
        self._name_map: dict[str, str] = {}

    def _generic_name(self) -> str:
        """Generate a placeholder name like ``_var0``."""
        name = f"_var{self._counter}"
        self._counter += 1
        return name

    def _map_name(self, original: str) -> str:
        """Map an original identifier to a deterministic placeholder."""
        if original not in self._name_map:
            self._name_map[original] = self._generic_name()
        return self._name_map[original]

    # Replace variable and attribute names
    def visit_Name(self, node: ast.Name) -> ast.AST:  # type: ignore[override]
        node.id = self._map_name(node.id)
        return node

    # Replace function argument names
    def visit_arg(self, node: ast.arg) -> ast.AST:  # type: ignore[override]
        node.arg = self._map_name(node.arg)
        return node

    # Replace attribute accesses (e.g., ``obj.attr``) – we keep the attribute
    # name but normalise the base object name.
    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:  # type: ignore[override]
        self.generic_visit(node)
        if isinstance(node.value, ast.Name):
            node.value.id = self._map_name(node.value.id)  # type: ignore[attr-defined]
        return node

def _normalized_ast_hash(source: str) -> str:
    """
    Parse *source* into an AST, normalise identifier names, and return a
    deterministic hash of the normalised tree.  This hash is used to detect
    Type‑2 (parameterised) clones.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Should never be called on syntactically invalid code – callers guard.
        return ""
    transformer = _NormalizeNamesTransformer()
    normalised_tree = transformer.visit(tree)
    ast.fix_missing_locations(normalised_tree)
    dump = ast.dump(normalised_tree, annotate_fields=False, include_attributes=False)
    return _hash_source(dump)

# ----------------------------------------------------------------------
# Core implementation
# ----------------------------------------------------------------------
def compute_clone_density_batch(
    input_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Compute clone‑density metrics for a batch of Python files.

    The function is deliberately tolerant to the various call signatures
    required by the project (positional argument, keyword argument,
    default call, etc.).

    Output CSV (``data/processed/clone_metrics.csv``) contains three columns:
    ``file_path``, ``clone_density`` (0.0 for first occurrence, 1.0 for a
    duplicate), and ``clone_type`` (``type1``, ``type2`` or ``unique``).
    """
    # Resolve the input directory
    src_dir = Path(input_path) if input_path is not None else Path("data/raw")

    if not src_dir.is_dir():
        logger.error("Input path %s does not exist or is not a directory.", src_dir)
        return

    # ------------------------------------------------------------------
    # First pass – exact (type‑1) clones
    # ------------------------------------------------------------------
    exact_hash_to_paths: defaultdict[str, list[Path]] = defaultdict(list)
    file_to_source: dict[Path, str] = {}

    for py_file in src_dir.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
            ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError) as exc:
            logger.warning("Syntax error in %s: %s", py_file, exc)
            log_parse_failure(str(py_file), str(exc))
            continue
        except Exception as exc:  # pragma: no cover – safety net
            logger.exception("Unexpected error while parsing %s", py_file)
            log_parse_failure(str(py_file), str(exc))
            continue

        file_hash = _hash_source(source)
        exact_hash_to_paths[file_hash].append(py_file)
        file_to_source[py_file] = source

    # ------------------------------------------------------------------
    # Second pass – parameterised (type‑2) clones for files that are not
    # exact duplicates.
    # ------------------------------------------------------------------
    type2_hash_to_paths: defaultdict[str, list[Path]] = defaultdict(list)

    for py_file, source in file_to_source.items():
        # Skip files already part of a type‑1 clone group with >1 member
        # (they will be reported as type‑1).
        exact_hash = _hash_source(source)
        if len(exact_hash_to_paths[exact_hash]) > 1:
            continue

        norm_hash = _normalized_ast_hash(source)
        if norm_hash:
            type2_hash_to_paths[norm_hash].append(py_file)

    # ------------------------------------------------------------------
    # Write results
    # ------------------------------------------------------------------
    processed_dir = _ensure_processed_dir()
    csv_path = processed_dir / "clone_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["file_path", "clone_density", "clone_type"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Helper to write a group of paths with a given type
        def _write_group(paths: list[Path], clone_type: str) -> None:
            for idx, file_path in enumerate(paths):
                density = 1.0 if idx > 0 else 0.0
                writer.writerow(
                    {
                        "file_path": str(file_path),
                        "clone_density": f"{density:.6f}",
                        "clone_type": clone_type,
                    }
                )

        # Write Type‑1 groups
        for paths in exact_hash_to_paths.values():
            if len(paths) == 1:
                _write_group(paths, "unique")
            else:
                _write_group(paths, "type1")

        # Write Type‑2 groups (exclude files already written)
        written: set[Path] = {Path(row["file_path"]) for row in []}  # placeholder
        for paths in type2_hash_to_paths.values():
            # Keep only files that were not part of a Type‑1 duplicate group
            unique_paths = [p for p in paths if len(exact_hash_to_paths[_hash_source(file_to_source[p])]) == 1]
            if len(unique_paths) == 1:
                _write_group(unique_paths, "unique")
            else:
                _write_group(unique_paths, "type2")

    logger.info("Clone density CSV written to %s", csv_path)

# ----------------------------------------------------------------------
# Script entry‑point – allows ``python code/ast_cloner.py`` to be used
# directly in the quick‑start run‑book.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # When invoked without arguments we use the default ``data/raw`` directory.
    compute_clone_density_batch()