import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from sklearn.model_selection import GroupKFold

from utils.config import get_log_path, get_processed_data_path, get_split_validation_path
from utils.exceptions import DataInsufficientError
from utils.logging import get_logger

logger = get_logger(__name__)

def load_processed_dataset() -> pd.DataFrame:
    """Load the preprocessed corrosion dataset."""
    path = get_processed_data_path("corrosion_dataset.parquet")
    if not path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {path}. Run preprocessing first.")
    return pd.read_parquet(path)

def validate_alloy_diversity(df: pd.DataFrame, min_alloys: int = 10) -> bool:
    """
    Verify the dataset contains enough unique specific alloy designations for LOSO/GroupKFold.
    Returns True if diversity is sufficient, raises DataInsufficientError otherwise.
    """
    group_col = "specific_alloy_designation"
    if group_col not in df.columns:
        # Fallback to ID if column name differs, but prefer the string designation per spec
        if "specific_alloy_designation_id" in df.columns:
            group_col = "specific_alloy_designation_id"
        else:
            logger.error(f"Neither 'specific_alloy_designation' nor 'specific_alloy_designation_id' found in dataset columns: {list(df.columns)}")
            return False
    
    unique_alloys = df[group_col].nunique()
    logger.info(f"Found {unique_alloys} unique alloy designations in column '{group_col}'.")
    
    if unique_alloys < min_alloys:
        logger.error(f"Insufficient alloy diversity: {unique_alloys} < {min_alloys} required.")
        return False
    return True

def perform_groupkfold_split(df: pd.DataFrame, n_splits: int = 5, random_state: int = 42) -> List[Tuple[List[int], List[int]]]:
    """
    Perform GroupKFold splitting using 'specific_alloy_designation' (or ID) as groups.
    This ensures no specific alloy appears in both train and test sets (LOSO logic per fold).
    
    FR-004/FR-012: Prevent data leakage by ensuring strict group separation.
    
    Returns a list of (train_indices, test_indices) tuples.
    """
    group_col = "specific_alloy_designation"
    if group_col not in df.columns:
        if "specific_alloy_designation_id" in df.columns:
            group_col = "specific_alloy_designation_id"
        else:
            raise ValueError(f"Group column 'specific_alloy_designation' not found in dataset.")
    
    groups = df[group_col].values
    
    logger.info(f"Performing GroupKFold split with n_splits={n_splits} using group column '{group_col}'.")
    
    gkf = GroupKFold(n_splits=n_splits)
    splits = list(gkf.split(df, groups=groups))
    
    logger.info(f"Generated {n_splits} GroupKFold splits.")
    return splits

def validate_split_integrity(splits: List[Tuple[List[int], List[int]]], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify strict GroupKFold constraint: zero overlap of specific_alloy_designation between train/test in each fold.
    
    Returns validation statistics including overlap counts.
    """
    group_col = "specific_alloy_designation"
    if group_col not in df.columns:
        if "specific_alloy_designation_id" in df.columns:
            group_col = "specific_alloy_designation_id"
        else:
            raise ValueError(f"Group column '{group_col}' not found in dataset for validation.")
    
    validation_results = {
        "total_splits": len(splits),
        "split_stats": [],
        "global_overlap_check": True,
        "details": [],
        "group_column_used": group_col
    }

    for i, (train_idx, test_idx) in enumerate(splits):
        train_alloys = set(df.iloc[train_idx][group_col].unique())
        test_alloys = set(df.iloc[test_idx][group_col].unique())
        
        overlap = train_alloys.intersection(test_alloys)
        is_valid = len(overlap) == 0
        
        split_stat = {
            "fold_index": i,
            "train_size": len(train_idx),
            "test_size": len(test_idx),
            "train_alloy_count": len(train_alloys),
            "test_alloy_count": len(test_alloys),
            "overlap_count": len(overlap),
            "is_valid": is_valid
        }
        
        validation_results["split_stats"].append(split_stat)
        
        if not is_valid:
            validation_results["global_overlap_check"] = False
            msg = f"Fold {i}: Found {len(overlap)} overlapping alloy IDs: {list(overlap)}"
            validation_results["details"].append(msg)
            logger.error(msg)
        else:
            logger.info(f"Fold {i}: Valid (0 overlap). Train alloys: {len(train_alloys)}, Test alloys: {len(test_alloys)}")

    if validation_results["global_overlap_check"]:
        logger.info("Split integrity check PASSED: No alloy leakage detected across all folds.")
    else:
        logger.error("Split integrity check FAILED: Alloy leakage detected.")
    
    return validation_results

def save_split_results(validation_results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save split validation results to JSON.
    Default path: data/logs/split_validation.json
    """
    if output_path is None:
        output_path = get_split_validation_path()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    logger.info(f"Split validation results saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for T015: Implement LOSO/GroupKFold split logic.
    
    1. Load processed dataset.
    2. Validate alloy diversity (>= 10 specific alloys).
    3. Perform GroupKFold split.
    4. Validate split integrity (zero overlap).
    5. Save results to data/logs/split_validation.json.
    """
    logger.info("Starting T015: Implement LOSO/GroupKFold split logic.")
    
    # 1. Load data
    try:
        df = load_processed_dataset()
    except FileNotFoundError as e:
        logger.critical(str(e))
        raise DataInsufficientError(f"Cannot perform split: {e}")
    
    # 2. Validate diversity
    if not validate_alloy_diversity(df, min_alloys=10):
        msg = "Insufficient alloy diversity for split. Cannot proceed with T015."
        logger.critical(msg)
        raise DataInsufficientError(msg)
    
    # 3. Perform split
    splits = perform_groupkfold_split(df, n_splits=5, random_state=42)
    
    # 4. Validate integrity
    results = validate_split_integrity(splits, df)
    
    # 5. Save results
    save_path = save_split_results(results)
    
    # 6. Final status
    if results["global_overlap_check"]:
        logger.info("T015 COMPLETED: Split logic implemented and integrity verified.")
        return 0
    else:
        logger.error("T015 FAILED: Split integrity check failed.")
        return 1

if __name__ == "__main__":
    exit(main())