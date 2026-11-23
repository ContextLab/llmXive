"""
code/modeling/split.py

Implements scaffold-based stratified splitting for USPTO reaction data.
Handles exclusion of cross-class scaffolds and generation of disjoint
Train, Validation, Test, and SC-003 Held-Out Validation sets.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def load_stratified_groups(path: Path) -> pd.DataFrame:
    """
    Load the stratified groups file generated in T022b.
    Columns: group_id, split, reaction_class, scaffold_id
    """
    if not path.exists():
        raise FileNotFoundError(f"Stratified groups file not found: {path}")
    logger.info(f"Loading stratified groups from {path}")
    df = pd.read_csv(path)
    return df

def load_excluded_scaffolds(path: Path) -> List[str]:
    """
    Load the list of excluded cross-class scaffolds.
    """
    if not path.exists():
        raise FileNotFoundError(f"Excluded scaffolds file not found: {path}")
    logger.info(f"Loading excluded scaffolds from {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('excluded_scaffold_ids', [])

def validate_split_consistency(
    train_ids: pd.Series,
    val_ids: pd.Series,
    test_ids: pd.Series,
    sc003_ids: pd.Series,
    scaffold_groups: pd.DataFrame
) -> bool:
    """
    Verify that no scaffold_id appears in multiple splits.
    """
    splits = {
        'train': train_ids,
        'validation': val_ids,
        'test': test_ids,
        'sc003': sc003_ids
    }

    # Map group_id to scaffold_id
    group_to_scaffold = scaffold_groups.set_index('group_id')['scaffold_id']

    scaffold_sets = {}
    for name, ids in splits.items():
        scaffolds = set(group_to_scaffold.loc[ids].unique())
        scaffold_sets[name] = scaffolds

    # Check for intersections
    all_keys = list(scaffold_sets.keys())
    for i in range(len(all_keys)):
        for j in range(i + 1, len(all_keys)):
            k1, k2 = all_keys[i], all_keys[j]
            intersection = scaffold_sets[k1].intersection(scaffold_sets[k2])
            if intersection:
                logger.error(f"Overlap detected between {k1} and {k2}: {len(intersection)} scaffolds")
                return False

    logger.info("Split consistency validation passed: No scaffold overlap detected.")
    return True

def create_train_val_test_split(
    groups_df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Assign groups to Train, Val, and Test based on stratified ratios.
    This is a helper for T022c/d.
    """
    # This function is primarily for reference; T022c/d logic is assumed to have run.
    # We assume the splits are already computed and stored as indices.
    # This is a placeholder to satisfy the API surface if called, but T022e
    # relies on the output files of T022c/d.
    raise NotImplementedError("Splits are expected to be pre-computed by T022c/d.")

def save_splits(
    indices: pd.Series,
    output_path: Path,
    split_name: str
) -> None:
    """
    Save a set of indices to a CSV file.
    """
    indices.to_csv(output_path, index=False, header=['group_id'])
    logger.info(f"Saved {split_name} indices to {output_path} ({len(indices)} groups)")

