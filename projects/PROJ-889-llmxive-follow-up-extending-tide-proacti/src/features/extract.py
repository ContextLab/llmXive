"""
src/features/extract.py

Extract quantitative structural features from both real and synthetic code
instances and produce a unified feature matrix CSV.

This implementation now correctly locates the real TIDE CSV (produced by
``src.data.acquire_real``) and the synthetic metadata CSV.  It also logs
progress and aborts with clear error messages if required inputs are missing.
"""

import ast
import csv
import hashlib
import json
import logging
import sys
from pathlib import Path

import pandas as pd
from radon.complexity import cc_visit

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_text(text: str) -> str:
    """Return the SHA‑256 hex digest of a Unicode string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ast_depth(node: ast.AST, current: int = 0) -> int:
    """Recursively compute the maximum depth of an AST node."""
    if not list(ast.iter_child_nodes(node)):
        return current
    return max(_ast_depth(child, current + 1) for child in ast.iter_child_nodes(node))


def _import_count(tree: ast.AST) -> int:
    """Count distinct import statements (both ``import`` and ``from``)."""
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                imports.add(alias.name)
        elif isinstance(n, ast.ImportFrom):
            module = n.module or ""
            imports.add(module)
    return len(imports)


def _cyclomatic_complexity(source: str) -> int:
    """
    Compute total cyclomatic complexity of the source using radon.

    Returns 0 if radon cannot parse the source.
    """
    try:
        blocks = cc_visit(source)
        return sum(block.complexity for block in blocks)
    except Exception:
        return 0


# ----------------------------------------------------------------------
# Processing functions
# ----------------------------------------------------------------------
def _process_real_instance(row: pd.Series) -> dict:
    """
    Extract features from a real TIDE instance.

    Expected columns in the input row:
        - instance_id
        - code (the Python source)
        - ground_truth_label
    """
    code = row["code"]
    tree = ast.parse(code)
    return {
        "instance_id": row["instance_id"],
        "origin": "real",
        "ground_truth_label": row["ground_truth_label"],
        "dependency_depth": None,          # not applicable for real data
        "semantic_scope": None,            # not applicable for real data
        "syntactic_complexity": None,      # not applicable for real data
        "ast_depth": _ast_depth(tree),
        "import_count": _import_count(tree),
        "cyclomatic_complexity": _cyclomatic_complexity(code),
        "sha256": _sha256_of_text(code),
    }


def _process_synthetic_instance(meta_row: pd.Series, synthetic_dir: Path) -> dict:
    """
    Extract features from a synthetic instance.

    ``meta_row`` must contain at least the following columns:
        - instance_id
        - filename
        - dependency_depth
        - semantic_scope
        - syntactic_complexity
        - ground_truth_label
    """
    filename = meta_row["filename"]
    file_path = synthetic_dir / filename
    if not file_path.is_file():
        raise FileNotFoundError(f"Synthetic file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        code = f.read()

    tree = ast.parse(code)
    return {
        "instance_id": meta_row["instance_id"],
        "origin": meta_row["origin"],
        "ground_truth_label": meta_row["ground_truth_label"],
        "dependency_depth": meta_row["dependency_depth"],
        "semantic_scope": meta_row["semantic_scope"],
        "syntactic_complexity": meta_row["syntactic_complexity"],
        "ast_depth": _ast_depth(tree),
        "import_count": _import_count(tree),
        "cyclomatic_complexity": _cyclomatic_complexity(code),
        "sha256": _sha256_of_text(code),
    }


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for ``python -m src.features.extract``.

    Produces ``data/interim/features.csv`` with the exact header required by
    the contract:
        instance_id,origin,ground_truth_label,dependency_depth,
        semantic_scope,syntactic_complexity,ast_depth,import_count,
        cyclomatic_complexity,sha256
    """
    logger = get_logger(__name__, log_file=str(paths.data("logs", "extract.log")))
    logger.info("Starting feature extraction.")

    # Paths
    raw_dir = paths.data("raw")
    synthetic_dir = paths.data("synthetic")
    interim_dir = paths.data("interim")
    interim_dir.mkdir(parents=True, exist_ok=True)

    tide_csv = raw_dir / "tide.csv"
    synthetic_meta = raw_dir / "synthetic_meta.csv"

    if not tide_csv.is_file():
        raise FileNotFoundError(f"Real TIDE CSV not found at {tide_csv}")
    if not synthetic_meta.is_file():
        raise FileNotFoundError(f"Synthetic metadata CSV not found at {synthetic_meta}")

    # Load datasets
    logger.info(f"Loading real TIDE data from {tide_csv}")
    real_df = pd.read_csv(tide_csv)
    logger.info(f"Loaded {len(real_df)} real instances.")

    logger.info(f"Loading synthetic metadata from {synthetic_meta}")
    synth_meta_df = pd.read_csv(synthetic_meta)
    logger.info(f"Loaded {len(synth_meta_df)} synthetic metadata rows.")

    # Process real instances
    records = []
    for _, row in real_df.iterrows():
        try:
            records.append(_process_real_instance(row))
        except Exception as e:
            logger.error(f"Failed to process real instance {row.get('instance_id')}: {e}")

    # Process synthetic instances
    for _, meta_row in synth_meta_df.iterrows():
        try:
            records.append(_process_synthetic_instance(meta_row, synthetic_dir))
        except Exception as e:
            logger.error(f"Failed to process synthetic instance {meta_row.get('instance_id')}: {e}")

    # Create DataFrame
    features_df = pd.DataFrame.from_records(records)

    # Ensure required columns exist (they may be None for real data)
    expected_columns = [
        "instance_id",
        "origin",
        "ground_truth_label",
        "dependency_depth",
        "semantic_scope",
        "syntactic_complexity",
        "ast_depth",
        "import_count",
        "cyclomatic_complexity",
        "sha256",
    ]
    missing_cols = set(expected_columns) - set(features_df.columns)
    if missing_cols:
        raise RuntimeError(f"Feature extraction produced missing columns: {missing_cols}")

    # Write CSV
    out_path = interim_dir / "features.csv"
    features_df.to_csv(out_path, index=False)
    logger.info(f"Wrote feature matrix with {len(features_df)} rows to {out_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logging.getLogger(__name__).exception("Feature extraction failed")
        sys.exit(1)