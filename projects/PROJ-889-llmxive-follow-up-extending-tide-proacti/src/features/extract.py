"""
Feature extraction script for the TIDE follow‑up study.

This script walks through all code instances (real and synthetic),
parses each Python file, computes structural metrics and merges them
with intrinsic properties and ground‑truth labels.  The resulting
feature matrix is written to ``data/interim/features.csv`` with the
exact header required by the contract.

The script is deliberately self‑contained and raises on any missing
input data so that failures are loud and reproducible.
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

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_text(text: str) -> str:
    """Return the hexadecimal SHA‑256 digest of *text*."""
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
            module = n.module if n.module else ""
            for alias in n.names:
                imports.add(f"{module}.{alias.name}" if module else alias.name)
    return len(imports)

def _cyclomatic_complexity(source: str) -> int:
    """
    Compute the total cyclomatic complexity of *source* using radon.
    The function sums the CC of all top‑level blocks (functions,
    methods, classes).  If radon cannot parse the source it returns 0.
    """
    try:
        blocks = cc_visit(source)
        return sum(b.complexity for b in blocks)
    except Exception as exc:  # pragma: no cover – defensive
        log.warning("Radon failed on source (%s): %s", source[:30], exc)
        return 0

# ----------------------------------------------------------------------
# Core extraction logic
# ----------------------------------------------------------------------
def _process_real_instance(row: pd.Series) -> dict:
    """
    Extract features from a real TIDE instance.

    Expected columns in ``tide.csv``:
        - instance_id
        - code (the Python source)
        - ground_truth_label
    """
    source = row["code"]
    instance_id = str(row["instance_id"])
    ground_truth = int(row["ground_truth_label"])

    # Parse AST – any syntax error will raise and abort loudly.
    tree = ast.parse(source)

    return {
        "instance_id": instance_id,
        "origin": "real",
        "ground_truth_label": ground_truth,
        # Intrinsic properties are not defined for real data;
        # we use the neutral defaults required by the schema.
        "dependency_depth": 0,
        "semantic_scope": "local",
        "syntactic_complexity": 0,
        "ast_depth": _ast_depth(tree),
        "import_count": _import_count(tree),
        "cyclomatic_complexity": _cyclomatic_complexity(source),
        "sha256": _sha256_of_text(source),
    }

def _process_synthetic_instance(meta_row: pd.Series, synthetic_dir: Path) -> dict:
    """
    Extract features from a synthetic instance.

    ``meta_row`` is a row from ``synthetic_meta.csv`` containing at
    least the following columns:
        - instance_id
        - filename
        - dependency_depth
        - semantic_scope
        - syntactic_complexity
        - ground_truth_label
    """
    instance_id = str(meta_row["instance_id"])
    filename = meta_row["filename"]
    source_path = synthetic_dir / filename
    if not source_path.is_file():
        raise FileNotFoundError(f"Synthetic source file not found: {source_path}")

    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    return {
        "instance_id": instance_id,
        "origin": "synthetic",
        "ground_truth_label": int(meta_row["ground_truth_label"]),
        "dependency_depth": int(meta_row["dependency_depth"]),
        "semantic_scope": meta_row["semantic_scope"],
        "syntactic_complexity": int(meta_row["syntactic_complexity"]),
        "ast_depth": _ast_depth(tree),
        "import_count": _import_count(tree),
        "cyclomatic_complexity": _cyclomatic_complexity(source),
        "sha256": _sha256_of_text(source),
    }

def main() -> None:
    """
    Entry point for ``python -m src.features.extract``.

    The function performs the following steps:

    1. Load the real TIDE CSV (``data/raw/tide.csv``).  The CSV must
       contain ``instance_id``, ``code`` and ``ground_truth_label``.
    2. Load the synthetic metadata CSV
       (``data/raw/synthetic_meta.csv``) and locate the corresponding
       ``.py`` files under ``data/synthetic``.
    3. Extract the structural features for every instance.
    4. Write the unified feature matrix to
       ``data/interim/features.csv`` with the exact header required by
       the contract.
    """
    # ------------------------------------------------------------------
    # Locate input files
    # ------------------------------------------------------------------
    tide_csv = paths.data("raw", "tide.csv")
    synthetic_meta_csv = paths.data("raw", "synthetic_meta.csv")
    synthetic_dir = paths.data("synthetic")

    if not tide_csv.is_file():
        raise FileNotFoundError(f"Real TIDE CSV not found at {tide_csv}")
    if not synthetic_meta_csv.is_file():
        raise FileNotFoundError(
            f"Synthetic metadata CSV not found at {synthetic_meta_csv}"
        )
    if not synthetic_dir.is_dir():
        raise FileNotFoundError(f"Synthetic source directory missing: {synthetic_dir}")

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    log.info("Loading real TIDE instances from %s", tide_csv)
    tide_df = pd.read_csv(tide_csv, dtype=str)  # keep everything as string initially
    required_real_cols = {"instance_id", "code", "ground_truth_label"}
    if not required_real_cols.issubset(tide_df.columns):
        missing = required_real_cols - set(tide_df.columns)
        raise RuntimeError(f"tide.csv is missing required columns: {missing}")

    log.info("Loading synthetic metadata from %s", synthetic_meta_csv)
    synth_meta_df = pd.read_csv(synthetic_meta_csv, dtype=str)
    required_meta_cols = {
        "instance_id",
        "filename",
        "dependency_depth",
        "semantic_scope",
        "syntactic_complexity",
        "ground_truth_label",
    }
    if not required_meta_cols.issubset(synth_meta_df.columns):
        missing = required_meta_cols - set(synth_meta_df.columns)
        raise RuntimeError(
            f"synthetic_meta.csv is missing required columns: {missing}"
        )

    # ------------------------------------------------------------------
    # Process records
    # ------------------------------------------------------------------
    records = []

    log.info("Processing real instances (%d rows)", len(tide_df))
    for _, row in tide_df.iterrows():
        records.append(_process_real_instance(row))

    log.info(
        "Processing synthetic instances (%d rows)", len(synth_meta_df)
    )
    for _, meta_row in synth_meta_df.iterrows():
        records.append(_process_synthetic_instance(meta_row, synthetic_dir))

    # ------------------------------------------------------------------
    # Write output CSV
    # ------------------------------------------------------------------
    out_path = paths.data("interim", "features.csv")
    header = [
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

    log.info("Writing %d feature rows to %s", len(records), out_path)
    with out_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=header)
        writer.writeheader()
        for rec in records:
            # Ensure ordering matches header and all required keys exist
            writer.writerow({k: rec[k] for k in header})

    log.info("Feature extraction completed successfully.")

if __name__ == "__main__":
    sys.exit(main())
