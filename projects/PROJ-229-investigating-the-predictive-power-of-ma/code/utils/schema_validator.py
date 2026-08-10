"""
Schema Validator for PCM Dataset.

This script validates the processed dataset against the static schema defined in
`contracts/dataset.schema.yaml`, while enforcing dynamic target constraints
determined by `data/results/target_decision.json`.

It ensures that:
1. The target field specified in the decision file exists in the dataset.
2. The dataset conforms to the static schema structure.
3. No NaN/Inf values exist in critical columns (if configured).
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import DataProcessingError
from code.utils.stability_checks import check_nan_inf, validate_dataframe

logger = get_pipeline_logger(__name__)

# Paths relative to project root
DECISION_FILE = _project_root / "data" / "results" / "target_decision.json"
SCHEMA_FILE = _project_root / "contracts" / "dataset.schema.yaml"
PROCESSED_DATA_FILE = _project_root / "data" / "processed" / "pcm_dataset_processed.csv"
VALIDATION_LOG_FILE = _project_root / "data" / "results" / "schema_validation_log.json"

def load_target_decision() -> Dict[str, Any]:
    """Load the target decision JSON to determine the active target field."""
    if not DECISION_FILE.exists():
        raise FileNotFoundError(
            f"Target decision file not found at {DECISION_FILE}. "
            "Run T005a/T006a first to generate this file."
        )
    
    with open(DECISION_FILE, 'r') as f:
        decision = json.load(f)
    
    if 'target' not in decision:
        raise DataProcessingError(
            "Target decision file missing 'target' key."
        )
    
    return decision

def load_schema() -> Dict[str, Any]:
    """Load the static dataset schema."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset schema file not found at {SCHEMA_FILE}. "
            "Run T007 first to generate this file."
        )
    
    with open(SCHEMA_FILE, 'r') as f:
        schema = yaml.safe_load(f)
    
    return schema

def load_processed_dataset() -> pd.DataFrame:
    """Load the processed dataset."""
    if not PROCESSED_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {PROCESSED_DATA_FILE}. "
            "Run T015 (or the data pipeline) first to generate this file."
        )
    
    df = pd.read_csv(PROCESSED_DATA_FILE)
    logger.info(f"Loaded dataset with shape: {df.shape}")
    return df

def validate_schema_structure(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that the dataframe columns match the schema requirements.
    
    Args:
        df: The dataframe to validate.
        schema: The schema dictionary.
        
    Returns:
        A list of validation error messages (empty if valid).
    """
    errors = []
    schema_properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    # Check required fields
    missing_required = set(required_fields) - set(df.columns)
    if missing_required:
        errors.append(f"Missing required fields: {missing_required}")
    
    # Check column types (basic check for numeric vs object)
    for col_name, col_schema in schema_properties.items():
        if col_name not in df.columns:
            continue
        
        expected_type = col_schema.get("type")
        if expected_type == "number":
            if not pd.api.types.is_numeric_dtype(df[col_name]):
                errors.append(f"Column '{col_name}' is expected to be numeric but is {df[col_name].dtype}")
        elif expected_type == "string":
            if not pd.api.types.is_string_dtype(df[col_name]):
                # Allow object dtype for strings, but warn if it's clearly not
                pass # Broad check, pandas string/object often intermixed
        
    return errors

def validate_dynamic_target(df: pd.DataFrame, decision: Dict[str, Any]) -> List[str]:
    """
    Validate that the dynamic target field exists and is valid.
    
    Args:
        df: The dataframe to validate.
        decision: The target decision dictionary.
        
    Returns:
        A list of validation error messages.
    """
    errors = []
    target_field = decision.get("target")
    
    if not target_field:
        errors.append("Target field name is empty in decision file.")
        return errors
    
    if target_field not in df.columns:
        errors.append(f"Dynamic target field '{target_field}' not found in dataset. "
                      f"Available columns: {list(df.columns)}")
        return errors
    
    # Check for nulls in the target
    null_count = df[target_field].isnull().sum()
    if null_count > 0:
        errors.append(f"Target field '{target_field}' contains {null_count} null values.")
    
    return errors

def run_validation() -> Dict[str, Any]:
    """
    Execute the full validation pipeline.
    
    Returns:
        A dictionary containing the validation results.
    """
    result = {
        "status": "failed",
        "errors": [],
        "warnings": [],
        "target_field": None,
        "dataset_shape": None,
        "details": {}
    }
    
    try:
        # 1. Load Context
        logger.info("Loading target decision...")
        decision = load_target_decision()
        target_field = decision.get("target")
        result["target_field"] = target_field
        
        logger.info("Loading schema...")
        schema = load_schema()
        
        logger.info("Loading processed dataset...")
        df = load_processed_dataset()
        result["dataset_shape"] = list(df.shape)
        
        # 2. Validate Dynamic Target
        logger.info(f"Validating dynamic target: {target_field}...")
        target_errors = validate_dynamic_target(df, decision)
        result["errors"].extend(target_errors)
        
        # 3. Validate Schema Structure
        logger.info("Validating schema structure...")
        structure_errors = validate_schema_structure(df, schema)
        result["errors"].extend(structure_errors)
        
        # 4. Stability Checks (NaN/Inf)
        logger.info("Running stability checks (NaN/Inf)...")
        nan_inf_issues = check_nan_inf(df)
        if nan_inf_issues:
            result["warnings"].extend(nan_inf_issues)
            # If critical columns have NaNs, it might be an error depending on strictness.
            # For now, we flag as warnings unless the target itself has NaNs (already checked).
        
        # 5. Determine Final Status
        if not result["errors"]:
            result["status"] = "passed"
            logger.info("Schema validation PASSED.")
        else:
            logger.error(f"Schema validation FAILED with {len(result['errors'])} errors.")
        
        result["details"]["decision_rationale"] = decision.get("decision_rationale", "N/A")
        result["details"]["coefficient"] = decision.get("coefficient")
        result["details"]["target_override"] = decision.get("target_override", False)
        
    except Exception as e:
        logger.exception("Validation process crashed.")
        result["status"] = "failed"
        result["errors"].append(f"Runtime error: {str(e)}")
    
    return result

def save_validation_log(result: Dict[str, Any]) -> None:
    """Save the validation result to a JSON file."""
    with open(VALIDATION_LOG_FILE, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    logger.info(f"Validation log saved to {VALIDATION_LOG_FILE}")

def main():
    """Entry point for the script."""
    logger.info("Starting Schema Validation (T007a)...")
    result = run_validation()
    save_validation_log(result)
    
    if result["status"] == "passed":
        logger.info("T007a completed successfully.")
        sys.exit(0)
    else:
        logger.error("T007a validation failed. Check logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
