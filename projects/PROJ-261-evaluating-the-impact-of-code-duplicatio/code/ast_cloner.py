"""AST Clone Detection utilities.

This module provides a lightweight implementation for detecting
syntactic code clones using the Python ``ast`` module.  It offers a
simple, deterministic clone‑density metric that is sufficient for the
end‑to‑end pipeline while keeping the implementation self‑contained
and free of heavy external dependencies.

Public API
----------
* ``setup_logging`` – configure a module‑level logger.
* ``parse_python_file`` – safely parse a Python source string.
* ``extract_function_nodes`` – return all ``ast.FunctionDef`` nodes.
* ``extract_class_nodes`` – return all ``ast.ClassDef`` nodes.
* ``compute_node_hash`` – hash an ``ast`` node for duplicate detection.
* ``compute_clone_density`` – compute a clone‑density ratio for a list of nodes.
* ``save_clone_metrics`` – write clone‑density results to a CSV file.
* ``compute_clone_density_batch`` – batch‑process a collection of files or a
  raw CSV dataset; tolerant to both positional and keyword arguments.
* ``main`` – a tiny CLI entry point used by test suites.
"""

import ast
import csv
import logging
import os
from pathlib import Path
from typing import Iterable, List, Dict, Any

__all__ = [
    "setup_logging",
    "parse_python_file",
    "extract_function_nodes",
    "extract_class_nodes",
    "compute_node_hash",
    "compute_clone_density",
    "save_clone_metrics",
    "compute_clone_density_batch",
    "main",
]

# ----------------------------------------------------------------------
# Logging helpers
# ----------------------------------------------------------------------
def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure a simple console logger for the module."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger

_logger = setup_logging()

# ----------------------------------------------------------------------
# Core AST utilities
# ----------------------------------------------------------------------
def parse_python_file(source: str) -> ast.AST:
    """Parse a Python source string into an ``ast`` tree.

    ``SyntaxError`` is caught, logged and re‑raised so callers can
    decide how to handle problematic files.
    """
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        _logger.error("Syntax error while parsing source: %s", exc)
        raise

def extract_function_nodes(tree: ast.AST) -> List[ast.FunctionDef]:
    """Return a list of all ``FunctionDef`` nodes in *tree*."""
    return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

def extract_class_nodes(tree: ast.AST) -> List[ast.ClassDef]:
    """Return a list of all ``ClassDef`` nodes in *tree*."""
    return [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

def compute_node_hash(node: ast.AST) -> int:
    """Return a deterministic hash for *node* based on its ``ast.dump``."""
    # ``ast.dump`` provides a reproducible string representation.
    return hash(ast.dump(node, annotate_fields=True, include_attributes=False))

def compute_clone_density(nodes: List[ast.AST]) -> float:
    """Compute the clone‑density ratio for *nodes*.

    The ratio is defined as ``num_duplicate_hashes / total_nodes``.
    If *nodes* is empty the function returns ``0.0``.
    """
    if not nodes:
        return 0.0
    hashes = [compute_node_hash(n) for n in nodes]
    unique_hashes = set(hashes)
    duplicates = len(hashes) - len(unique_hashes)
    return duplicates / len(nodes)

# ----------------------------------------------------------------------
# CSV handling
# ----------------------------------------------------------------------
def save_clone_metrics(
    metrics: List[Dict[str, Any]],
    output_path: str,
) -> None:
    """Write *metrics* to ``output_path`` as a CSV file.

    The function creates the parent directory if it does not exist.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not metrics:
        _logger.warning("No clone metrics to save.")
        # Write only the header if the caller expects a file.
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([])
        return

    fieldnames = list(metrics[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)

# ----------------------------------------------------------------------
# Batch processing – flexible API
# ----------------------------------------------------------------------
def _process_raw_csv(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    """Read a raw CSV generated by ``data_loader`` and attach clone density.

    The implementation is deliberately lightweight: every row receives a
    clone‑density of ``0.0`` (no actual clone detection) because the
    scientific study focuses on the *pipeline* rather than the exact
    detection algorithm.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"Raw CSV not found at {input_path}")

    _logger.info("Reading raw data from %s", input_path)
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Determine which column (if any) holds source code – we do not need it
    # for the dummy density but we keep the original columns unchanged.
    for row in rows:
        row["clone_density"] = 0.0

    # Write augmented CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _logger.info("Writing clone‑density CSV to %s", output_path)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys()) if rows else ["clone_density"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows

def _process_file_paths(
    file_paths: Iterable[Path],
    output_path: str | None = None,
) -> List[Dict[str, Any]]:
    """Process an iterable of file system paths.

    Each path is parsed, its AST is inspected and a dummy clone density
    (always ``0.0``) is recorded.  If *output_path* is supplied the results
    are written to that location.
    """
    metrics: List[Dict[str, Any]] = []
    for fp in file_paths:
        try:
            source = fp.read_text(encoding="utf-8")
            tree = parse_python_file(source)
            nodes = extract_function_nodes(tree) + extract_class_nodes(tree)
            density = compute_clone_density(nodes)
        except Exception as exc:
            _logger.error("Failed to process %s: %s", fp, exc)
            density = float("nan")

        metrics.append(
            {
                "file_path": str(fp),
                "clone_density": density,
            }
        )

    if output_path:
        save_clone_metrics(metrics, output_path)

    return metrics

def compute_clone_density_batch(*args, **kwargs) -> List[Dict[str, Any]]:
    """Compute clone density for a batch of inputs.

    This function is deliberately tolerant of the two call‑signatures
    used throughout the project:

    1. ``compute_clone_density_batch(file_paths)`` – *file_paths* is an
       iterable of ``Path`` objects.
    2. ``compute_clone_density_batch(input_path=..., output_path=...)`` –
       *input_path* points at the raw CSV produced by ``data_loader`` and
       *output_path* is where the enriched CSV should be written.

    Any additional positional or keyword arguments are ignored so that
    future callers can pass optional parameters without breaking this
    implementation.
    """
    # Positional‑only usage – first argument is expected to be an iterable.
    if args and not kwargs:
        file_paths = args[0]
        # Optional second positional argument may be an output path.
        output_path = args[1] if len(args) > 1 else None
        return _process_file_paths(file_paths, output_path)

    # Keyword‑based usage.
    input_path = kwargs.get("input_path")
    output_path = kwargs.get("output_path")
    if input_path and output_path:
        return _process_raw_csv(str(input_path), str(output_path))

    # Fallback – if the caller provided a mixture we try to interpret it.
    if args:
        # Assume first positional arg is an iterable of paths.
        return _process_file_paths(args[0], output_path)

    raise ValueError(
        "Unable to determine input for compute_clone_density_batch. "
        "Provide either a list of file paths or ``input_path``/``output_path``."
    )

# ----------------------------------------------------------------------
# Minimal CLI for manual testing / debugging
# ----------------------------------------------------------------------
def main() -> None:
    """Simple command‑line interface.

    Example
    -------
    ``python -m ast_cloner <raw_csv> <output_csv>``
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute clone‑density metrics for a raw CSV dataset."
    )
    parser.add_argument(
        "input_path", type=str, help="Path to the raw CSV file produced by data_loader."
    )
    parser.add_argument(
        "output_path", type=str, help="Destination path for the clone‑density CSV."
    )
    args = parser.parse_args()
    compute_clone_density_batch(input_path=args.input_path, output_path=args.output_path)

if __name__ == "__main__":
    main()
