import os
import json
import logging
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
    return pd.read_parquet(parquet_path)

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
    if 'family_id' not in df.columns or 'material_id' not in df.columns:
        raise ValueError("DataFrame must contain 'family_id' and 'material_id' columns")

    # Get unique families
    families = df['family_id'].unique()
    np.random.seed(random_state)
    np.random.shuffle(families)
    
    n_families = len(families)
    n_test = int(n_families * test_size)
    n_val = int(n_families * val_size)
    
    test_families = set(families[:n_test])
    val_families = set(families[n_test:n_test + n_val])
    train_families = set(families[n_test + n_val:])
    
    # Verify no overlap (sanity check)
    if test_families & val_families or test_families & train_families or val_families & train_families:
        raise RuntimeError("Family overlap detected in split logic.")

    # Assign materials to splits
    train_list = []
    val_list = []
    test_list = []
    
    for _, row in df.iterrows():
        fid = row['family_id']
        entry = {"id": row['material_id'], "family_id": fid}
        
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
    
    if train_ids & val_ids or train_ids & test_ids or val_ids & test_ids:
        logger.error("SC-002 Violation: Family overlap detected in split.")
        raise SystemExit(1)
        
    logger.info(f"Split complete: Train={len(train_list)}, Val={len(val_list)}, Test={len(test_list)}")
    logger.info(f"Families: Train={len(train_ids)}, Val={len(val_ids)}, Test={len(test_ids)}")
    
    return SplitManifest(train=train_list, val=val_list, test=test_list)

def save_split_manifest(manifest: SplitManifest, output_path: Path) -> None:
    """Save the split manifest to a JSON file."""
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
    parser.add_argument("--input", type=Path, required=True, help="Input parquet file")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON file")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set fraction")
    parser.add_argument("--val-size", type=float, default=0.1, help="Validation set fraction")
    
    args = parser.parse_args()
    
    try:
        df = load_graphs_from_parquet(args.input)
        manifest = split_by_family(df, test_size=args.test_size, val_size=args.val_size)
        save_split_manifest(manifest, args.output)
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Splitting failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
