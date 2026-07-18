"""
Stratified splitting logic for 2D material graphs.

Splits data by family_id (chemical prototype/space group) to ensure
no family appears in both train and test sets (SC-002 compliance).
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

# Import from sibling modules as per API surface
# Note: pyarrow is required for parquet support, usually installed with pandas
try:
    import pyarrow
except ImportError:
    raise ImportError("pyarrow is required for parquet support. Install with: pip install pyarrow")

@dataclass
class SplitManifest:
    """Schema for the split indices output."""
    train: List[Dict[str, str]]
    val: List[Dict[str, str]]
    test: List[Dict[str, str]]
    metadata: Dict[str, Any]

def load_graphs_from_parquet(parquet_path: Path) -> pd.DataFrame:
    """
    Load graph data from a parquet file.
    
    Args:
        parquet_path: Path to the parquet file.
        
    Returns:
        DataFrame containing graph data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    
    required_cols = ['id', 'family_id']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {parquet_path}: {missing}")
    
    return df

def split_by_family(
    df: pd.DataFrame,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> SplitManifest:
    """
    Split data by family_id to ensure family separation.
    
    This function groups materials by their `family_id`, then splits the
    groups into train, validation, and test sets. This ensures that no
    family appears in more than one split, satisfying SC-002 (Family Separation).
    
    Args:
        df: DataFrame containing graph data with 'id' and 'family_id' columns.
        train_ratio: Fraction of families for training.
        val_ratio: Fraction of families for validation.
        test_ratio: Fraction of families for testing.
        seed: Random seed for reproducibility.
        
    Returns:
        SplitManifest containing the split indices.
        
    Raises:
        ValueError: If ratios do not sum to 1.0 or if there are insufficient families.
        SystemExit: If family overlap is detected (SC-002 violation).
    """
    if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
        raise ValueError(f"Ratios must sum to 1.0, got {train_ratio + val_ratio + test_ratio}")
    
    # Group by family_id
    families = df['family_id'].unique()
    if len(families) < 10:
        raise ValueError(f"Insufficient number of families ({len(families)}) for splitting.")
    
    # Set seed for reproducibility
    rng = np.random.default_rng(seed)
    
    # Shuffle families
    shuffled_families = rng.permutation(families).tolist()
    
    # Calculate split sizes
    n_families = len(shuffled_families)
    n_train = int(n_families * train_ratio)
    n_val = int(n_families * val_ratio)
    n_test = n_families - n_train - n_val
    
    if n_test == 0:
        raise ValueError(f"Insufficient families for test set (n_test=0). Total families: {n_families}")
    
    # Split families
    train_families = set(shuffled_families[:n_train])
    val_families = set(shuffled_families[n_train:n_train + n_val])
    test_families = set(shuffled_families[n_train + n_val:])
    
    # Verify no overlap
    train_val_overlap = train_families & val_families
    train_test_overlap = train_families & test_families
    val_test_overlap = val_families & test_families
    
    if train_val_overlap or train_test_overlap or val_test_overlap:
        logging.error("SC-002 Violation: Family overlap detected in split.")
        if train_val_overlap:
            logging.error(f"Train/Val overlap: {train_val_overlap}")
        if train_test_overlap:
            logging.error(f"Train/Test overlap: {train_test_overlap}")
        if val_test_overlap:
            logging.error(f"Val/Test overlap: {val_test_overlap}")
        sys.exit(1)
    
    # Build split indices
    train_list = []
    val_list = []
    test_list = []
    
    for _, row in df.iterrows():
        entry = {"id": row['id'], "family_id": row['family_id']}
        if row['family_id'] in train_families:
            train_list.append(entry)
        elif row['family_id'] in val_families:
            val_list.append(entry)
        else:
            test_list.append(entry)
    
    # Final verification
    train_ids = {x['id'] for x in train_list}
    val_ids = {x['id'] for x in val_list}
    test_ids = {x['id'] for x in test_list}
    
    # Check for ID overlap (should not happen if family split is correct)
    id_overlaps = []
    if train_ids & val_ids: id_overlaps.append("Train/Val")
    if train_ids & test_ids: id_overlaps.append("Train/Test")
    if val_ids & test_ids: id_overlaps.append("Val/Test")
    
    if id_overlaps:
        logging.error(f"SC-002 Violation: ID overlap detected in splits: {id_overlaps}")
        sys.exit(1)
    
    logging.info(f"Split complete: Train={len(train_list)}, Val={len(val_list)}, Test={len(test_list)}")
    logging.info(f"Train families: {len(train_families)}, Val families: {len(val_families)}, Test families: {len(test_families)}")
    
    return SplitManifest(
        train=train_list,
        val=val_list,
        test=test_list,
        metadata={
            "seed": seed,
            "train_ratio": train_ratio,
            "val_ratio": val_ratio,
            "test_ratio": test_ratio,
            "total_families": n_families,
            "train_families": len(train_families),
            "val_families": len(val_families),
            "test_families": len(test_families)
        }
    )

def save_split_manifest(manifest: SplitManifest, output_path: Path) -> None:
    """
    Save the split manifest to a JSON file.
    
    Args:
        manifest: The SplitManifest object to save.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "train": manifest.train,
        "val": manifest.val,
        "test": manifest.test,
        "metadata": manifest.metadata
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logging.info(f"Split manifest saved to {output_path}")

def main():
    """
    Main entry point for the splitter script.
    
    Usage:
        python code/model/splitter.py --input data/processed/graphs_v1.parquet --output data/processed/split_indices.json
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Split graphs by family for train/val/test sets.")
    parser.add_argument("--input", type=str, required=True, help="Path to input parquet file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file.")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Fraction of families for training.")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Fraction of families for validation.")
    parser.add_argument("--test-ratio", type=float, default=0.1, help="Fraction of families for testing.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        logging.info(f"Loading data from {input_path}...")
        df = load_graphs_from_parquet(input_path)
        
        logging.info(f"Splitting data by family (seed={args.seed})...")
        manifest = split_by_family(
            df,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio,
            seed=args.seed
        )
        
        logging.info(f"Saving split manifest to {output_path}...")
        save_split_manifest(manifest, output_path)
        
        logging.info("Splitting completed successfully.")
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()