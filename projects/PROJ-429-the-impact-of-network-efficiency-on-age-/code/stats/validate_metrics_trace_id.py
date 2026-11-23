import os
import sys
import logging
import json
import re
from pathlib import Path

# Add project root to path to allow relative imports if needed, 
# though this script primarily uses standard library and pandas if available
# We will implement the logic directly to avoid circular dependencies or missing imports.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def validate_trace_id_format(trace_id: str) -> bool:
    """
    Validates if a string is a valid SHA-256 hex string.
    SHA-256 produces a 64-character hexadecimal string.
    """
    if not isinstance(trace_id, str):
        return False
    # Regex for 64 hex characters
    pattern = r'^[a-fA-F0-9]{64}$'
    return bool(re.match(pattern, trace_id))

def validate_metrics_trace_ids(csv_path: Path) -> dict:
    """
    Validates the trace_id column in the network_metrics.csv file.
    
    Returns a dictionary with validation results:
    {
        "file_exists": bool,
        "column_exists": bool,
        "total_rows": int,
        "valid_count": int,
        "invalid_count": int,
        "sample_invalid_ids": list,
        "status": "PASS" | "FAIL" | "WARNING"
    }
    """
    result = {
        "file_exists": False,
        "column_exists": False,
        "total_rows": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "sample_invalid_ids": [],
        "status": "FAIL"
    }

    # Check if file exists
    if not csv_path.exists():
        logger.warning(f"File not found: {csv_path}")
        result["status"] = "WARNING" # Task says exit 0, log warning
        return result

    result["file_exists"] = True

    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
    except ImportError:
        logger.error("Pandas is required to read the CSV file.")
        result["status"] = "FAIL"
        return result
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        result["status"] = "FAIL"
        return result

    result["total_rows"] = len(df)

    # Check if 'trace_id' column exists
    if 'trace_id' not in df.columns:
        logger.error("Column 'trace_id' not found in the CSV file.")
        result["status"] = "FAIL"
        return result

    result["column_exists"] = True

    # Validate each trace_id
    invalid_ids = []
    for idx, row in df.iterrows():
        tid = row['trace_id']
        if not validate_trace_id_format(tid):
            invalid_ids.append(tid)
    
    result["valid_count"] = result["total_rows"] - len(invalid_ids)
    result["invalid_count"] = len(invalid_ids)
    
    # Store up to 5 sample invalid IDs for inspection
    result["sample_invalid_ids"] = invalid_ids[:5]

    if result["invalid_count"] == 0:
        result["status"] = "PASS"
        logger.info(f"Validation PASSED: All {result['total_rows']} trace_ids are valid SHA-256 hex strings.")
    else:
        result["status"] = "FAIL"
        logger.warning(f"Validation FAILED: Found {result['invalid_count']} invalid trace_ids out of {result['total_rows']}.")

    return result

def main():
    # Define path relative to project root
    # Assuming script runs from project root or code/stats/
    project_root = Path(__file__).resolve().parent.parent.parent
    csv_path = project_root / "data" / "results" / "network_metrics.csv"

    logger.info(f"Validating trace_id column in: {csv_path}")
    
    validation_result = validate_metrics_trace_ids(csv_path)
    
    # Log final status
    logger.info(f"Validation Status: {validation_result['status']}")
    
    # If file is missing, we log warning and exit 0 as per task requirements
    if not validation_result['file_exists']:
        logger.warning("File missing. Exiting with code 0 as per task requirements.")
        sys.exit(0)
    
    # If validation fails, we still exit 0 for this specific task (T019) 
    # because it is a validation task, but the status is recorded.
    # However, typically a failed validation might warrant a non-zero exit in a pipeline.
    # The task says: "If file is missing or empty... log warning and exit 0".
    # It doesn't explicitly say exit 0 on validation failure, but T019 is a validator.
    # To be safe and consistent with "do not block", we exit 0 but report status.
    # If the pipeline requires strict failure, the caller (T020) would handle it.
    
    # Save detailed result to a JSON file for downstream tasks
    output_path = project_root / "data" / "results" / "trace_id_validation_report.json"
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation report saved to: {output_path}")
    
    # Exit 0 regardless of validation pass/fail to avoid blocking the pipeline 
    # if the file simply hasn't been generated yet (T008_run might not have run).
    # The task description implies this task is a check, not a gate that stops execution 
    # if the upstream file is missing.
    sys.exit(0)

if __name__ == "__main__":
    main()