def run_split_pipeline() -> None:
    """
    Main execution for T022e: Generate SC-003 Held-Out Validation Set.

    Steps:
    1. Load cleaned_reactions.parquet and scaffold_groups.parquet.
    2. Load excluded scaffolds (cross-class).
    3. Load Train, Val, Test indices.
    4. Compute the set of remaining groups.
    5. Sample a subset for SC-003 validation.
    6. Verify disjointness and save output.
    """
    logger.info("Starting T022e: SC-003 Held-Out Validation Set Generation")

    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_processed = project_root / "data" / "processed"
    data_results = project_root / "data" / "results"

    cleaned_reactions_path = data_processed / "cleaned_reactions.parquet"
    scaffold_groups_path = data_processed / "scaffold_groups.parquet"
    excluded_scaffolds_path = data_processed / "excluded_scaffolds.json"

    train_indices_path = data_processed / "train_indices.csv"
    val_indices_path = data_processed / "validation_indices.csv"
    test_indices_path = data_processed / "held_out_test_indices.csv"

    sc003_output_path = data_processed / "sc003_val_indices.csv"

    # 1. Load Data
    logger.info("Loading cleaned reactions and scaffold groups...")
    if not cleaned_reactions_path.exists():
        raise FileNotFoundError(f"Missing cleaned reactions: {cleaned_reactions_path}")
    if not scaffold_groups_path.exists():
        raise FileNotFoundError(f"Missing scaffold groups: {scaffold_groups_path}")

    # We need the mapping from reaction_id to scaffold_id.
    # scaffold_groups.parquet should have: scaffold_id, group_id, and potentially reaction_ids or a way to join.
    # Assuming scaffold_groups.parquet has 'scaffold_id' and 'group_id'.
    # cleaned_reactions.parquet has 'scaffold_id' (generated in T010) or we join on it.
    # T010 output: scaffold_groups.parquet with column 'scaffold_id'.
    # T017 output: cleaned_reactions.parquet.
    # We need to ensure cleaned_reactions has 'scaffold_id'.
    # If not, we must re-join or assume it was added in T017/T010 pipeline.
    # Based on T010 description: "Output scaffold_groups.parquet with column scaffold_id".
    # T017 description: "Output cleaned_reactions.parquet".
    # We assume T017/T010 pipeline added 'scaffold_id' to cleaned_reactions.

    reactions_df = pd.read_parquet(cleaned_reactions_path)
    scaffold_groups_df = pd.read_parquet(scaffold_groups_path)

    if 'scaffold_id' not in reactions_df.columns:
        raise ValueError("cleaned_reactions.parquet must contain 'scaffold_id' column.")

    # 2. Load Excluded Scaffolds
    logger.info("Loading excluded cross-class scaffolds...")
    excluded_scaffolds = load_excluded_scaffolds(excluded_scaffolds_path)
    logger.info(f"Excluded {len(excluded_scaffolds)} cross-class scaffolds.")

    # 3. Load Existing Splits
    logger.info("Loading Train, Val, Test indices...")
    if not train_indices_path.exists():
        raise FileNotFoundError(f"Missing train indices: {train_indices_path}")
    if not val_indices_path.exists():
        raise FileNotFoundError(f"Missing validation indices: {val_indices_path}")
    if not test_indices_path.exists():
        raise FileNotFoundError(f"Missing test indices: {test_indices_path}")

    train_ids = pd.read_csv(train_indices_path)['group_id'].tolist()
    val_ids = pd.read_csv(val_indices_path)['group_id'].tolist()
    test_ids = pd.read_csv(test_indices_path)['group_id'].tolist()

    # 4. Determine Remaining Groups
    # We need the mapping from group_id to scaffold_id to filter properly.
    # scaffold_groups_df should have 'group_id' and 'scaffold_id'.
    if 'group_id' not in scaffold_groups_df.columns:
        # Fallback: if group_id is the index
        scaffold_groups_df = scaffold_groups_df.reset_index()

    group_to_scaffold = scaffold_groups_df.set_index('group_id')['scaffold_id']

    all_group_ids = group_to_scaffold.index.tolist()
    used_group_ids = set(train_ids + val_ids + test_ids)
    remaining_group_ids = [g for g in all_group_ids if g not in used_group_ids]

    logger.info(f"Found {len(remaining_group_ids)} remaining groups after Train/Val/Test assignment.")

    # Filter remaining groups to exclude any that might have slipped through (should not happen if T022a was correct)
    # Also ensure no remaining group belongs to an excluded scaffold (redundant check)
    valid_remaining_ids = []
    for gid in remaining_group_ids:
        scaff = group_to_scaffold[gid]
        if scaff not in excluded_scaffolds:
            valid_remaining_ids.append(gid)
        else:
            logger.warning(f"Group {gid} belongs to excluded scaffold {scaff}, skipping.")

    logger.info(f"Filtered {len(valid_remaining_ids)} valid remaining groups for SC-003.")

    if not valid_remaining_ids:
        logger.warning("No valid groups remaining for SC-003 set. Creating empty file.")
        pd.DataFrame({'group_id': []}).to_csv(sc003_output_path, index=False)
        return

    # 5. Sample SC-003 Set
    # Strategy: Take a fixed percentage or fixed number from the remaining disjoint groups.
    # Let's aim for ~10% of the remaining, or at least 50 groups if available.
    sample_size = min(500, max(50, int(len(valid_remaining_ids) * 0.10)))
    np.random.shuffle(valid_remaining_ids)
    sc003_ids = valid_remaining_ids[:sample_size]

    logger.info(f"Selected {len(sc003_ids)} groups for SC-003 validation set.")

    # 6. Verify Disjointness
    sc003_set = set(sc003_ids)
    if sc003_set.intersection(set(train_ids)):
        raise RuntimeError("SC-003 set overlaps with Train!")
    if sc003_set.intersection(set(val_ids)):
        raise RuntimeError("SC-003 set overlaps with Validation!")
    if sc003_set.intersection(set(test_ids)):
        raise RuntimeError("SC-003 set overlaps with Test!")

    logger.info("Disjointness verification passed.")

    # 7. Save Output
    save_splits(pd.Series(sc003_ids), sc003_output_path, "SC-003 Validation")

    # Log Summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_groups": len(all_group_ids),
        "excluded_scaffolds_count": len(excluded_scaffolds),
        "train_count": len(train_ids),
        "val_count": len(val_ids),
        "test_count": len(test_ids),
        "remaining_count": len(valid_remaining_ids),
        "sc003_count": len(sc003_ids),
        "sc003_output_path": str(sc003_output_path)
    }

    log_path = data_results / "sc003_split_log.json"
    with open(log_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved SC-003 split log to {log_path}")

def main():
    """
    Entry point for the split pipeline (specifically T022e).
    """
    try:
        run_split_pipeline()
        logger.info("T022e completed successfully.")
    except Exception as e:
        logger.error(f"T022e failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()