import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import get_logger, log_error_context

def validate_effect_size(effect_size: float, min_val: float = -1.0, max_val: float = 1.0) -> bool:
    """
    Validate that an effect size is within acceptable bounds.
    
    Args:
        effect_size: Effect size value to validate
        min_val: Minimum allowed value (default -1.0 for correlation)
        max_val: Maximum allowed value (default 1.0 for correlation)
        
    Returns:
        True if valid, False otherwise
    """
    if math.isnan(effect_size) or math.isinf(effect_size):
        return False
    return min_val <= effect_size <= max_val

def validate_study_row(row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a study row from extracted data.
    
    Args:
        row: Dictionary containing study data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    logger = get_logger(__name__)
    
    # Check required fields
    required_fields = ["study_id", "effect_size"]
    for field in required_fields:
        if field not in row:
            error_msg = f"Missing required field: {field}"
            logger.error(error_msg)
            return False, error_msg
    
    # Validate effect size
    if not validate_effect_size(row["effect_size"]):
        error_msg = f"Invalid effect size: {row['effect_size']}"
        logger.error(error_msg)
        return False, error_msg
    
    # Validate sample size if present
    if "n" in row:
        if not isinstance(row["n"], (int, float)) or row["n"] <= 0:
            error_msg = f"Invalid sample size: {row['n']}"
            logger.error(error_msg)
            return False, error_msg
    
    return True, None

def filter_valid_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter a list of studies to include only valid ones.
    
    Args:
        studies: List of study dictionaries
        
    Returns:
        List of valid study dictionaries
    """
    logger = get_logger(__name__)
    valid_studies = []
    
    for study in studies:
      is_valid, error_msg = validate_study_row(study)
      if is_valid:
          valid_studies.append(study)
      else:
          logger.warning(f"Skipping invalid study: {study.get('study_id', 'unknown')} - {error_msg}")
    
    return valid_studies

def validate_file_size(file_path: Union[str, Path], max_size_mb: float = 5.0) -> Tuple[bool, Optional[str]]:
    """
    Validate that a file size is within acceptable limits.
    
    Args:
        file_path: Path to file
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    logger = get_logger(__name__)
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return False, error_msg
    
    file_size_bytes = path_obj.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        error_msg = f"File size {file_size_mb:.2f}MB exceeds limit of {max_size_mb}MB"
        logger.error(error_msg)
        return False, error_msg
    
    return True, None

def validate_generated_plots(plot_dir: Union[str, Path], max_size_mb: float = 5.0) -> Dict[str, Any]:
    """
    Validate all plots in a directory.
    
    Args:
        plot_dir: Directory containing plot files
        max_size_mb: Maximum allowed file size per plot
        
    Returns:
        Validation report dictionary
    """
    logger = get_logger(__name__)
    dir_path = Path(plot_dir)
    
    if not dir_path.exists():
        return {
            "valid": False,
            "error": f"Directory not found: {plot_dir}",
            "plots_validated": 0
        }
    
    plot_files = list(dir_path.glob("*.png"))
    validation_results = []
    all_valid = True
    
    for plot_file in plot_files:
        is_valid, error_msg = validate_file_size(plot_file, max_size_mb)
        validation_results.append({
            "file": str(plot_file.name),
            "valid": is_valid,
            "error": error_msg
        })
        if not is_valid:
            all_valid = False
    
    return {
        "valid": all_valid,
        "plots_validated": len(plot_files),
        "results": validation_results
    }

def main():
    """
    Entry point for validator utility testing.
    """
    logger = get_logger(__name__)
    logger.info("Validator utility module loaded successfully.")

if __name__ == "__main__":
    main()
