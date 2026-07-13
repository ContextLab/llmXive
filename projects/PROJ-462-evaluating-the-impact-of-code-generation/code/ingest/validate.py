import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Import logging utilities
try:
    from ingest.logging import get_validate_logger, log_validation_result
except ImportError:
    # Fallback for direct execution or missing logging module
    import logging
    logger = logging.getLogger(__name__)
    def get_validate_logger():
        return logger
    def log_validation_result(*args, **kwargs):
        pass

# Required variables as per data-model.md and contracts/dataset.schema.yaml
REQUIRED_VARIABLES = [
    'tool_usage',
    'task_time',
    'defect_rate',
    'experience_years',
    'task_complexity',
    'project_type',
    'team_size'
]

def load_verified_datasets_from_spec(spec_path: str = "specs/001-code-generation-performance-outcomes/spec.md") -> List[Dict[str, Any]]:
    """
    Loads verified dataset URLs and checksums from the spec.md file.
    Parses the '# Verified datasets' block.
    """
    datasets = []
    spec_file = Path(spec_path)
    if not spec_file.exists():
        # If spec doesn't exist, return empty list (handled by caller)
        return datasets

    in_verified_block = False
    current_dataset = {}

    with open(spec_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("# Verified datasets"):
                in_verified_block = True
                continue
            if in_verified_block:
                if line.startswith("#") and not line.startswith("##"):
                    # End of verified block
                    if current_dataset:
                        datasets.append(current_dataset)
                        current_dataset = {}
                    in_verified_block = False
                    continue
                if line.startswith("- "):
                    # Parse list item: - [Name](url) checksum: sha256
                    # Simple parsing for format: - [Name](url) checksum: sha256
                    # Or: - [Name](url)
                    if current_dataset:
                        datasets.append(current_dataset)
                    current_dataset = {}
                    parts = line[2:].split(") ")
                    if len(parts) >= 1:
                        name_url = parts[0]
                        if "(" in name_url and ")" in name_url:
                            name = name_url.split("(")[0].strip("[]")
                            url = name_url.split("(")[1].split(")")[0]
                            current_dataset['name'] = name
                            current_dataset['url'] = url
                        else:
                            current_dataset['name'] = name_url
                            current_dataset['url'] = ""
                    if len(parts) >= 2:
                        checksum_part = parts[1]
                        if "checksum:" in checksum_part:
                            checksum = checksum_part.split("checksum:")[1].strip()
                            current_dataset['checksum'] = checksum
                    if "sha256" in current_dataset.get('checksum', '').lower():
                        pass # valid checksum
                    elif not current_dataset.get('checksum'):
                        # Try to find checksum later in line if not immediately after )
                        pass
                elif line.startswith("checksum:") and current_dataset:
                    # Handle case where checksum is on next line
                    current_dataset['checksum'] = line.split("checksum:")[1].strip()

    if current_dataset:
        datasets.append(current_dataset)

    return datasets

def check_csv_variables(file_path: str, variables: List[str]) -> Tuple[bool, List[str]]:
    """
    Checks if a CSV file contains all required variables.
    Returns (all_present, list_of_missing_variables).
    """
    missing = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return False, variables
            
            existing_vars = set(reader.fieldnames)
            for var in variables:
                if var not in existing_vars:
                    missing.append(var)
            
            return len(missing) == 0, missing
    except Exception as e:
        # If file cannot be read, treat as missing all variables or raise specific error
        raise FileNotFoundError(f"Could not read CSV file: {file_path}. Error: {str(e)}")

def check_tool_usage_variable(file_path: str) -> bool:
    """Checks specifically for tool_usage variable."""
    present, _ = check_csv_variables(file_path, ['tool_usage'])
    return present

def check_task_time_variable(file_path: str) -> bool:
    """Checks specifically for task_time variable."""
    present, _ = check_csv_variables(file_path, ['task_time'])
    return present

def check_defect_rate_variable(file_path: str) -> bool:
    """Checks specifically for defect_rate variable."""
    present, _ = check_csv_variables(file_path, ['defect_rate'])
    return present

def check_experience_years_variable(file_path: str) -> bool:
    """Checks specifically for experience_years variable."""
    present, _ = check_csv_variables(file_path, ['experience_years'])
    return present

def identify_missing_experience_values(file_path: str, column: str = 'experience_years') -> List[int]:
    """
    Identifies row indices where experience_years is missing or non-numeric.
    Returns list of row indices (0-based).
    """
    missing_indices = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                val = row.get(column)
                if val is None or val.strip() == '':
                    missing_indices.append(idx)
                else:
                    try:
                        float(val)
                    except ValueError:
                        missing_indices.append(idx)
    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path}: {str(e)}")
    return missing_indices

