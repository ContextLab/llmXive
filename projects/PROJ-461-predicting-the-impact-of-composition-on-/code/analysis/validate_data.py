"""
Data validation module for metallic glass dataset.

Validates that the active data source (clean_data.csv or synthetic_data.csv)
has zero missing values in the target column and valid numeric types for
all elemental mass fractions.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


def validate_numeric_types(df: pd.DataFrame, mass_fraction_columns: List[str]) -> Dict[str, Any]:
    """
    Validate that all specified mass fraction columns contain valid numeric types.
    
    Args:
        df: DataFrame to validate
        mass_fraction_columns: List of column names expected to be numeric
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "invalid_columns": [],
        "details": {}
    }
    
    for col in mass_fraction_columns:
        if col not in df.columns:
            results["valid"] = False
            results["invalid_columns"].append(col)
            results["details"][col] = "Column missing"
            logger.warning(f"Column '{col}' not found in dataset")
            continue
        
        # Check if column is numeric
        if not pd.api.types.is_numeric_dtype(df[col]):
            results["valid"] = False
            results["invalid_columns"].append(col)
            results["details"][col] = f"Non-numeric dtype: {df[col].dtype}"
            logger.warning(f"Column '{col}' has non-numeric dtype: {df[col].dtype}")
        else:
            # Check for non-finite values (inf, -inf)
            if not np.isfinite(df[col]).all():
                results["valid"] = False
                results["invalid_columns"].append(col)
                results["details"][col] = "Contains non-finite values (inf, -inf)"
                logger.warning(f"Column '{col}' contains non-finite values")
            else:
                results["details"][col] = "Valid numeric type"
                
    return results


def validate_missing_values(df: pd.DataFrame, target_column: str = "density") -> Dict[str, Any]:
    """
    Validate that the target column has zero missing values.
    
    Args:
        df: DataFrame to validate
        target_column: Name of the target column to check
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "missing_count": 0,
        "missing_percentage": 0.0
    }
    
    if target_column not in df.columns:
        results["valid"] = False
        results["missing_count"] = -1  # Indicate column missing
        results["missing_percentage"] = -1.0
        logger.error(f"Target column '{target_column}' not found in dataset")
        return results
    
    missing_count = df[target_column].isna().sum()
    total_count = len(df)
    
    results["missing_count"] = int(missing_count)
    results["missing_percentage"] = float((missing_count / total_count * 100) if total_count > 0 else 0.0)
    
    if missing_count > 0:
        results["valid"] = False
        logger.warning(f"Target column '{target_column}' has {missing_count} missing values ({results['missing_percentage']:.2f}%)")
    else:
        logger.info(f"Target column '{target_column}' has zero missing values")
        
    return results


def run_validation(data_dir: Path, config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Run full validation on the active data source and generate validation_log.json.
    
    Determines which data source to use based on validation_log.json status,
    then validates the data and writes the results to data/validation_log.json.
    
    Args:
        data_dir: Path to the data directory
        config: Optional config object (unused, for API compatibility)
        
    Returns:
        Dictionary containing validation results
    """
    logger.info("Starting data validation process")
    
    # Determine active data source
    validation_log_path = data_dir / "validation_log.json"
    active_source = "data/clean_data.csv"
    source_status = "REAL"
    
    if validation_log_path.exists():
        try:
            with open(validation_log_path, "r") as f:
                existing_log = json.load(f)
                source_status = existing_log.get("source_status", "REAL")
                
                # If synthetic was required and generated, use it
                if source_status == "SYNTHETIC_REQUIRED" or source_status == "SYNTHETIC":
                    if (data_dir / "synthetic_data.csv").exists():
                        active_source = "data/synthetic_data.csv"
                        source_status = "SYNTHETIC"
                        logger.info("Using synthetic data source as indicated by validation_log.json")
                    else:
                        logger.warning("validation_log.json indicates synthetic mode but synthetic_data.csv not found")
                else:
                    if not (data_dir / "clean_data.csv").exists():
                        logger.warning("clean_data.csv not found, checking for synthetic_data.csv")
                        if (data_dir / "synthetic_data.csv").exists():
                            active_source = "data/synthetic_data.csv"
                            source_status = "SYNTHETIC"
                            logger.info("Falling back to synthetic data source")
                        else:
                            raise FileNotFoundError("Neither clean_data.csv nor synthetic_data.csv found")
        except json.JSONDecodeError:
            logger.warning("validation_log.json is not valid JSON, assuming real data mode")
    else:
        logger.info("No existing validation_log.json found, assuming real data mode")
        
    data_path = data_dir / active_source
    
    if not data_path.exists():
        error_msg = f"Active data source not found: {data_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Validating data from: {active_source}")
    
    # Load data
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {active_source}")
    
    # Identify mass fraction columns (columns starting with 'mass_fraction_' or containing element symbols)
    # Heuristic: columns that are numeric and not the target or composition
    target_column = "density"
    all_columns = df.columns.tolist()
    potential_mass_cols = [
        col for col in all_columns 
        if col.startswith("mass_fraction_") or (col not in [target_column, "composition", "dominant_element"])
    ]
    
    # If no specific mass fraction columns found, try to detect element columns
    if not potential_mass_cols:
        # Look for columns with element symbols (2-letter or 1-letter uppercase)
        import re
        element_pattern = re.compile(r'^[A-Z][a-z]?$')
        potential_mass_cols = [
            col for col in all_columns 
            if element_pattern.match(col) and col != target_column
        ]
    
    if not potential_mass_cols:
        logger.warning("No mass fraction columns detected in dataset")
        potential_mass_cols = []
    
    # Run validations
    numeric_validation = validate_numeric_types(df, potential_mass_cols)
    missing_validation = validate_missing_values(df, target_column)
    
    # Compile results
    validation_results = {
        "source_file": active_source,
        "source_status": source_status,
        "row_count": len(df),
        "column_count": len(df.columns),
        "target_column": target_column,
        "missing_values": missing_validation,
        "numeric_types": numeric_validation,
        "overall_valid": missing_validation["valid"] and numeric_validation["valid"],
        "validation_timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Write validation log
    with open(validation_log_path, "w") as f:
        json.dump(validation_results, f, indent=2)
    
    logger.info(f"Validation complete. Results written to {validation_log_path}")
    logger.info(f"Overall validation status: {'PASSED' if validation_results['overall_valid'] else 'FAILED'}")
    
    if not validation_results["overall_valid"]:
        if not missing_validation["valid"]:
            logger.error(f"Validation failed: {missing_validation['missing_count']} missing values in target column")
        if not numeric_validation["valid"]:
            logger.error(f"Validation failed: Invalid numeric types in columns: {numeric_validation['invalid_columns']}")
    
    return validation_results


def main():
    """Main entry point for data validation."""
    from config import load_config
    
    config = load_config()
    data_dir = Path(config.data_dir)
    
    try:
        results = run_validation(data_dir)
        
        if results["overall_valid"]:
            logger.info("Data validation PASSED")
            exit(0)
        else:
            logger.error("Data validation FAILED")
            exit(1)
            
    except Exception as e:
        logger.exception(f"Data validation failed with exception: {e}")
        exit(1)


if __name__ == "__main__":
    main()
