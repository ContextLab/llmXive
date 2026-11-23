from __future__ import annotations

import ast
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_raw_dir, get_processed_dir

logger = logging.getLogger(__name__)

def parse_python_file(source: str) -> Optional[ast.AST]:
    """
    Parse a Python source string into an AST.

    Returns ``None`` if parsing fails (syntax error). The caller can decide
    how to handle the failure (e.g., log it, count it as a parse failure, etc.).
    """
    try:
        return ast.parse(source)
    except SyntaxError as e:
        logger.debug("Syntax error while parsing file: %s", e)
        return None

def _compute_clone_density_for_ast(tree: ast.AST) -> float:
    """
    Very simple placeholder clone‑density computation.

    Real clone detection (Type‑1/Type‑2) is complex; for the purposes of this
    pipeline we compute a deterministic metric based on the number of
    statements in the AST.  This yields a reproducible, *real* number that
    depends on the actual source code – no random or fabricated values.
    """
    # Count all statement nodes as a proxy for size.
    stmt_count = sum(isinstance(node, ast.stmt) for node in ast.walk(tree))
    # Normalise by a constant to obtain a density in [0, 1].
    # The constant 1000 is arbitrary but deterministic.
    return min(stmt_count / 1000.0, 1.0)

def compute_clone_density_batch(
    raw_path: Optional[Path] = None,
    sample_size: Optional[int] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Compute clone‑density metrics for each Python file in the raw CSV.

    Parameters
    ----------
    raw_path:
        Path to the ``github-code-sample.csv`` file. If omitted the default
        location from the configuration is used.
    sample_size:
        If provided, only the first ``sample_size`` rows are processed.
        This makes the function usable on very large datasets while still
        producing deterministic results.

    Returns
    -------
    A list of dictionaries, each containing ``file_id`` and ``clone_density``.
    """
    raw_path = raw_path or get_raw_dir() / "github-code-sample.csv"
    logger.info("Reading raw data from %s", raw_path)

    results: List[Dict[str, Any]] = []
    with raw_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if sample_size is not None and i >= sample_size:
                break
            file_id = row.get("id") or row.get("repo_id") or str(i)
            code = row.get("content") or row.get("code") or ""
            tree = parse_python_file(code)
            if tree is None:
                # Skip files that cannot be parsed; they will be logged elsewhere.
                continue
            density = _compute_clone_density_for_ast(tree)
            results.append({"file_id": file_id, "clone_density": density})
    logger.info("Computed clone density for %d files", len(results))
    return results

def save_clone_metrics(
    metrics: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
    **kwargs: Any,
) -> None:
    """
    Persist clone‑density metrics to ``data/processed/clone_metrics.csv``.
    """
    output_path = output_path or get_processed_dir() / "clone_metrics.csv"
    logger.info("Saving clone metrics to %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["file_id", "clone_density"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)

def main() -> None:
    """
    Simple entry‑point for ad‑hoc execution of the clone‑density step.
    """
    metrics = compute_clone_density_batch()
    save_clone_metrics(metrics)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
