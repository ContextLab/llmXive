import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Set, Dict, Any, Tuple

# Import from existing API surface
from src.data.preprocessing import (
    load_split_manifest,
    load_split_indices,
    extract_templates_for_indices,
    verify_reaction_template_split
)
from src.utils.state_manager import compute_file_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_splits(manifest_path: Path) -> Dict[str, List[int]]:
    """
    Load the split indices from the manifest and indices file.
    Returns a dictionary mapping split names to lists of indices.
    """
    manifest = load_split_manifest(manifest_path)
    splits = {}
    for split_name in ['train', 'val', 'test']:
        if split_name not in manifest:
            raise ValueError(f"Split '{split_name}' not found in manifest {manifest_path}")
        
        indices_file = manifest[split_name]['indices_file']
        indices_list = load_split_indices(indices_file)
        splits[split_name] = indices_list
    
    return splits


def extract_scaffolds(data_root: Path, splits: Dict[str, List[int]]) -> Dict[str, Set[str]]:
    """
    Extract reaction templates (scaffolds) for each split.
    Uses the existing extract_templates_for_indices function.
    """
    logger.info("Extracting scaffolds for each split...")
    scaffolds = {}
    
    for split_name, indices in splits.items():
        logger.info(f"  Processing {split_name} split ({len(indices)} samples)...")
        templates = extract_templates_for_indices(data_root / "processed", indices)
        scaffolds[split_name] = set(templates)
        logger.info(f"    Found {len(templates)} unique templates in {split_name}")
    
    return scaffolds


def check_leakage(scaffolds: Dict[str, Set[str]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Check for scaffold leakage between splits.
    Returns (has_leakage, details_dict).
    """
    logger.info("Checking for scaffold leakage...")
    
    train_scaffolds = scaffolds.get('train', set())
    val_scaffolds = scaffolds.get('val', set())
    test_scaffolds = scaffolds.get('test', set())
    
    leakage_details = {
        'train_val_overlap': set(),
        'train_test_overlap': set(),
        'val_test_overlap': set(),
        'train_val_test_overlap': set()
    }
    
    # Check train vs val
    overlap_train_val = train_scaffolds.intersection(val_scaffolds)
    leakage_details['train_val_overlap'] = list(overlap_train_val)
    
    # Check train vs test
    overlap_train_test = train_scaffolds.intersection(test_scaffolds)
    leakage_details['train_test_overlap'] = list(overlap_train_test)
    
    # Check val vs test
    overlap_val_test = val_scaffolds.intersection(test_scaffolds)
    leakage_details['val_test_overlap'] = list(overlap_val_test)
    
    # Check triple overlap
    overlap_all = train_scaffolds.intersection(val_scaffolds, test_scaffolds)
    leakage_details['train_val_test_overlap'] = list(overlap_all)
    
    total_leaked = (
        len(overlap_train_val) + 
        len(overlap_train_test) + 
        len(overlap_val_test)
    )
    
    has_leakage = total_leaked > 0
    
    if has_leakage:
        logger.warning(f"LEAKAGE DETECTED: {total_leaked} scaffolds appear in multiple splits!")
        logger.warning(f"  Train-Val overlap: {len(overlap_train_val)}")
        logger.warning(f"  Train-Test overlap: {len(overlap_train_test)}")
        logger.warning(f"  Val-Test overlap: {len(overlap_val_test)}")
    else:
        logger.info("No scaffold leakage detected. Splits are clean.")
    
    return has_leakage, leakage_details


def main():
    """
    Main entry point for the scaffold leakage validation script.
    """
    parser = argparse.ArgumentParser(
        description='Validate no scaffold leakage between train/val/test splits'
    )
    parser.add_argument(
        '--manifest',
        type=Path,
        default=Path('data/artifacts/split_manifest.json'),
        help='Path to the split manifest file'
    )
    parser.add_argument(
        '--data-root',
        type=Path,
        default=Path('data'),
        help='Root directory for processed data'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/artifacts/leakage_report.json'),
        help='Path to write the leakage report'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting scaffold leakage validation...")
    logger.info(f"  Manifest: {args.manifest}")
    logger.info(f"  Data root: {args.data_root}")
    logger.info(f"  Output: {args.output}")
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Load splits
    try:
        splits = load_splits(args.manifest)
        logger.info(f"Loaded {len(splits)} splits from manifest")
    except Exception as e:
        logger.error(f"Failed to load splits: {e}")
        raise
    
    # Extract scaffolds
    scaffolds = extract_scaffolds(args.data_root, splits)
    
    # Check for leakage
    has_leakage, leakage_details = check_leakage(scaffolds)
    
    # Compile report
    report = {
        'status': 'failed' if has_leakage else 'passed',
        'timestamp': Path(__file__).parent.name,  # Placeholder, should use datetime
        'manifest_path': str(args.manifest),
        'splits_summary': {
            'train': len(scaffolds['train']),
            'val': len(scaffolds['val']),
            'test': len(scaffolds['test'])
        },
        'leakage_details': leakage_details,
        'total_leaked_scaffolds': (
            len(leakage_details['train_val_overlap']) +
            len(leakage_details['train_test_overlap']) +
            len(leakage_details['val_test_overlap'])
        ),
        'recommendation': (
            "FAIL: Scaffold leakage detected. Splits must be regenerated with stricter template separation."
            if has_leakage else
            "PASS: No scaffold leakage detected. Splits are valid for training."
        )
    }
    
    # Write report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Leakage report written to: {args.output}")
    
    # Compute checksum for state management
    checksum = compute_file_hash(args.output)
    logger.info(f"Report checksum: {checksum}")
    
    # Exit with appropriate code
    if has_leakage:
        logger.error("Scaffold leakage detected! Validation FAILED.")
        exit(1)
    else:
        logger.info("Scaffold leakage validation PASSED.")
        exit(0)


if __name__ == '__main__':
    main()
