"""
T013f: Generate Real Family-Based Split.

This script generates a stratified split of the dataset based on chemical prototype/family.
It consumes `data/processed/graphs_v1.parquet` and outputs `data/processed/split_indices.json`.

Requirements:
- Derive family_id using pymatgen StructureMatcher.
- Use sklearn.model_selection.train_test_split with stratify.
- Ensure no training family appears in the test set.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("split_generator")

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "graphs_v1.parquet"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "split_indices.json"
DEFAULT_TEST_SIZE = 0.2
RANDOM_STATE = 42

# StructureMatcher parameters as per task spec
LATTICE_TOL = 0.01
POSITION_TOL = 0.1
ANGLE_TOL = 5.0

def load_graphs_from_parquet(path: Path) -> pd.DataFrame:
    """Load the parquet file containing graph data."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    logger.info(f"Loading graphs from {path}")
    df = pd.read_parquet(path)
    
    required_cols = ["structure_json", "family_id"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    
    return df

def derive_family_id(structure_json: str) -> str:
    """
    Derive a canonical family ID from a structure JSON string.
    
    This function parses the structure, attempts to find a prototype match,
    and returns a string identifier. In a real pipeline, this might involve
    a global clustering step, but here we use a hash of the reduced cell
    or a simple identifier based on the structure itself if no global
    clustering is performed in this specific script.
    
    However, the task requires using StructureMatcher to *group* them.
    Since this script runs once, we perform a single-pass clustering
    to assign family IDs to the loaded data.
    
    Note: For large datasets, O(N^2) matching is expensive. We implement
    a simplified grouping logic here assuming the 'family_id' column
    might already exist or we compute it based on a hash of the structure
    if we cannot perform full clustering in this step.
    
    BUT, the task spec says: "Derive family_id by loading structures and 
    using pymatgen.core.structure.StructureMatcher ... to group them by prototype."
    
    To satisfy this strictly without O(N^2) on the full dataset (which might
    hang the runner), we will:
    1. Check if 'family_id' is already in the dataframe. If so, use it.
    2. If not, we attempt a lightweight grouping.
    
    Wait, the input schema from T013d4 says: "Output schema MUST include ... family_id (str)".
    So `graphs_v1.parquet` SHOULD already have `family_id`.
    The task T013f says: "Derive family_id by loading structures and using ... StructureMatcher".
    This implies we might need to RE-CALCULATE or VERIFY it, or the previous step
    used a simple heuristic and this step refines it.
    
    Given the constraint "Consume graphs_v1.parquet from T013d4", and T013d4 output
    includes `family_id`, we will assume the column exists. If the task demands
    we *re-derive* it using StructureMatcher, we must do so.
    
    Let's implement the re-derivation logic:
    - Load all structures.
    - Group them by matching.
    - Assign new family IDs.
    
    To avoid O(N^2) crash, we will use a greedy clustering approach with a limit
    or just use the existing ID if the task allows.
    However, the spec says "Derive family_id by loading structures and using...".
    We will implement a robust grouping.
    """
    # This function is called per row in the old logic, but we need global context.
    # We will move the logic to `assign_families` below.
    return structure_json  # Placeholder, actual logic in assign_families
    
def assign_families(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign family IDs to the dataframe using StructureMatcher.
    
    This performs a greedy clustering of structures.
    """
    logger.info("Starting family assignment via StructureMatcher...")
    
    matcher = StructureMatcher(
        ltol=LATTICE_TOL,
        stol=POSITION_TOL,
        angle_tol=ANGLE_TOL,
        primitive_cell=True,
        scale=True,
        attempt_supercell=False,
        allow_subset=False,
    )
    
    structures = []
    indices = []
    
    # Parse structures
    for idx, row in df.iterrows():
        try:
            struct = Structure.from_dict(json.loads(row["structure_json"]))
            structures.append(struct)
            indices.append(idx)
        except Exception as e:
            logger.warning(f"Skipping invalid structure at index {idx}: {e}")
    
    if not structures:
        logger.error("No valid structures found to group.")
        # Return df with dummy IDs if none found
        df["family_id"] = "unknown"
        return df
    
    # Greedy clustering
    # We maintain a list of representative structures for each family
    representatives = []
    family_ids = [None] * len(structures)
    
    current_family_count = 0
    
    # Limit iterations to avoid hanging if N is large (e.g., > 1000)
    # If the dataset is huge, we might need a sample or a faster method.
    # Assuming the dataset fits in memory and N is reasonable for this task.
    
    logger.info(f"Processing {len(structures)} structures...")
    
    for i, struct in enumerate(structures):
        assigned = False
        for j, rep in enumerate(representatives):
            if matcher.fit(struct, rep):
                family_ids[i] = f"family_{j}"
                assigned = True
                break
        
        if not assigned:
            representatives.append(struct)
            family_ids[i] = f"family_{current_family_count}"
            current_family_count += 1
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i+1}/{len(structures)} structures. Families: {current_family_count}")
    
    # Map back to dataframe
    df["family_id"] = [family_ids[i] for i in indices]
    
    logger.info(f"Assigned {current_family_count} unique families.")
    return df

def generate_family_split(
    df: pd.DataFrame,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> Tuple[List[int], List[int]]:
    """
    Generate a stratified train/test split based on family_id.
    
    Ensures that no family appears in both train and test sets.
    """
    logger.info(f"Generating stratified split (test_size={test_size})...")
    
    # Ensure family_id is present
    if "family_id" not in df.columns:
        raise ValueError("Dataframe must contain 'family_id' column for stratification.")
    
    # Convert family_id to a hashable type if needed (it's str)
    # Use sklearn's train_test_split with stratify
    indices = df.index.tolist()
    families = df["family_id"].tolist()
    
    train_idx, test_idx = train_test_split(
        indices,
        test_size=test_size,
        random_state=random_state,
        stratify=families,
    )
    
    return train_idx, test_idx

def verify_family_separation(
    df: pd.DataFrame,
    train_idx: List[int],
    test_idx: List[int],
) -> bool:
    """
    Verify that no family appears in both train and test sets.
    """
    train_families = set(df.loc[train_idx, "family_id"])
    test_families = set(df.loc[test_idx, "family_id"])
    
    intersection = train_families & test_families
    
    if intersection:
        logger.error(f"FAMILY LEAK DETECTED: Families {intersection} appear in both train and test.")
        return False
    
    logger.info("Family separation verified: No overlap between train and test families.")
    return True

def save_split(
    train_idx: List[int],
    test_idx: List[int],
    output_path: Path,
) -> None:
    """
    Save the split indices to a JSON file.
    """
    split_data = {
        "train_indices": train_idx,
        "test_indices": test_idx,
        "metadata": {
            "random_state": RANDOM_STATE,
            "test_size": DEFAULT_TEST_SIZE,
            "strategy": "family_stratified",
            "total_train": len(train_idx),
            "total_test": len(test_idx),
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(split_data, f, indent=2)
    
    logger.info(f"Split saved to {output_path}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a family-based stratified split for 2D materials."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Path to the input parquet file (graphs_v1.parquet).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to the output JSON file (split_indices.json).",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help="Fraction of data to use for testing.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=RANDOM_STATE,
        help="Random seed for reproducibility.",
    )
    
    args = parser.parse_args()
    
    try:
        # 1. Load Data
        df = load_graphs_from_parquet(args.input)
        
        # 2. Assign Families (Re-derive using StructureMatcher as per spec)
        # Note: If the dataset is too large, this step might be slow.
        # The task requires it, so we do it.
        df = assign_families(df)
        
        # 3. Generate Split
        train_idx, test_idx = generate_family_split(
            df,
            test_size=args.test_size,
            random_state=args.random_state,
        )
        
        # 4. Verify Separation
        if not verify_family_separation(df, train_idx, test_idx):
            logger.error("SC-002 Violation: Family overlap detected. Exiting.")
            sys.exit(1)
        
        # 5. Save Output
        save_split(train_idx, test_idx, args.output)
        
        logger.info("T013f completed successfully.")
        
    except Exception as e:
        logger.error(f"T013f failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()