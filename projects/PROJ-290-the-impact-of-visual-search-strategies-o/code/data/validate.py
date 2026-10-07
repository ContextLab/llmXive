import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_config
from utils.logging import get_logger

# Constants for critical variables
CRITICAL_VARS = [
    "gaze_coordinates",
    "response_times",
    "emotion_labels"
]

# ROI annotations are checked but trigger fallback if missing, not a hard halt
# unless the fallback mechanism is explicitly disabled (not implemented here)
OPTIONAL_VARS = [
    "roi_annotations"
]

def get_logger_wrapper(name: str) -> logging.Logger:
    """Wrapper to get a logger configured for this module."""
    return get_logger(name)

def check_variable_presence(data: Any, required_vars: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if the dataset contains the required variables.
    
    Args:
        data: The loaded dataset object (e.g., HuggingFace Dataset or dict of arrays).
        required_vars: List of variable names to check.
        
    Returns:
        Tuple of (all_present: bool, missing_vars: List[str])
    """
    logger = get_logger_wrapper("data.validate")
    missing = []
    
    # Determine how to check presence based on data type
    if hasattr(data, 'column_names'):
        # HuggingFace Dataset
        available = set(data.column_names)
    elif isinstance(data, dict):
        available = set(data.keys())
    elif hasattr(data, 'columns'):
        # Pandas DataFrame
        available = set(data.columns)
    else:
        logger.error(f"Unknown data type for validation: {type(data)}")
        return False, required_vars

    for var in required_vars:
        if var not in available:
            missing.append(var)
        
    return len(missing) == 0, missing

def validate_data_content(data: Any, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Perform basic content validation (non-empty, non-null checks).
    
    Args:
        data: The dataset to validate.
        logger: Logger instance.
        
    Returns:
        Dict with validation details.
    """
    if logger is None:
        logger = get_logger_wrapper("data.validate")
        
    result = {
        "is_valid": True,
        "issues": [],
        "row_count": 0,
        "column_count": 0
    }
    
    if data is None:
        result["is_valid"] = False
        result["issues"].append("Dataset is None")
        return result

    # Count rows/cols
    if hasattr(data, '__len__'):
        result["row_count"] = len(data)
    if hasattr(data, 'column_names'):
        result["column_count"] = len(data.column_names)
    elif hasattr(data, 'columns'):
        result["column_count"] = len(data.columns)
    elif isinstance(data, dict):
        result["column_count"] = len(data.keys())
        
    if result["row_count"] == 0:
        result["is_valid"] = False
        result["issues"].append("Dataset is empty (0 rows)")
        
    return result

def define_generic_roi_grid(img_width: int = 100, img_height: int = 100) -> Dict[str, List[Tuple[int, int]]]:
    """
    Define a generic 3x3 grid ROI fallback.
    
    Args:
        img_width: Width of the image.
        img_height: Height of the image.
        
    Returns:
        Dict mapping ROI names to list of (x, y) coordinates or bounding boxes.
    """
    w_step = img_width // 3
    h_step = img_height // 3
    
    rois = {
        "top_left": [(0, 0), (w_step, h_step)],
        "top_center": [(w_step, 0), (2 * w_step, h_step)],
        "top_right": [(2 * w_step, 0), (img_width, h_step)],
        "middle_left": [(0, h_step), (w_step, 2 * h_step)],
        "middle_center": [(w_step, h_step), (2 * w_step, 2 * h_step)],
        "middle_right": [(2 * w_step, h_step), (img_width, 2 * h_step)],
        "bottom_left": [(0, 2 * h_step), (w_step, img_height)],
        "bottom_center": [(w_step, 2 * h_step), (2 * w_step, img_height)],
        "bottom_right": [(2 * w_step, 2 * h_step), (img_width, img_height)]
    }
    return rois

def apply_roi_fallback(data: Any, logger: Optional[logging.Logger] = None) -> Any:
    """
    Apply generic ROI fallback if roi_annotations are missing.
    
    This modifies the dataset in place or returns a new one with generated ROI annotations.
    """
    if logger is None:
        logger = get_logger_wrapper("data.validate")
        
    logger.info("Applying Generic ROI Fallback (3x3 grid) for missing roi_annotations")
    
    # Implementation depends on data structure.
    # For HuggingFace datasets, we might need to add a new column.
    # For simplicity, we assume we can add a column or that the downstream
    # extraction logic knows to use the default grid if the column is missing.
    
    # If we need to inject a flag or default structure:
    if hasattr(data, 'column_names') and 'roi_annotations' not in data.column_names:
        # We can't easily add a complex object column to HF Dataset without processing,
        # so we rely on the extraction logic checking for the column existence.
        # We log that we are using the fallback.
        logger.warning("roi_annotations missing. Downstream extraction will use 3x3 grid fallback.")
    elif isinstance(data, dict) and 'roi_annotations' not in data:
        data['roi_annotations'] = define_generic_roi_grid()
        
    return data

def write_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Write the validation report to a JSON file.
    
    Args:
        report: The validation report dictionary.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Validation report written to {output_path}")

def validate_dataset(data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main validation function for the dataset.
    
    Args:
        data: The dataset to validate.
        config: Optional configuration dict.
        
    Returns:
        The validation report dictionary.
    """
    logger = get_logger_wrapper("data.validate")
    report = {
        "status": "unknown",
        "timestamp": None,
        "missing_critical_vars": [],
        "missing_optional_vars": [],
        "content_check": {},
        "roi_fallback_applied": False
    }
    
    # Check variable presence
    all_present, missing_critical = check_variable_presence(data, CRITICAL_VARS)
    report["missing_critical_vars"] = missing_critical
    
    _, missing_optional = check_variable_presence(data, OPTIONAL_VARS)
    report["missing_optional_vars"] = missing_optional
    
    # Content check
    report["content_check"] = validate_data_content(data, logger)
    
    # Handle ROI fallback
    if "roi_annotations" in missing_optional:
        data = apply_roi_fallback(data, logger)
        report["roi_fallback_applied"] = True
        
    # Determine final status
    if not all_present:
        report["status"] = "failed"
        logger.error(f"CRITICAL: Missing required variables: {missing_critical}")
        logger.error("HALTING execution as per FR-009.")
        # We return the report, but the main function will handle the exit
    else:
        report["status"] = "passed"
        logger.info("Validation passed. All critical variables present.")
        
    return report

def main() -> int:
    """
    Main entry point for the validation script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger = get_logger_wrapper("data.validate")
    logger.info("Starting dataset validation (T012)...")
    
    config = get_config()
    data_path = config.get("data_raw_path")
    output_path = Path(config.get("validation_report_path", "data/validation_report.json"))
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data (assuming T010 has already populated data/raw or we load from processed)
    # Since T010 downloads to data/raw, we look for the downloaded file there.
    # We need to import the download module or assume the file exists.
    # Given the pipeline, we assume the raw data file is available.
    
    try:
        from datasets import load_from_disk
        # Try to load from the raw directory
        raw_dir = Path(data_path)
        if not raw_dir.exists():
            logger.error(f"Raw data directory not found: {raw_dir}")
            return 1
            
        # Find the dataset directory (assuming T010 created a subfolder or the dataset is the root)
        # We'll look for a 'dataset' subfolder or load the first directory
        dataset_dirs = [d for d in raw_dir.iterdir() if d.is_dir()]
        if not dataset_dirs:
            logger.error(f"No dataset directories found in {raw_dir}")
            return 1
            
        # Assume the first directory is the downloaded dataset
        dataset_path = dataset_dirs[0]
        logger.info(f"Loading dataset from: {dataset_path}")
        
        dataset = load_from_disk(str(dataset_path))
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return 1
        
    # Run validation
    report = validate_dataset(dataset, config)
    
    # Write report
    write_validation_report(report, output_path)
    
    # HALT if critical vars missing
    if report["status"] == "failed":
        logger.critical("Validation failed due to missing critical variables. Halting.")
        return 1
        
    logger.info("Validation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
