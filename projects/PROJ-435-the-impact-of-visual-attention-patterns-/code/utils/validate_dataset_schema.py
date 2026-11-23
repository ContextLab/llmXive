import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure we can import from the project root if this script is run as a module
# or directly.
def get_project_root() -> Path:
    """Get the root directory of the project."""
    # Assuming the script is in code/utils/
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

class DataInvalidError(Exception):
    """Raised when the dataset schema or ROI definitions are invalid."""
    pass

def get_required_columns() -> List[str]:
    """
    Returns the list of required columns for the raw eye-tracking dataset.
    Based on T004 task description.
    """
    return [
        'headline_text',
        'belief_rating',
        'cognitive_reflection_score',
        'fixation_duration'
    ]

def get_required_roi_definitions() -> List[str]:
    """
    Returns the list of required ROI bounding box names.
    Based on T004 task description.
    """
    return [
        'source_attribution',
        'headline_body'
    ]

def load_raw_data(input_path: Path) -> Any:
    """
    Loads the raw dataset from a Parquet file.
    Uses pandas for reading parquet files.
    """
    try:
        import pandas as pd
        return pd.read_parquet(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load raw data from {input_path}: {e}")

def validate_columns(df: Any, required_columns: List[str]) -> List[str]:
    """
    Checks if the DataFrame contains all required columns.
    Returns a list of missing columns.
    """
    if not hasattr(df, 'columns'):
        raise DataInvalidError("Loaded data does not have a 'columns' attribute.")
    
    missing = []
    for col in required_columns:
        if col not in df.columns:
            missing.append(col)
    return missing

def validate_roi_definitions(df: Any, required_rois: List[str]) -> List[str]:
    """
    Checks if the dataset contains the required ROI definitions.
    Assumes ROI definitions are stored in a column named 'roi_definitions' or similar,
    or that the dataset itself contains rows indicating ROI availability.
    
    Based on typical eye-tracking data structures in this project, ROI definitions
    are often metadata. We check if a column 'roi_definitions' exists and contains
    the required ROIs, or if the dataset has a 'roi_type' column with these values.
    
    For this implementation, we assume the raw dataset has a column 'roi_definitions'
    which is a list or string representation of available ROIs, OR we check if
    'roi_type' column exists and contains the required values.
    
    If the raw data is just gaze points, we might need to check if the 'roi_type'
    column exists and has the required values.
    """
    missing_rois = []
    
    # Strategy 1: Check if 'roi_definitions' column exists and contains the ROIs
    if 'roi_definitions' in df.columns:
        # Assuming roi_definitions is a list or JSON string
        all_rois = set()
        for val in df['roi_definitions'].dropna():
            if isinstance(val, str):
                try:
                    # Try to parse as JSON list
                    import json
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        all_rois.update(parsed)
                    else:
                        all_rois.add(val)
                except json.JSONDecodeError:
                    all_rois.add(val)
            elif isinstance(val, list):
                all_rois.update(val)
            else:
                all_rois.add(str(val))
        
        for roi in required_rois:
            if roi not in all_rois:
                missing_rois.append(roi)
    else:
        # Strategy 2: Check if 'roi_type' column exists and has the required values
        # This implies the raw data already has mapped ROIs, which might be the case
        # if the raw data is pre-processed. However, the task says "raw dataset".
        # Let's assume the raw dataset might have a 'roi_type' column with possible values.
        if 'roi_type' in df.columns:
            present_rois = set(df['roi_type'].dropna().unique())
            for roi in required_rois:
                if roi not in present_rois:
                    missing_rois.append(roi)
        else:
            # If neither column exists, we cannot verify ROIs.
            # We assume the ROIs are missing.
            missing_rois.extend(required_rois)
    
    return missing_rois

def validate_dataset_schema(df: Any, required_columns: List[str], required_rois: List[str]) -> Dict[str, Any]:
    """
    Validates the dataset schema and ROI definitions.
    Returns a dictionary with validation status and details.
    """
    missing_columns = validate_columns(df, required_columns)
    missing_rois = validate_roi_definitions(df, required_rois)
    
    is_valid = len(missing_columns) == 0 and len(missing_rois) == 0
    
    result = {
        "status": "valid" if is_valid else "invalid",
        "missing_columns": missing_columns,
        "missing_rois": missing_rois
    }
    
    return result

def write_validation_result(output_path: Path, result: Dict[str, Any]) -> None:
    """
    Writes the validation result to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logging.info(f"Validation result written to {output_path}")

def main() -> None:
    """
    Main function to run the schema validation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    project_root = get_project_root()
    input_path = project_root / 'data' / 'raw' / 'eye_tracking_raw.parquet'
    output_path = project_root / 'state' / 'schema_validation.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logging.info(f"Loading raw data from {input_path}")
    df = load_raw_data(input_path)
    
    required_columns = get_required_columns()
    required_rois = get_required_roi_definitions()
    
    logging.info(f"Validating schema for columns: {required_columns}")
    logging.info(f"Validating ROI definitions: {required_rois}")
    
    result = validate_dataset_schema(df, required_columns, required_rois)
    
    if result['status'] == 'invalid':
        error_msg = f"DataInvalidError: Missing columns: {result['missing_columns']}, Missing ROIs: {result['missing_rois']}"
        logging.error(error_msg)
        raise DataInvalidError(error_msg)
    
    write_validation_result(output_path, result)
    logging.info("Schema validation completed successfully.")

if __name__ == "__main__":
    main()