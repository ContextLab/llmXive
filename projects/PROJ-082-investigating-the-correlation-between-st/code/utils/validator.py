import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_effect_size(r: float, n: int) -> Tuple[bool, Optional[str]]:
    """
    Validate effect size parameters.
    
    Args:
        r: Correlation coefficient.
        n: Sample size.
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(n, int) or n <= 0:
        return False, f"Invalid sample size: {n}. Must be a positive integer."
    
    if not isinstance(r, (int, float)) or math.isnan(r) or math.isinf(r):
        return False, f"Invalid correlation coefficient: {r}. Must be a number."
    
    if not -1.0 <= r <= 1.0:
        return False, f"Correlation coefficient out of range: {r}. Must be between -1 and 1."
    
    return True, None

def validate_study_row(row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a study row from the input data.
    
    Args:
        row: Dictionary containing study data.
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    required_fields = ["study_id", "tract", "r", "n"]
    
    for field in required_fields:
        if field not in row:
            return False, f"Missing required field: {field}"
    
    is_valid_r, err_r = validate_effect_size(row.get("r"), row.get("n"))
    if not is_valid_r:
        return False, f"Invalid effect size data: {err_r}"
    
    # Validate tract name is not empty
    if not row.get("tract") or not str(row.get("tract")).strip():
        return False, "Tract name is missing or empty"
    
    return True, None

def filter_valid_studies(studies: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter a list of studies, separating valid and invalid entries.
    
    Args:
        studies: List of study dictionaries.
    
    Returns:
        Tuple of (valid_studies, invalid_studies_with_reasons).
    """
    valid = []
    invalid = []
    
    for i, study in enumerate(studies):
        is_valid, reason = validate_study_row(study)
        if is_valid:
            valid.append(study)
        else:
            invalid.append({
                "index": i,
                "study_id": study.get("study_id", f"unknown_{i}"),
                "reason": reason
            })
            log_error_context(logger, ValueError(reason), {"study_id": study.get("study_id"), "row_index": i})
    
    return valid, invalid

def validate_file_size(file_path: str, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> Tuple[bool, Optional[str]]:
    """
    Validate that a generated file does not exceed the maximum allowed size.
    
    Args:
        file_path: Path to the file to validate.
        max_size_bytes: Maximum allowed file size in bytes (default 5MB).
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File does not exist: {file_path}"
    
    file_size = path.stat().st_size
    
    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size_bytes / (1024 * 1024)
        return False, f"File size {size_mb:.2f}MB exceeds limit {max_mb}MB"
    
    logger.info(f"File validation passed: {file_path} ({file_size} bytes)")
    return True, None

def validate_generated_plots(plot_dir: str, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate all PNG files in a directory against size constraints.
    
    Args:
        plot_dir: Path to the directory containing generated plots.
        max_size_bytes: Maximum allowed file size in bytes (default 5MB).
    
    Returns:
        Tuple of (all_valid, list_of_validation_results).
    """
    dir_path = Path(plot_dir)
    
    if not dir_path.exists():
        return False, [{"directory": plot_dir, "error": "Directory does not exist"}]
    
    results = []
    all_valid = True
    
    png_files = list(dir_path.glob("*.png"))
    
    if not png_files:
        logger.warning(f"No PNG files found in {plot_dir}")
        return True, []
    
    for png_file in png_files:
        is_valid, error = validate_file_size(str(png_file), max_size_bytes)
        result = {
            "file": str(png_file),
            "size_bytes": png_file.stat().st_size,
            "valid": is_valid
        }
        if not is_valid:
            result["error"] = error
            all_valid = False
            logger.error(f"Plot validation failed: {error}")
        else:
            logger.info(f"Plot validation passed: {png_file.name} ({result['size_bytes']} bytes)")
        results.append(result)
    
    return all_valid, results

def main():
    """CLI entry point for validation utilities."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Study data and artifact validation")
    parser.add_argument("--input", help="Path to input JSON file containing studies")
    parser.add_argument("--plots", help="Path to directory containing generated plots for size validation")
    
    args = parser.parse_args()
    
    exit_code = 0
    
    if args.input:
        with open(args.input, "r") as f:
            data = json.load(f)
        
        studies = data if isinstance(data, list) else data.get("studies", [])
        
        valid, invalid = filter_valid_studies(studies)
        
        print(f"Total studies: {len(studies)}")
        print(f"Valid: {len(valid)}")
        print(f"Invalid: {len(invalid)}")
        
        if invalid:
            print("\nInvalid studies:")
            for item in invalid:
                print(f"  - {item['study_id']}: {item['reason']}")
            exit_code = 1
    
    if args.plots:
        all_valid, results = validate_generated_plots(args.plots)
        
        print(f"\nPlot Validation Results ({args.plots}):")
        for res in results:
            status = "PASS" if res["valid"] else "FAIL"
            print(f"  [{status}] {res['file']} ({res['size_bytes']} bytes)")
            if not res["valid"] and "error" in res:
                print(f"       Reason: {res['error']}")
        
        if not all_valid:
            exit_code = 1
    
    return exit_code

if __name__ == "__main__":
    import sys
    sys.exit(main())
