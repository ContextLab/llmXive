import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import argparse
import random

@dataclass
class SplitManifest:
    train_ids: List[str]
    val_ids: List[str]
    test_ids: List[str]
    family_splits: Dict[str, str]

def split_by_family(
    graphs: List[Dict[str, Any]],
    test_ratio: float = 0.2,
    val_ratio: float = 0.1,
    seed: int = 42
) -> SplitManifest:
    """Split graphs by chemical family to ensure family separation.
    
    This implementation ensures that no material family (chemical prototype)
    appears in both training and test sets, enabling true inter-family
    generalization evaluation as required by SC-002.
    """
    random.seed(seed)
    
    # Group by family
    families: Dict[str, List[str]] = {}
    for g in graphs:
        # Support both 'family' and 'family_id' keys for robustness
        fam = g.get('family_id') or g.get('family') or 'unknown'
        if fam not in families:
            families[fam] = []
        families[fam].append(g['material_id'])
    
    train_ids, val_ids, test_ids = [], [], []
    family_splits = {}
    
    # Sort families by size to ensure balanced splits
    # Larger families get more representation in train/val/test proportionally
    sorted_families = sorted(families.items(), key=lambda x: len(x[1]), reverse=True)
    
    for fam, ids in sorted_families:
        # Shuffle within family to avoid ordering bias
        random.shuffle(ids)
        
        # Calculate split sizes
        n_total = len(ids)
        n_test = max(1, int(n_total * test_ratio))
        n_val = max(1, int(n_total * val_ratio))
        
        # Ensure we don't allocate more than available
        if n_test + n_val >= n_total:
            # If family is too small, put most in train, small in test
            n_test = max(1, n_total // 5)
            n_val = max(1, n_total // 10)
            if n_test + n_val >= n_total:
                n_val = n_total - n_test - 1
                n_test = n_total - n_val - 1
        
        test_ids.extend(ids[:n_test])
        val_ids.extend(ids[n_test:n_test+n_val])
        train_ids.extend(ids[n_test+n_val:])
        
        # Record split assignment for each material
        for mid in ids:
            if mid in test_ids:
                family_splits[mid] = 'test'
            elif mid in val_ids:
                family_splits[mid] = 'val'
            else:
                family_splits[mid] = 'train'
    
    return SplitManifest(train_ids, val_ids, test_ids, family_splits)

def save_split_manifest(manifest: SplitManifest, path: Path):
    """Save split manifest to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(asdict(manifest), f, indent=2)

def load_graphs_from_parquet(path: Path) -> List[Dict[str, Any]]:
    """Load graphs from parquet file."""
    try:
        import pandas as pd
        df = pd.read_parquet(path)
        graphs = []
        for _, row in df.iterrows():
            # Convert row to dict, handling nested structures
            graph_dict = {}
            for col in df.columns:
                val = row[col]
                # Handle numpy arrays and other serializable types
                if hasattr(val, 'tolist'):
                    val = val.tolist()
                graph_dict[col] = val
            graphs.append(graph_dict)
        return graphs
    except ImportError:
        raise ImportError("pandas and pyarrow are required to read parquet files. "
                        "Install with: pip install pandas pyarrow")

def main():
    """Main entry point for splitting dataset by family."""
    parser = argparse.ArgumentParser(
        description="Split material graphs by chemical family for inter-family generalization testing"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        required=True,
        help="Path to input parquet file containing material graphs"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        required=True,
        help="Path to output split manifest JSON file"
    )
    parser.add_argument(
        "--test-ratio", 
        type=float, 
        default=0.2,
        help="Ratio of data to use for test set (default: 0.2)"
    )
    parser.add_argument(
        "--val-ratio", 
        type=float, 
        default=0.1,
        help="Ratio of data to use for validation set (default: 0.1)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info(f"Loading graphs from {args.input}")
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    graphs = load_graphs_from_parquet(input_path)
    logger.info(f"Loaded {len(graphs)} graphs")
    
    # Perform family-based split
    logger.info(f"Splitting by family (test={args.test_ratio}, val={args.val_ratio}, seed={args.seed})")
    manifest = split_by_family(
        graphs,
        test_ratio=args.test_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed
    )
    
    # Verify family separation
    train_families = set()
    val_families = set()
    test_families = set()
    
    for mid, split in manifest.family_splits.items():
        # Find the family for this material
        for g in graphs:
            if g['material_id'] == mid:
                fam = g.get('family_id') or g.get('family') or 'unknown'
                if split == 'train':
                    train_families.add(fam)
                elif split == 'val':
                    val_families.add(fam)
                elif split == 'test':
                    test_families.add(fam)
                break
    
    # Check for family overlap
    train_test_overlap = train_families & test_families
    if train_test_overlap:
        logger.warning(f"WARNING: {len(train_test_overlap)} families appear in both train and test sets!")
        logger.warning(f"Overlapping families: {train_test_overlap}")
    else:
        logger.info("SUCCESS: No family overlap between train and test sets")
    
    logger.info(f"Train: {len(manifest.train_ids)} materials")
    logger.info(f"Val: {len(manifest.val_ids)} materials")
    logger.info(f"Test: {len(manifest.test_ids)} materials")
    
    # Save manifest
    output_path = Path(args.output)
    save_split_manifest(manifest, output_path)
    logger.info(f"Split manifest saved to {output_path}")
    
    # Print summary
    print(f"\nSplit Summary:")
    print(f"  Train: {len(manifest.train_ids)} materials")
    print(f"  Val:   {len(manifest.val_ids)} materials")
    print(f"  Test:  {len(manifest.test_ids)} materials")
    print(f"  Output: {output_path}")

if __name__ == "__main__":
    main()