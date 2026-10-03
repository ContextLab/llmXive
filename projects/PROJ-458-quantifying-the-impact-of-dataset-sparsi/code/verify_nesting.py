"""
T032c: Verify strict nesting of all sparsity subsets.

Reads all sparsity_<level>pct.csv files from data/processed/,
verifies that the set of indices in each subset is a strict subset
of the next larger subset, and logs the result to 
data/metadata/nesting_verification.json.
"""
import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
from utils.logging import get_logger

# Expected sparsity levels in ascending order as defined in T032b
SPARSITY_LEVELS = [1, 2, 5, 10, 25, 50, 100]

def load_subset_indices(file_path: Path) -> set:
    """Load the 'material_id' (or index) column from a CSV and return as a set."""
    if not file_path.exists():
        raise FileNotFoundError(f"Sparsity subset file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    # Determine the index column name. Usually 'material_id' or the first column.
    # Based on T032b, we expect a column identifying the rows (likely material_id).
    # If the CSV has an explicit index column saved, use that.
    # Assuming 'material_id' is the primary key based on data_ingestion.py context.
    if 'material_id' in df.columns:
        return set(df['material_id'].astype(str))
    elif 'id' in df.columns:
        return set(df['id'].astype(str))
    else:
        # Fallback: use the first column if it looks like an ID
        first_col = df.columns[0]
        return set(df[first_col].astype(str))

def verify_nesting(
    processed_dir: Path, 
    metadata_dir: Path, 
    logger: logging.Logger
) -> dict:
    """
    Verify that sparsity subsets are strictly nested.
    
    Returns a dict with:
      - is_strictly_nested: bool
      - details: list of verification steps
    """
    results = {
        "is_strictly_nested": True,
        "details": [],
        "subset_sizes": {}
    }

    prev_set = None
    prev_level = None

    for level in SPARSITY_LEVELS:
        file_name = f"sparsity_{level}pct.csv"
        file_path = processed_dir / file_name
        
        if not file_path.exists():
            msg = f"Missing file: {file_name}"
            results["details"].append({"level": level, "status": "missing", "error": msg})
            results["is_strictly_nested"] = False
            continue

        try:
            current_set = load_subset_indices(file_path)
            results["subset_sizes"][level] = len(current_set)
            
            if prev_set is not None:
                # Check strict subset: prev must be a subset of current
                # And sizes must be strictly increasing (unless 0 rows, which shouldn't happen)
                if not prev_set.issubset(current_set):
                    msg = f"Level {prev_level} is NOT a subset of Level {level}"
                    results["details"].append({"level": level, "status": "fail", "error": msg})
                    results["is_strictly_nested"] = False
                elif len(prev_set) >= len(current_set):
                    # Should be strictly increasing size for nested samples
                    msg = f"Level {prev_level} size ({len(prev_set)}) >= Level {level} size ({len(current_set)})"
                    results["details"].append({"level": level, "status": "fail", "error": msg})
                    results["is_strictly_nested"] = False
                else:
                    results["details"].append({
                        "level": level, 
                        "status": "pass", 
                        "prev_size": len(prev_set), 
                        "curr_size": len(current_set)
                    })
            else:
                results["details"].append({"level": level, "status": "pass", "note": "First level"})
            
            prev_set = current_set
            prev_level = level

        except Exception as e:
            msg = f"Error processing {file_name}: {str(e)}"
            results["details"].append({"level": level, "status": "error", "error": msg})
            results["is_strictly_nested"] = False

    return results

def main():
    logger = get_logger("verify_nesting")
    logger.info("Starting nesting verification (T032c).")

    # Define paths relative to project root
    # Assuming script is run from project root or code/
    base_dir = Path(____).parent.parent if '__file__' in globals() else Path.cwd()
    # Fallback to cwd if running as module
    if not (base_dir / "data").exists():
        base_dir = Path.cwd()

    processed_dir = base_dir / "data" / "processed"
    metadata_dir = base_dir / "data" / "metadata"

    # Ensure metadata directory exists
    metadata_dir.mkdir(parents=True, exist_ok=True)

    if not processed_dir.exists():
        logger.error(f"Processed directory not found: {processed_dir}")
        sys.exit(1)

    verification_result = verify_nesting(processed_dir, metadata_dir, logger)

    output_file = metadata_dir / "nesting_verification.json"
    with open(output_file, 'w') as f:
        json.dump(verification_result, f, indent=2)

    logger.info(f"Verification complete. Result: {verification_result['is_strictly_nested']}")
    logger.info(f"Output written to: {output_file}")

    if not verification_result['is_strictly_nested']:
        logger.error("Nnesting verification FAILED. Please check the details.")
        sys.exit(1)
    else:
        logger.info("Nnesting verification PASSED.")

if __name__ == "__main__":
    main()
