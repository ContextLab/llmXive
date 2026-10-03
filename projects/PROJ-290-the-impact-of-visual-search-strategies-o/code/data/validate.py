import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from sibling modules using exact names from API surface
from utils.logging import get_logger
from config import get_config
from features.extraction import get_roi_annotations_fallback, define_generic_roi_grid

# --- Configuration & Setup ---
CONFIG = get_config()
logger = get_logger(__name__)

# --- Core Logic: ROI Fallback ---
def apply_roi_fallback(
    df: Any,
    logger: logging.Logger,
    config: Dict[str, Any]
) -> Tuple[Any, bool]:
    """
    Applies a Generic ROI Fallback (3x3 grid) if 'roi_annotations' are missing or empty.
    
    This function checks if the 'roi_annotations' column exists and contains data.
    If missing or effectively empty, it generates a standard 3x3 grid definition
    and assigns it to the records, returning the modified dataframe and a status flag.
    
    Args:
        df: The pandas DataFrame containing raw or processed data.
        logger: The logging instance.
        config: Configuration dictionary (unused directly but passed for consistency).
        
    Returns:
        Tuple[DataFrame, bool]: The potentially modified DataFrame and a boolean 
        indicating if fallback was applied (True) or if annotations already existed (False).
    """
    if df is None:
        logger.error("Input DataFrame is None. Cannot apply ROI fallback.")
        return df, False

    # Check if column exists
    if 'roi_annotations' not in df.columns:
        logger.info("Column 'roi_annotations' not found in DataFrame. Applying Generic ROI Fallback.")
        fallback_grid = define_generic_roi_grid()
        
        # Assign the grid definition to every row
        # We assume the grid is a standard dictionary/list structure representing the 3x3 layout
        df['roi_annotations'] = [fallback_grid] * len(df)
        
        logger.info(f"Applied Generic ROI Fallback (3x3 grid) to {len(df)} records.")
        return df, True

    # Check if the column exists but contains NaN/None values
    if df['roi_annotations'].isna().all():
        logger.info("Column 'roi_annotations' exists but is entirely empty (NaN). Applying Generic ROI Fallback.")
        fallback_grid = define_generic_roi_grid()
        df['roi_annotations'] = [fallback_grid] * len(df)
        logger.info(f"Applied Generic ROI Fallback (3x3 grid) to {len(df)} records (replaced NaN).")
        return df, True
    
    # Check if there is any valid data in the column
    valid_count = df['roi_annotations'].notna().sum()
    if valid_count == 0:
        logger.info("Column 'roi_annotations' exists but contains no valid data. Applying Generic ROI Fallback.")
        fallback_grid = define_generic_roi_grid()
        df['roi_annotations'] = [fallback_grid] * len(df)
        logger.info(f"Applied Generic ROI Fallback (3x3 grid) to {len(df)} records.")
        return df, True

    # If we reach here, valid ROI annotations exist
    logger.info(f"ROI annotations found ({valid_count} valid records). No fallback needed.")
    return df, False

# --- Validation Logic ---
def check_variable_presence(df: Any, required_vars: List[str]) -> Dict[str, bool]:
    """
    Checks if required variables are present in the DataFrame.
    
    Args:
        df: The DataFrame to check.
        required_vars: List of column names to check.
        
    Returns:
        Dict mapping variable name to boolean (True if present).
    """
    if df is None:
        return {var: False for var in required_vars}
    
    return {var: var in df.columns for var in required_vars}

def validate_data_content(df: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the content of the dataset, specifically checking for critical variables.
    If critical variables are missing, it attempts to apply fallbacks (like ROI) 
    and then re-evaluates.
    
    Args:
        df: The DataFrame to validate.
        config: Configuration dictionary.
        
    Returns:
        Dict containing validation status, missing variables, and fallback info.
    """
    critical_vars = ['gaze_coordinates', 'response_times', 'emotion_labels']
    # roi_annotations is special: missing is okay if fallback can be applied
    optional_vars = ['roi_annotations']
    
    all_vars = critical_vars + optional_vars
    presence = check_variable_presence(df, all_vars)
    
    missing_critical = [var for var, present in presence.items() if var in critical_vars and not present]
    missing_optional = [var for var, present in presence.items() if var in optional_vars and not present]
    
    result = {
        "status": "pending",
        "missing_variables": missing_critical + missing_optional,
        "critical_missing": missing_critical,
        "fallback_applied": False,
        "fallback_type": None
    }
    
    # If critical vars are missing, we halt (but first check if we can fix ROI)
    if missing_critical:
        result["status"] = "failed"
        return result
    
    # Handle optional ROI annotations: apply fallback if missing
    if 'roi_annotations' in missing_optional:
        logger.warning("ROI annotations missing. Attempting Generic ROI Fallback (3x3 grid).")
        df, applied = apply_roi_fallback(df, logger, config)
        if applied:
            result["fallback_applied"] = True
            result["fallback_type"] = "generic_3x3_grid"
            result["missing_variables"].remove('roi_annotations')
            result["status"] = "success"
        else:
            result["status"] = "failed"
            result["missing_variables"].append('roi_annotations') # Ensure it's in the list
    else:
        result["status"] = "success"
        
    return result

def write_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the validation report to a JSON file.
    
    Args:
        report: The validation report dictionary.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {output_path}")

def validate_dataset(df: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for dataset validation.
    
    1. Checks for critical variables.
    2. Applies ROI fallback if necessary.
    3. Writes the report.
    4. Halts if critical variables are still missing.
    
    Args:
        df: The dataset DataFrame.
        config: Configuration dictionary.
        
    Returns:
        The final validation report.
    """
    logger.info("Starting dataset validation...")
    
    # Perform validation logic
    report = validate_data_content(df, config)
    
    # Write report to data/validation_report.json
    output_path = Path(CONFIG.data_dir) / "validation_report.json"
    write_validation_report(report, output_path)
    
    # Halt if critical variables are missing
    if report["status"] == "failed":
        error_msg = f"CRITICAL VALIDATION FAILED: Missing required variables: {report['critical_missing']}. Halting execution."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Validation successful.")
    return report

def main() -> None:
    """
    Main execution function for the validation script.
    Loads data (simulated or real path), validates, and reports.
    """
    logger.info("Running data validation pipeline...")
    
    # In a real pipeline, this would load the downloaded dataset
    # For this task implementation, we assume df is passed or loaded from a standard location
    # Since we are implementing the logic, we define the structure here.
    # In the actual pipeline, this is called by the orchestrator or a runner script.
    
    config = CONFIG
    # Placeholder for data loading - in real execution, this comes from download.py
    # df = load_raw_data() 
    
    # Example usage of the logic (if run standalone for testing):
    # This block ensures the logic is executable if a test DataFrame is provided
    try:
        # We expect the orchestrator to pass the data, but if run as __main__,
        # we might need to mock or load. For T013, the core is the function logic.
        # If this script is run directly without data, it should exit gracefully 
        # or load a test case if one exists.
        
        # Since T013 is purely about the logic implementation, we ensure the functions
        # are defined and callable. The actual invocation happens in the pipeline.
        pass
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()