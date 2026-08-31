"""Generate a real family-based stratified split for 2D materials.

This module implements Task T013f: Generate Real Family-Based Split.
It consumes `data/processed/graphs_v1.parquet`, derives chemical prototypes
(family_id) using pymatgen StructureMatcher, and produces a stratified
train/test split ensuring no family appears in both sets (SC-002 compliance).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
import pandas as pd
from pymatgen.core.structure import Structure
from pymatgen.core.lattice import Lattice
from pymatgen.analysis.structure_matcher import StructureMatcher
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PARQUET = "data/processed/graphs_v1.parquet"
OUTPUT_SPLIT = "data/processed/split_indices.json"
RANDOM_STATE = 42
# StructureMatcher tolerances as per spec
LATTICE_TOL = 0.01
POSITION_TOL = 0.1
ANGLE_TOL = 5.0

def load_graphs_from_parquet(path: str) -> pd.DataFrame:
    """Load the graphs DataFrame from the specified parquet file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    logger.info(f"Loading graphs from {path}")
    df = pd.read_parquet(path)
    required_cols = ["structure_pickle", "cif_raw", "family_id"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    logger.info(f"Loaded {len(df)} graphs")
    return df

def derive_family_id(structure: Structure, matcher: StructureMatcher) -> str:
    """
    Derive a canonical family ID for a structure.
    In a real pipeline, we would cluster all structures.
    Here, we use the structure's formula and a hash of its reduced cell
    as a proxy for the 'family' if we cannot run full clustering in memory.
    However, the spec requires using StructureMatcher to group them.
    To do this correctly without loading all into memory at once (which might OOM),
    we implement a greedy clustering approach or use a hash of the reduced cell
    as a unique identifier for the prototype.

    Since StructureMatcher compares two structures, to assign a family_id to a
    single structure in a batch, we typically:
    1. Load all structures.
    2. Run a clustering algorithm (e.g., hierarchical or greedy) using StructureMatcher.
    3. Assign IDs.

    Given the constraints of a single script and potential memory limits,
    we will attempt to load all, compute a 'reduced cell signature' which is
    invariant to symmetry, and use that as the family_id.
    A more robust way with StructureMatcher requires pairwise comparison.
    Let's implement a greedy clustering:
    - Pick first structure as prototype 0.
    - For each subsequent structure, check if it matches any existing prototype.
    - If yes, assign that family ID. If no, create new prototype.

    To avoid O(N^2) comparisons if N is huge, we rely on the fact that
    StructureMatcher is expensive. We will limit this to a reasonable sample
    if the dataset is massive, but the task says "Consume graphs_v1.parquet".
    If the file is too large, we might need to stream.
    For now, we assume the file fits in memory for the clustering step
    (or we sample if it doesn't, but we must output a split for the data we have).

    Actually, a better approach for the 'family_id' column in the parquet
    (which this script expects to exist or create) is to compute it here.
    The task says "Derive family_id by using ... StructureMatcher".
    We will compute a 'reduced cell' fingerprint.
    """
    # Get the reduced cell to find a canonical representation
    # pymatgen's get_reduced_structure() is good but might not be unique enough.
    # StructureMatcher uses a reduced cell internally.
    # We will use the string representation of the reduced cell parameters
    # and composition as a key.
    try:
        reduced = structure.get_reduced_structure()
        # Create a hashable key
        key = (
            tuple(sorted(reduced.composition.elements)),
            reduced.lattice.abc,
            reduced.lattice.angles,
        )
        # Round to avoid float noise
        key = (
            key[0],
            tuple(round(x, 4) for x in key[1]),
            tuple(round(x, 4) for x in key[2]),
        )
        return str(key)
    except Exception:
        # Fallback to formula
        return structure.composition.reduced_formula

def assign_families(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign family_id to each row in the DataFrame.
    We reconstruct structures from pickle or CIF and compute a canonical family ID.
    """
    logger.info("Assigning family IDs based on structural prototypes...")
    matcher = StructureMatcher(
        ltol=LATTICE_TOL,
        stol=POSITION_TOL,
        angle_tol=ANGLE_TOL,
    )

    # We need to group structures that are equivalent.
    # A simple hash of reduced structure might not be 100% accurate for all
    # cases StructureMatcher handles, but it's efficient.
    # To strictly follow "StructureMatcher ... to group them", we should do clustering.
    # However, O(N^2) is risky.
    # Let's try a hybrid: use reduced structure hash as a fast pre-group,
    # then verify with StructureMatcher within groups if needed.
    # Or, simpler: just use the reduced structure signature as the family_id.
    # The spec says "Derive family_id by using ... StructureMatcher ... to group them".
    # This implies the grouping logic.
    # We will implement a greedy clustering if N is small (< 2000),
    # otherwise we fall back to the reduced structure hash which is the standard
    # proxy for 'prototype' in high-throughput (and what StructureMatcher uses internally).

    family_ids = []
    prototypes = []  # List of (Structure, family_id)

    # If the dataset is too large, we might need to sample or stream.
    # Assuming it fits for now.
    count = 0
    for idx, row in df.iterrows():
        count += 1
        if count % 100 == 0:
            logger.info(f"Processing {count}/{len(df)}")

        # Reconstruct structure
        structure = None
        try:
            if "structure_pickle" in row and pd.notna(row["structure_pickle"]):
                # Handle bytes or string
                raw = row["structure_pickle"]
                if isinstance(raw, str):
                    # If it was base64 encoded or similar, decode?
                    # Assuming raw bytes or pickled object
                    # If it's a string representation of bytes, we might need to handle it.
                    # Let's assume it's the raw bytes from pickle.dumps
                    structure = pickle.loads(raw)
                else:
                    structure = pickle.loads(raw)
            elif "cif_raw" in row and pd.notna(row["cif_raw"]):
                from pymatgen.io.cif import CifParser
                parser = CifParser.from_string(row["cif_raw"])
                structure = parser.get_structures()[0]
            else:
                logger.warning(f"Row {idx} has no structure data, skipping")
                family_ids.append("unknown")
                continue
        except Exception as e:
            logger.warning(f"Failed to parse structure at {idx}: {e}")
            family_ids.append("unknown")
            continue

        if structure is None:
            family_ids.append("unknown")
            continue

        # Try to match against existing prototypes
        found = False
        for proto_struct, fid in prototypes:
            if matcher.fit(structure, proto_struct):
                family_ids.append(fid)
                found = True
                break

        if not found:
            # New family
            new_fid = f"family_{len(prototypes)}"
            prototypes.append((structure, new_fid))
            family_ids.append(new_fid)

    df["family_id"] = family_ids
    logger.info(f"Assigned {len(prototypes)} unique families")
    return df

def generate_family_split(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[List[int], List[int]]:
    """
    Generate a stratified split based on family_id.
    Ensures that no family appears in both train and test.
    """
    logger.info("Generating family-based stratified split...")
    family_ids = df["family_id"].tolist()
    indices = list(range(len(df)))

    # We need to split indices such that the set of families in train
    # and test are disjoint.
    # sklearn's train_test_split with stratify=family_ids ensures
    # the *proportion* of families is preserved, but it DOES NOT
    # guarantee that a specific family is entirely in train or test.
    # To guarantee disjoint families, we must split on the *unique families*.

    unique_families = list(set(family_ids))
    # Remove 'unknown' if present to avoid splitting unknowns unpredictably
    if "unknown" in unique_families:
        unique_families.remove("unknown")
        # We can put 'unknown' in train or test, let's put in train
        unknown_indices = [i for i, f in enumerate(family_ids) if f == "unknown"]
    else:
        unknown_indices = []

    # Split the unique families
    train_families, test_families = train_test_split(
        unique_families,
        test_size=test_size,
        random_state=RANDOM_STATE,
        shuffle=True
    )

    train_indices = []
    test_indices = []

    for i, fid in enumerate(family_ids):
        if fid in train_families:
            train_indices.append(indices[i])
        elif fid in test_families:
            test_indices.append(indices[i])
        else:
            # 'unknown' or other
            train_indices.append(indices[i]) # Default to train

    logger.info(f"Train size: {len(train_indices)}, Test size: {len(test_indices)}")

    # Verify disjoint
    train_fam_set = set(family_ids[i] for i in train_indices)
    test_fam_set = set(family_ids[i] for i in test_indices)
    intersection = train_fam_set.intersection(test_fam_set)
    if intersection:
        logger.error(f"Family overlap detected: {intersection}")
        raise ValueError(f"SC-002 Violation: Families in both sets: {intersection}")

    return train_indices, test_indices

def verify_family_separation(train_indices: List[int], test_indices: List[int], df: pd.DataFrame) -> bool:
    """Verify that no family ID appears in both train and test."""
    train_fams = set(df.iloc[train_indices]["family_id"].tolist())
    test_fams = set(df.iloc[test_indices]["family_id"].tolist())
    overlap = train_fams.intersection(test_fams)
    if overlap:
        logger.error(f"Verification failed: Overlapping families: {overlap}")
        return False
    logger.info("Verification passed: No overlapping families.")
    return True

def save_split(train_indices: List[int], test_indices: List[int], output_path: str) -> None:
    """Atomically write the split to JSON."""
    split_data = {
        "train_indices": train_indices,
        "test_indices": test_indices,
        "random_state": RANDOM_STATE,
        "test_size": 0.2,
        "num_families_train": len(set(df.iloc[train_indices]["family_id"].tolist())),
        "num_families_test": len(set(df.iloc[test_indices]["family_id"].tolist())),
    }

    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    # Atomic write: mkstemp in same dir, then rename
    fd, temp_path = tempfile.mkstemp(suffix=".json", dir=output_dir)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(split_data, f, indent=2)
        os.rename(temp_path, output_path)
        logger.info(f"Split saved to {output_path}")
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def main():
    parser = argparse.ArgumentParser(description="Generate family-based split")
    parser.add_argument(
        "--input",
        type=str,
        default=INPUT_PARQUET,
        help="Path to input parquet file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_SPLIT,
        help="Path to output split JSON",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of families for test set",
    )
    args = parser.parse_args()

    try:
        df = load_graphs_from_parquet(args.input)
        df = assign_families(df)
        train_idx, test_idx = generate_family_split(df, test_size=args.test_size)
        verify_family_separation(train_idx, test_idx, df)
        save_split(train_idx, test_idx, args.output)
        logger.info("Task T013f completed successfully.")
    except Exception as e:
        logger.error(f"Task T013f failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()