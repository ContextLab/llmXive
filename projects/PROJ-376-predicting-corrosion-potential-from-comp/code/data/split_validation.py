import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
import pandas as pd
from sklearn.model_selection import GroupKFold

from utils.logging import get_logger
from utils.exceptions import DataInsufficientError
from utils.config import get_processed_dataset_path, get_split_indices_path, get_split_validation_path, get_log_path

logger = get_logger(__name__)

def load_split_indices() -> Dict[str, List[Tuple[List[int], List[int]]]]:
    """
    Load the saved train/test indices from the split task.
    Expected format: JSON file containing a list of fold dictionaries.
    """
    split_file = get_split_indices_path()
    if not split_file.exists():
        raise FileNotFoundError(f"Split indices file not found: {split_file}")

    with open(split_file, 'r') as f:
        data = json.load(f)

    return data

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed dataset to access alloy designations.
    """
    data_path = get_processed_dataset_path()
    if not data_path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {data_path}")

    return pd.read_parquet(data_path)

def validate_split_integrity(split_data: Dict[str, List[Tuple[List[int], List[int]]]], 
                             df: pd.DataFrame, 
                             alloy_column: str = "specific_alloy_designation_id") -> Dict[str, Any]:
    """
    Verify that GroupKFold constraint is met: zero overlap of specific_alloy_designation_id 
    between train and test sets for each fold.
    
    Args:
        split_data: Dict containing fold indices (train, test)
        df: Preprocessed DataFrame containing alloy designations
        alloy_column: Column name for alloy ID
    
    Returns:
        Dictionary containing fold statistics and overlap verification results.
    """
    results = {
        "total_folds": len(split_data),
        "folds": [],
        "global_status": "PASS",
        "details": []
    }

    # Extract alloy designations for all rows
    if alloy_column not in df.columns:
        raise ValueError(f"Alloy column '{alloy_column}' not found in dataset. Available: {list(df.columns)}")
    
    alloy_series = df[alloy_column].astype(str)

    for fold_idx, fold_data in enumerate(split_data):
        train_indices = fold_data["train_indices"]
        test_indices = fold_data["test_indices"]

        # Get alloy IDs for train and test
        train_alloys = set(alloy_series.iloc[train_indices].values)
        test_alloys = set(alloy_series.iloc[test_indices].values)

        # Check for overlap
        overlap = train_alloys.intersection(test_alloys)
        
        fold_result = {
            "fold_id": fold_idx,
            "train_count": len(train_indices),
            "test_count": len(test_indices),
            "unique_train_alloys": len(train_alloys),
            "unique_test_alloys": len(test_alloys),
            "overlap_count": len(overlap),
            "overlap_alloys": sorted(list(overlap)),
            "status": "FAIL" if len(overlap) > 0 else "PASS"
        }
        
        results["folds"].append(fold_result)
        results["details"].append(
            f"Fold {fold_idx}: Train({len(train_indices)}) vs Test({len(test_indices)}) -> Overlap: {len(overlap)}"
        )

        if len(overlap) > 0:
            results["global_status"] = "FAIL"
            logger.error(f"Split Integrity FAILED for Fold {fold_idx}: Found {len(overlap)} overlapping alloy(s): {overlap}")
        else:
            logger.info(f"Fold {fold_idx} integrity check PASSED.")

    return results

def save_split_results(validation_results: Dict[str, Any]) -> Path:
    """
    Save the split validation results to the designated JSON file.
    """
    output_path = get_split_validation_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    logger.info(f"Split validation results saved to: {output_path}")
    return output_path

def main():
    """
    Main entry point for T017: Verify split integrity.
    """
    logger.info("Starting split integrity verification (T017)...")
    
    try:
        # Load indices and data
        split_data = load_split_indices()
        df = load_processed_data()
        
        logger.info(f"Loaded {len(split_data)} folds and {len(df)} records.")
        
        # Validate integrity
        results = validate_split_integrity(split_data, df)
        
        # Save results
        output_path = save_split_results(results)
        
        # Final status
        if results["global_status"] == "PASS":
            logger.info("Split integrity verification PASSED. No alloy leakage detected.")
            return 0
        else:
            logger.error("Split integrity verification FAILED. Alloy leakage detected.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Critical file missing: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
