import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from utils.logging import get_logger
from config import get_config

def get_logger_wrapper(logger_name: str = "validate") -> logging.Logger:
    """Get a logger instance for this module."""
    return get_logger(logger_name)

def check_variable_presence(df: pd.DataFrame, required_vars: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if all required variables are present in the DataFrame columns.
    
    Args:
        df: DataFrame to check
        required_vars: List of required column names
        
    Returns:
        Tuple of (all_present, list_of_missing_vars)
    """
    logger = get_logger("validate")
    missing = [var for var in required_vars if var not in df.columns]
    all_present = len(missing) == 0
    
    if not all_present:
        logger.warning(f"Missing required variables: {missing}")
    else:
        logger.info("All required variables present")
        
    return all_present, missing

def validate_data_content(df: pd.DataFrame, required_vars: List[str]) -> Dict[str, Any]:
    """
    Validate that the data contains non-empty values for required variables.
    
    Args:
        df: DataFrame to validate
        required_vars: List of required column names
        
    Returns:
        Dictionary with validation results
    """
    logger = get_logger("validate")
    results = {
        "total_rows": len(df),
        "variables_checked": required_vars,
        "valid_records": 0,
        "invalid_records": 0,
        "missing_data": {}
    }
    
    valid_count = 0
    for idx, row in df.iterrows():
        is_valid = True
        for var in required_vars:
            if var not in row or pd.isna(row[var]):
                is_valid = False
                if var not in results["missing_data"]:
                    results["missing_data"][var] = 0
                results["missing_data"][var] += 1
        
        if is_valid:
            valid_count += 1
        else:
            results["invalid_records"] += 1
    
    results["valid_records"] = valid_count
    logger.info(f"Valid records: {valid_count}/{len(df)}")
    
    return results

def define_generic_roi_grid(image_width: int = 64, image_height: int = 64) -> Dict[str, Tuple[int, int, int, int]]:
    """
    Define a 3x3 grid of ROIs for face images.
    
    Args:
        image_width: Width of the face image
        image_height: Height of the face image
        
    Returns:
        Dictionary mapping ROI names to (x, y, width, height) tuples
    """
    logger = get_logger("validate")
    
    cell_width = image_width // 3
    cell_height = image_height // 3
    
    roi_grid = {
        "top_left": (0, 0, cell_width, cell_height),
        "top_center": (cell_width, 0, cell_width, cell_height),
        "top_right": (2 * cell_width, 0, cell_width, cell_height),
        "middle_left": (0, cell_height, cell_width, cell_height),
        "middle_center": (cell_width, cell_height, cell_width, cell_height),
        "middle_right": (2 * cell_width, cell_height, cell_width, cell_height),
        "bottom_left": (0, 2 * cell_height, cell_width, cell_height),
        "bottom_center": (cell_width, 2 * cell_height, cell_width, cell_height),
        "bottom_right": (2 * cell_width, 2 * cell_height, cell_width, cell_height),
    }
    
    logger.info(f"Generated 3x3 ROI grid for {image_width}x{image_height} image")
    return roi_grid

def apply_roi_fallback(df: pd.DataFrame, image_width: int = 64, image_height: int = 64) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply Generic ROI Fallback (3x3 grid) if roi_annotations are missing.
    
    This function checks if 'roi_annotations' column is missing or empty,
    and if so, generates a default 3x3 grid annotation for each record.
    
    Args:
        df: DataFrame containing gaze data
        image_width: Width of face images (default 64)
        image_height: Height of face images (default 64)
        
    Returns:
        Tuple of (modified_df, fallback_info)
    """
    logger = get_logger("validate")
    fallback_info = {
        "applied": False,
        "grid_type": "3x3",
        "image_dimensions": (image_width, image_height),
        "records_modified": 0,
        "reason": ""
    }
    
    # Check if roi_annotations column exists
    if "roi_annotations" not in df.columns:
        logger.info("roi_annotations column missing - applying 3x3 grid fallback")
        fallback_info["reason"] = "Column 'roi_annotations' does not exist"
        fallback_info["applied"] = True
        
        # Generate grid for all records
        grid = define_generic_roi_grid(image_width, image_height)
        fallback_annotations = [grid for _ in range(len(df))]
        df["roi_annotations"] = fallback_annotations
        fallback_info["records_modified"] = len(df)
        
    else:
        # Check if roi_annotations are empty/None for any records
        empty_mask = df["roi_annotations"].isna() | (df["roi_annotations"].apply(lambda x: x is None or (isinstance(x, dict) and len(x) == 0)))
        empty_count = empty_mask.sum()
        
        if empty_count > 0:
            logger.info(f"Found {empty_count} records with empty roi_annotations - applying 3x3 grid fallback")
            fallback_info["reason"] = f"{empty_count} records had missing/empty roi_annotations"
            fallback_info["applied"] = True
            
            grid = define_generic_roi_grid(image_width, image_height)
            
            # Apply fallback only to records with empty annotations
            def apply_fallback_if_empty(annotations):
                if pd.isna(annotations) or annotations is None or (isinstance(annotations, dict) and len(annotations) == 0):
                    return grid
                return annotations
            
            df.loc[empty_mask, "roi_annotations"] = df.loc[empty_mask, "roi_annotations"].apply(apply_fallback_if_empty)
            fallback_info["records_modified"] = int(empty_count)
        else:
            logger.info("All records have valid roi_annotations - no fallback needed")
    
    return df, fallback_info

def write_validation_report(
    output_path: str,
    status: str,
    missing_vars: List[str],
    data_content: Dict[str, Any],
    roi_fallback_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Write validation report to JSON file.
    
    Args:
        output_path: Path to output JSON file
        status: Overall validation status ('PASS', 'FAIL', 'WARN')
        missing_vars: List of missing variable names
        data_content: Data content validation results
        roi_fallback_info: Information about ROI fallback application
    """
    logger = get_logger("validate")
    
    report = {
        "status": status,
        "timestamp": pd.Timestamp.now().isoformat(),
        "missing_variables": missing_vars,
        "data_content": data_content,
        "roi_fallback_applied": roi_fallback_info["applied"] if roi_fallback_info else False,
        "roi_fallback_details": roi_fallback_info if roi_fallback_info else None
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Validation report written to {output_path}")

def validate_dataset(
    df: pd.DataFrame,
    required_vars: List[str],
    output_path: str = "data/validation_report.json",
    image_width: int = 64,
    image_height: int = 64
) -> bool:
    """
    Main validation function that checks variables, applies ROI fallback if needed,
    and writes the validation report.
    
    Args:
        df: DataFrame to validate
        required_vars: List of required variable names
        output_path: Path for the validation report
        image_width: Width of face images
        image_height: Height of face images
        
    Returns:
        True if validation passes (critical vars present), False otherwise
    """
    logger = get_logger("validate")
    
    # Check variable presence
    all_present, missing_vars = check_variable_presence(df, required_vars)
    
    # Critical variables that must be present
    critical_vars = ["gaze_coordinates", "response_times", "emotion_labels"]
    critical_missing = [v for v in missing_vars if v in critical_vars]
    
    if critical_missing:
        logger.error(f"CRITICAL: Missing required variables: {critical_missing}")
        write_validation_report(
            output_path=output_path,
            status="FAIL",
            missing_vars=missing_vars,
            data_content={},
            roi_fallback_info=None
        )
        return False
    
    # Validate data content
    data_content = validate_data_content(df, required_vars)
    
    # Apply ROI fallback if roi_annotations is missing or partially empty
    roi_fallback_info = None
    if "roi_annotations" in required_vars:
        df, roi_fallback_info = apply_roi_fallback(df, image_width, image_height)
    
    # Determine final status
    if missing_vars:
        status = "WARN"
    else:
        status = "PASS"
    
    write_validation_report(
        output_path=output_path,
        status=status,
        missing_vars=missing_vars,
        data_content=data_content,
        roi_fallback_info=roi_fallback_info
    )
    
    logger.info(f"Validation complete: {status}")
    return True

def main():
    """Main entry point for standalone execution."""
    logger = get_logger("validate")
    config = get_config()
    
    # Example usage - in real execution, data would be loaded from download.py
    logger.info("Running dataset validation with ROI fallback logic")
    
    # This would typically be called from the pipeline after download
    # For testing, we can create a minimal example
    try:
        # Check if raw data exists
        raw_data_path = Path(config.DATA_RAW_DIR) / "dataset.csv"
        if raw_data_path.exists():
            df = pd.read_csv(raw_data_path)
            required_vars = ["gaze_coordinates", "response_times", "emotion_labels", "roi_annotations"]
            success = validate_dataset(df, required_vars, output_path="data/validation_report.json")
            if not success:
                sys.exit(1)
        else:
            logger.info("No raw data found - validation skipped (expected if download not run)")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
