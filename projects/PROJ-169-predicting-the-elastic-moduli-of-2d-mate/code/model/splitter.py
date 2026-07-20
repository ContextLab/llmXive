import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SplitManifest:
    train: List[Dict[str, Any]]
    val: List[Dict[str, Any]]
    test: List[Dict[str, Any]]

def load_graphs_from_parquet(parquet_path: Path) -> pd.DataFrame:
    """Load graphs from parquet file."""
    if not parquet_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {parquet_path}")
    
    try:
        df = pd.read_parquet(parquet_path)
        logger.info(f"Loaded {len(df)} graphs from {parquet_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to read parquet file: {e}")
        raise

def load_split_indices(split_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load existing split indices from JSON."""
    if not split_path.exists():
        logger.warning(f"Split indices file not found: {split_path}. Starting fresh.")
        return {"train": [], "val": [], "test": []}
    
    try:
        with open(split_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded existing split indices from {split_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load split indices: {e}")
        raise

def split_by_family(
    df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42
) -> SplitManifest:
    """
    Split the dataframe by family_id to ensure no family overlap between train/val/test.
    
    Args:
        df: DataFrame with 'material_id' and 'family_id' columns.
        test_size: Fraction of families for test set.
        val_size: Fraction of families for validation set.
        random_state: Random seed for reproducibility.
        
    Returns:
        SplitManifest containing lists of material entries for train, val, test.
    """
    required_cols = ['family_id', 'material_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"DataFrame missing required columns: {missing_cols}")

    # Get unique families
    families = df['family_id'].unique()
    if len(families) == 0:
        raise ValueError("No families found in data.")
    
    # Use numpy for reproducible shuffling
    rng = np.random.RandomState(random_state)
    shuffled_families = families.copy()
    rng.shuffle(shuffled_families)
    
    n_families = len(shuffled_families)
    n_test = max(1, int(n_families * test_size))
    n_val = max(1, int(n_families * val_size))
    
    # Ensure we don't exceed total
    if n_test + n_val >= n_families:
        n_val = max(1, n_families - n_test - 1)
    
    test_families = set(shuffled_families[:n_test])
    val_families = set(shuffled_families[n_test:n_test + n_val])
    train_families = set(shuffled_families[n_test + n_val:])
    
    logger.info(f"Assigned {len(test_families)} families to test, {len(val_families)} to val, {len(train_families)} to train")

    # Assign materials to splits
    train_list = []
    val_list = []
    test_list = []
    
    for _, row in df.iterrows():
        fid = row['family_id']
        mid = row['material_id']
        entry = {"id": str(mid), "family_id": str(fid)}
        
        if fid in test_families:
            test_list.append(entry)
        elif fid in val_families:
            val_list.append(entry)
        else:
            train_list.append(entry)
    
    # Final verification: ensure no family appears in multiple sets
    train_ids = {item['family_id'] for item in train_list}
    val_ids = {item['family_id'] for item in val_list}
    test_ids = {item['family_id'] for item in test_list}
    
    overlap_train_val = train_ids & val_ids
    overlap_train_test = train_ids & test_ids
    overlap_val_test = val_ids & test_ids
    
    if overlap_train_val or overlap_train_test or overlap_val_test:
        logger.error("SC-002 Violation: Family overlap detected in split.")
        if overlap_train_val:
            logger.error(f"Overlap train/val: {overlap_train_val}")
        if overlap_train_test:
            logger.error(f"Overlap train/test: {overlap_train_test}")
        if overlap_val_test:
            logger.error(f"Overlap val/test: {overlap_val_test}")
        logger.error("Exiting with code 1 as per SC-002 requirement.")
        sys.exit(1)
        
    logger.info(f"Split complete: Train={len(train_list)}, Val={len(val_list)}, Test={len(test_list)}")
    logger.info(f"Families: Train={len(train_ids)}, Val={len(val_ids)}, Test={len(test_ids)}")
    
    return SplitManifest(train=train_list, val=val_list, test=test_list)

def save_split_manifest(manifest: SplitManifest, output_path: Path) -> None:
    """Save the split manifest to a JSON file.
    
    Output schema is a list of objects [{"id": "...", "family_id": "..."}, ...]
    as required by T017, but wrapped in keys for train/val/test for clarity.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format as a dict with keys 'train', 'val', 'test'
    data = {
        "train": manifest.train,
        "val": manifest.val,
        "test": manifest.test
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved split manifest to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Split data by family")
    parser.add_argument("--input", type=Path, required=True, help="Input parquet file (graphs_v1.parquet)")
    parser.add_argument("--existing-split", type=Path, default=None, help="Optional existing split_indices.json to consume/overwrite")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON file (split_indices.json)")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set fraction")
    parser.add_argument("--val-size", type=float, default=0.1, help="Validation set fraction")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    try:
        # Load the primary data source
        df = load_graphs_from_parquet(args.input)
        
        # Optionally load existing split (for validation/logging, though we regenerate)
        if args.existing_split:
            existing_split = load_split_indices(args.existing_split)
            logger.info(f"Consumed existing split from {args.existing_split} (will be overwritten)")
        
        # Perform the stratified split by family
        manifest = split_by_family(df, test_size=args.test_size, val_size=args.val_size, random_state=args.seed)
        
        # Save the new split, overwriting any existing file at the output path
        save_split_manifest(manifest, args.output)
        
        logger.info(f"Successfully generated stratified split satisfying SC-002 (inter-family generalization).")
        
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Splitting failed")
        sys.exit(1)

if __name__ == "__main__":
    main()