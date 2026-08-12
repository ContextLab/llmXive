import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config import load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def validate_numeric_types(df: pd.DataFrame, composition_col: str = "composition") -> Dict[str, Any]:
    """
    Validates that all mass fractions within the composition column are numeric.
    Returns a dict with 'valid' (bool) and 'errors' (list of strings).
    """
    errors = []
    valid = True
    
    if composition_col not in df.columns:
        errors.append(f"Column '{composition_col}' not found in DataFrame.")
        return {"valid": False, "errors": errors}

    # Check if composition is a string representation of a dict or actual dict
    # We assume it might be a string like "{'Fe': 0.5, 'B': 0.5}" or a dict
    for idx, row in df.iterrows():
        comp = row[composition_col]
        if isinstance(comp, str):
            try:
                # Attempt to parse if it's a string representation
                # In a real scenario, we might use ast.literal_eval, but for safety in this context
                # we assume the preprocessing step already handled parsing or it's a dict.
                # If it's a string that isn't a dict, this is a format error.
                import ast
                comp = ast.literal_eval(comp)
            except (ValueError, SyntaxError):
                errors.append(f"Row {idx}: Composition string could not be parsed.")
                valid = False
                continue
        
        if not isinstance(comp, dict):
            errors.append(f"Row {idx}: Composition is not a dictionary.")
            valid = False
            continue

        for elem, val in comp.items():
            if not isinstance(val, (int, float, np.number)):
                errors.append(f"Row {idx}: Mass fraction for '{elem}' is not numeric ({type(val).__name__}).")
                valid = False
                break
    
    return {"valid": valid, "errors": errors}

def validate_missing_values(df: pd.DataFrame, target_col: str = "density") -> Dict[str, Any]:
    """
    Validates that the target column has zero missing values.
    Returns a dict with 'valid' (bool), 'missing_count' (int), and 'total_rows' (int).
    """
    if target_col not in df.columns:
        return {"valid": False, "missing_count": -1, "total_rows": len(df), "error": f"Target column '{target_col}' not found."}

    missing_count = df[target_col].isna().sum()
    total_rows = len(df)
    
    return {
        "valid": missing_count == 0,
        "missing_count": int(missing_count),
        "total_rows": total_rows
    }

def run_validation(data_path: Path, target_col: str = "density", composition_col: str = "composition") -> Dict[str, Any]:
    """
    Runs all validation checks on the provided data file.
    Returns a comprehensive validation report.
    """
    logger.info(f"Starting validation for {data_path}")
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return {
            "status": "error",
            "message": f"File not found: {data_path}",
            "row_count": 0,
            "missing_target": -1,
            "valid_types": False
        }

    try:
        # Load data
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {
            "status": "error",
            "message": str(e),
            "row_count": 0,
            "missing_target": -1,
            "valid_types": False
        }

    # Run validators
    missing_stats = validate_missing_values(df, target_col)
    type_stats = validate_numeric_types(df, composition_col)

    # Determine overall status
    is_valid = missing_stats["valid"] and type_stats["valid"]
    status = "passed" if is_valid else "failed"

    report = {
        "status": status,
        "source_file": str(data_path),
        "row_count": missing_stats["total_rows"],
        "missing_target_count": missing_stats["missing_count"],
        "target_column_valid": missing_stats["valid"],
        "composition_types_valid": type_stats["valid"],
        "composition_errors": type_stats["errors"],
        "timestamp": pd.Timestamp.now().isoformat()
    }

    logger.info(f"Validation {status}: {missing_stats['total_rows']} rows, {missing_stats['missing_count']} missing targets")
    
    return report

def main():
    """
    Entry point for the validation script.
    Reads config, locates the data file, runs validation, and saves the log.
    """
    config = load_config()
    data_dir = config.data_dir
    output_dir = data_dir  # Output log to data directory as per task spec
    
    # Determine which file to validate: clean_data.csv or synthetic_data.csv
    clean_path = data_dir / "clean_data.csv"
    synthetic_path = data_dir / "synthetic_data.csv"
    
    target_file = None
    source_status = "missing"
    
    if clean_path.exists():
        target_file = clean_path
        source_status = "clean_data"
    elif synthetic_path.exists():
        target_file = synthetic_path
        source_status = "synthetic_data"
    else:
        logger.error("Neither clean_data.csv nor synthetic_data.csv found.")
        # Create a failure log anyway
        error_report = {
            "status": "error",
            "message": "No data file found to validate",
            "source_status": "missing",
            "row_count": 0,
            "missing_target_count": -1,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        log_path = output_dir / "validation_log.json"
        with open(log_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        return 1

    logger.info(f"Validating {target_file.name} (Source: {source_status})")
    
    report = run_validation(target_file, target_col="density", composition_col="composition")
    report["source_status"] = source_status

    log_path = output_dir / "validation_log.json"
    with open(log_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation log saved to {log_path}")
    
    if report["status"] != "passed":
        logger.warning("Validation failed. Check validation_log.json for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