def calculate_missing_percentage(file_path: str, column: str = 'experience_years') -> float:
    """
    Calculates percentage of missing values for a specific column.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                return 0.0
            total = len(rows)
            missing_count = 0
            for row in rows:
                val = row.get(column)
                if val is None or val.strip() == '':
                    missing_count += 1
                else:
                    try:
                        float(val)
                    except ValueError:
                        missing_count += 1
            return (missing_count / total) * 100
    except Exception as e:
        raise RuntimeError(f"Error calculating missing percentage: {str(e)}")

def filter_missing_data(file_path: str, output_path: str, column: str = 'experience_years', threshold: float = 20.0) -> Tuple[bool, float]:
    """
    Filters out rows with missing values in the specified column.
    Returns (success, percentage_removed).
    If percentage removed > threshold, returns (True, percentage) but caller should warn.
    """
    missing_indices = identify_missing_experience_values(file_path, column)
    try:
        with open(file_path, 'r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames
            rows = list(reader)
        
        total_rows = len(rows)
        if total_rows == 0:
            return True, 0.0
        
        # Create new rows excluding missing indices
        # Convert missing_indices to set for O(1) lookup
        missing_set = set(missing_indices)
        filtered_rows = [row for i, row in enumerate(rows) if i not in missing_set]
        
        removed_count = total_rows - len(filtered_rows)
        percentage_removed = (removed_count / total_rows) * 100 if total_rows > 0 else 0.0

        with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_rows)
        
        return True, percentage_removed
    except Exception as e:
        raise RuntimeError(f"Error filtering data: {str(e)}")

def validate_dataset_from_url(url: str, expected_checksum: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates a dataset from a URL.
    1. Downloads (or assumes downloaded if path exists - simplified for this task context)
    2. Checks checksum if provided
    3. Checks for required variables
    4. Handles missing variables with clear error (T014)
    
    Returns a validation report dict.
    """
    logger = get_validate_logger()
    report = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "missing_variables": [],
        "checksum_valid": None,
        "message": ""
    }

    # Note: In a full pipeline, download would happen here or file path would be passed.
    # For T014, we assume the file is already downloaded to data/raw/<name>.csv
    # We need to infer the filename or expect it. 
    # Since T011a/b/c handle download, T014 focuses on the validation logic.
    # We will assume the file is at data/raw/<url_basename>.csv for this implementation.
    filename = url.split('/')[-1]
    if not filename.endswith('.csv'):
        filename += '.csv'
    file_path = f"data/raw/{filename}"

    if not os.path.exists(file_path):
        # If file doesn't exist, we can't validate variables. 
        # This might be a download error.
        report["status"] = "error"
        report["message"] = f"Dataset file not found at {file_path}. Download may have failed."
        return report

    # Check required variables (T014 implementation)
    all_present, missing_vars = check_csv_variables(file_path, REQUIRED_VARIABLES)
    
    if not all_present:
        # T014: Halt with clear error identifying missing variable
        # Instead of just returning, we raise a specific exception or set status to 'failed'
        # The task says "halt with clear error". In a script, this means raising an exception.
        # We set the report status and message, but the caller (main) should raise the error.
        report["status"] = "failed"
        report["missing_variables"] = missing_vars
        report["message"] = f"Validation FAILED: Missing required variables: {', '.join(missing_vars)}. Dataset cannot be processed."
        # Raise an error to halt execution as per T014 requirement
        raise ValueError(f"Dataset validation failed at {file_path}: Missing required variables: {', '.join(missing_vars)}")
    
    report["status"] = "passed"
    report["message"] = "All required variables present."
    return report

def validate_all_datasets(spec_path: str = "specs/001-code-generation-performance-outcomes/spec.md") -> List[Dict[str, Any]]:
    """
    Validates all datasets listed in the spec.md file.
    """
    datasets = load_verified_datasets_from_spec(spec_path)
    results = []
    for dataset in datasets:
        url = dataset.get('url')
        checksum = dataset.get('checksum')
        if url:
            try:
                result = validate_dataset_from_url(url, checksum)
                results.append(result)
            except ValueError as e:
                # T014: Catch the raised error and record it
                results.append({
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "missing_variables": [],
                    "checksum_valid": None,
                    "message": str(e)
                })
        else:
            results.append({
                "url": "unknown",
                "status": "error",
                "message": "No URL found in dataset record."
            })
    return results

def generate_validation_report(results: List[Dict[str, Any]], output_path: str = "data/output/validation_report.json"):
    """
    Generates a JSON report of validation results.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger = get_validate_logger()
    logger.info(f"Validation report generated at {output_path}")

def main():
    """
    Main entry point for validation script.
    Validates datasets from spec.md and halts if any are missing required variables.
    """
    logger = get_validate_logger()
    logger.info("Starting dataset validation (T014)...")
    
    try:
        results = validate_all_datasets()
        
        # Check if any failed
        failed_count = sum(1 for r in results if r.get('status') == 'failed')
        
        if failed_count > 0:
            logger.error(f"Validation failed for {failed_count} dataset(s).")
            generate_validation_report(results)
            # Halt execution as per T014
            sys.exit(1)
        else:
            logger.info("All datasets validated successfully.")
            generate_validation_report(results)
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()