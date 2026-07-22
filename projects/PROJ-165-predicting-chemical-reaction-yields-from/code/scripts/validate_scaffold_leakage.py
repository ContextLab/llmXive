"""
Script to validate scaffold-based splitting for zero leakage between train/val/test sets.
Reads processed split files, extracts scaffolds, and verifies no overlap.
Outputs a JSON report to data/artifacts/leakage_report.json.
"""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Set, Dict, Any

import pandas as pd
import numpy as np

# Add project root to path if running as script
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys_path = str(PROJECT_ROOT / "code")
if sys_path not in os.sys.path:
    os.sys.path.insert(0, sys_path)

from src.data.preprocessing import get_scaffold
from src.utils.state_manager import update_state, load_state, log_task_start, log_task_complete
from src.utils.seeds import set_seed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_splits(split_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load train, val, test CSV files from the processed directory."""
    splits = {}
    for split_name in ["train", "val", "test"]:
        file_path = split_dir / f"{split_name}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Split file not found: {file_path}")
        
        logger.info(f"Loading {split_name} split from {file_path}")
        df = pd.read_csv(file_path)
        splits[split_name] = df
        logger.info(f"Loaded {len(df)} samples for {split_name}")
    
    return splits

def extract_scaffolds(df: pd.DataFrame, scaffold_col: str = "scaffold") -> Set[str]:
    """Extract unique scaffolds from a dataframe."""
    if scaffold_col not in df.columns:
        # Attempt to generate if not present (fallback for old data)
        logger.warning(f"Column '{scaffold_col}' not found, generating scaffolds from 'smiles'")
        if "smiles" not in df.columns:
            raise ValueError("DataFrame must contain 'smiles' column or pre-computed 'scaffold' column")
        df[scaffold_col] = df["smiles"].apply(get_scaffold)
    
    return set(df[scaffold_col].dropna().unique())

def check_leakage(splits: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Check for scaffold overlap between train, val, and test sets."""
    train_scaffolds = extract_scaffolds(splits["train"])
    val_scaffolds = extract_scaffolds(splits["val"])
    test_scaffolds = extract_scaffolds(splits["test"])

    results = {
        "train_count": len(splits["train"]),
        "val_count": len(splits["val"]),
        "test_count": len(splits["test"]),
        "train_scaffold_count": len(train_scaffolds),
        "val_scaffold_count": len(val_scaffolds),
        "test_scaffold_count": len(test_scaffolds),
        "leakage_detected": False,
        "details": {}
    }

    # Check Train vs Val
    train_val_overlap = train_scaffolds.intersection(val_scaffolds)
    if train_val_overlap:
        results["leakage_detected"] = True
        results["details"]["train_val_overlap"] = list(train_val_overlap)[:10]  # Limit log size
        results["details"]["train_val_overlap_count"] = len(train_val_overlap)
    
    # Check Train vs Test
    train_test_overlap = train_scaffolds.intersection(test_scaffolds)
    if train_test_overlap:
        results["leakage_detected"] = True
        results["details"]["train_test_overlap"] = list(train_test_overlap)[:10]
        results["details"]["train_test_overlap_count"] = len(train_test_overlap)

    # Check Val vs Test
    val_test_overlap = val_scaffolds.intersection(test_scaffolds)
    if val_test_overlap:
        results["leakage_detected"] = True
        results["details"]["val_test_overlap"] = list(val_test_overlap)[:10]
        results["details"]["val_test_overlap_count"] = len(val_test_overlap)

    # Check all three
    if not results["leakage_detected"]:
        results["details"]["status"] = "PASS: No scaffold leakage detected"
    else:
        results["details"]["status"] = "FAIL: Scaffold leakage detected"

    return results

def main():
    parser = argparse.ArgumentParser(description="Validate scaffold leakage in data splits")
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default=str(PROJECT_ROOT / "data" / "processed"),
        help="Directory containing train/val/test CSV files"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(PROJECT_ROOT / "data" / "artifacts" / "leakage_report.json"),
        help="Path to save the leakage report"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42, 
        help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    set_seed(args.seed)
    
    data_dir = Path(args.data_dir)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log_task_start("T020", "Validating scaffold leakage")

    try:
        logger.info(f"Reading splits from {data_dir}")
        splits = load_splits(data_dir)
        
        logger.info("Checking for scaffold leakage...")
        report = check_leakage(splits)
        
        # Add metadata
        report["timestamp"] = str(Path(__file__).resolve().parent)
        report["data_dir"] = str(data_dir)
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Leakage report saved to {output_path}")
        
        if report["leakage_detected"]:
            logger.error(f"Leakage detected! {report['details']['status']}")
            # Do not exit with error code to allow pipeline to continue to next steps if needed, 
            # but log clearly. The execution stage can check this file.
        else:
            logger.info(f"Validation successful: {report['details']['status']}")

        # Update state
        update_state("T020", "completed", str(output_path))
        log_task_complete("T020", "Leakage validation completed")

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        update_state("T020", "failed", str(e))
        log_task_complete("T020", f"Failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()