import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs() -> Path:
    """Ensure the audit output directory exists."""
    audit_dir = Path("data/audit")
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir

def load_split_data(train_path: str, test_path: str) -> tuple:
    """
    Load the training and test datasets.
    Expects paths to CSV files containing material_id and features/targets.
    
    Returns:
        tuple: (train_df, test_df) as pandas DataFrames
    """
    try:
        import pandas as pd
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        return train_df, test_df
    except Exception as e:
        logger.error(f"Failed to load split data: {e}")
        raise

def extract_material_ids(df: Any, column_name: str = "material_id") -> Set[str]:
    """
    Extract the set of unique material IDs from a DataFrame.
    
    Args:
        df: Pandas DataFrame containing the data
        column_name: The column name containing material IDs
        
    Returns:
        Set of material IDs
    """
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame. Available columns: {list(df.columns)}")
    return set(df[column_name].dropna().astype(str).unique())

def check_leakage(train_ids: Set[str], test_ids: Set[str]) -> List[str]:
    """
    Check for intersection between training and test material IDs.
    
    Args:
        train_ids: Set of material IDs in the training set
        test_ids: Set of material IDs in the test set
        
    Returns:
        List of leaking material IDs (intersection)
    """
    leakage = train_ids.intersection(test_ids)
    return sorted(list(leakage))

def write_leakage_report(leaking_ids: List[str], output_path: str, status: str) -> None:
    """
    Write the leakage report to a JSON file.
    
    Args:
        leaking_ids: List of leaking material IDs
        output_path: Path to the output JSON file
        status: Status of the audit ("PASS" or "FAIL")
    """
    report = {
        "status": status,
        "leaking_material_ids": leaking_ids,
        "leakage_count": len(leaking_ids),
        "message": "No data leakage detected." if status == "PASS" else "DATA LEAKAGE DETECTED: Training and test sets share material IDs."
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Leakage report written to {output_path}")

def run_audit_pipeline(
    train_path: str = "data/processed/train_split.csv",
    test_path: str = "data/processed/test_split.csv",
    output_path: str = "data/audit/leakage_report.json"
) -> bool:
    """
    Run the full data leakage audit pipeline.
    
    1. Load train and test splits.
    2. Extract material IDs.
    3. Check for intersection.
    4. Write report.
    5. Return True if audit passes, False if leakage detected.
    
    Args:
        train_path: Path to training data CSV
        test_path: Path to test data CSV
        output_path: Path to output leakage report JSON
        
    Returns:
        bool: True if no leakage, False if leakage detected
    """
    logger.info("Starting Data Leakage Audit...")
    
    # Ensure output directory exists
    ensure_dirs()
    
    # Load data
    train_df, test_df = load_split_data(train_path, test_path)
    logger.info(f"Loaded train ({len(train_df)} rows) and test ({len(test_df)} rows) data.")
    
    # Extract IDs
    train_ids = extract_material_ids(train_df)
    test_ids = extract_material_ids(test_df)
    logger.info(f"Found {len(train_ids)} unique materials in train, {len(test_ids)} in test.")
    
    # Check leakage
    leaking_ids = check_leakage(train_ids, test_ids)
    
    if leaking_ids:
        write_leakage_report(leaking_ids, output_path, "FAIL")
        logger.error(f"DATA LEAKAGE DETECTED! {len(leaking_ids)} materials found in both sets.")
        logger.error(f"Leaking IDs: {leaking_ids[:10]}{'...' if len(leaking_ids) > 10 else ''}")
        return False
    else:
        write_leakage_report([], output_path, "PASS")
        logger.info("Audit PASSED: No data leakage detected.")
        return True

def main():
    """Main entry point for the audit script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Leakage Audit for Model Training")
    parser.add_argument("--train", type=str, default="data/processed/train_split.csv",
                        help="Path to training data CSV")
    parser.add_argument("--test", type=str, default="data/processed/test_split.csv",
                        help="Path to test data CSV")
    parser.add_argument("--output", type=str, default="data/audit/leakage_report.json",
                        help="Path to output leakage report JSON")
    
    args = parser.parse_args()
    
    success = run_audit_pipeline(args.train, args.test, args.output)
    
    if not success:
        logger.error("Audit failed. Aborting training pipeline.")
        sys.exit(1)
    else:
        logger.info("Audit successful. Proceeding with training.")
        sys.exit(0)

if __name__ == "__main__":
    main()
