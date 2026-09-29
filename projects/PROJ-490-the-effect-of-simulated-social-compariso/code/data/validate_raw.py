import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

# Import from sibling modules as per API surface
from data.config import get_config
from utils.logger import get_logger, log_execution_start, log_execution_end

# Define required variables based on task description and schema
REQUIRED_VARS = {
    "avatar_condition",
    "pre_self_esteem",
    "post_self_esteem",
    "comparison_tendency"
}

def validate_raw_directory(raw_dir: Path) -> bool:
    """
    Check if the raw data directory exists.
    """
    if not raw_dir.exists():
        logging.error(f"Raw directory does not exist: {raw_dir}")
        return False
    if not raw_dir.is_dir():
        logging.error(f"Path is not a directory: {raw_dir}")
        return False
    return True

def validate_raw_data_variables(raw_dir: Path) -> Dict[str, Any]:
    """
    Verify that data/raw contains ALL required variables BEFORE imputation.
    
    Checks for CSV/JSON files in data/raw and ensures they contain:
    - avatar_condition
    - pre_self_esteem
    - post_self_esteem
    - comparison_tendency
    
    If any are missing, it triggers synthetic data generation logic (T010)
    by returning a 'fail' status with missing variables.
    
    Returns a validation object to be written to data/processed/pre_imputation_validation.json.
    """
    logger = logging.getLogger(__name__)
    log_execution_start(logger, "validate_raw_data_variables")
    
    result = {
        "status": "pass",
        "missing_vars": [],
        "timestamp": None,
        "triggered_synthetic": False
    }
    
    # 1. Check directory existence
    if not validate_raw_directory(raw_dir):
        result["status"] = "fail"
        result["missing_vars"] = ["Raw directory missing"]
        # Write timestamp
        from datetime import datetime
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    # 2. Scan for data files
    data_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.json"))
    
    if not data_files:
        logger.warning("No CSV or JSON files found in data/raw.")
        result["status"] = "fail"
        result["missing_vars"] = ["No data files found"]
        from datetime import datetime
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    
    # 3. Check variables in the first valid data file found
    # We assume if the first file has them, the dataset is valid.
    # If the first file is empty or malformed, we try the next.
    found_valid_file = False
    all_missing = set()
    
    for file_path in data_files:
        logger.info(f"Checking file: {file_path}")
        try:
            if file_path.suffix == '.csv':
                import pandas as pd
                df = pd.read_csv(file_path)
            elif file_path.suffix == '.json':
                import pandas as pd
                df = pd.read_json(file_path)
            else:
                continue
            
            # Check columns
            current_columns = set(df.columns)
            missing_in_this_file = REQUIRED_VARS - current_columns
            
            if not missing_in_this_file:
                # All required variables found
                found_valid_file = True
                logger.info(f"All required variables found in {file_path.name}")
                break
            else:
                logger.warning(f"Missing variables in {file_path.name}: {missing_in_this_file}")
                all_missing.update(missing_in_this_file)
                
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            continue
    
    if not found_valid_file:
        result["status"] = "fail"
        result["missing_vars"] = list(all_missing) if all_missing else ["Variables missing in all files"]
        result["triggered_synthetic"] = True
        logger.warning("Required variables missing. Triggering synthetic data generation.")
    
    # 4. Add timestamp
    from datetime import datetime
    result["timestamp"] = datetime.utcnow().isoformat()
    
    log_execution_end(logger, "validate_raw_data_variables", success=(result["status"] == "pass"))
    return result

def run_validation() -> Dict[str, Any]:
    """
    Main entry point for validation task.
    """
    config = get_config()
    raw_dir = config.data_raw_path
    processed_dir = config.data_processed_path
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    validation_result = validate_raw_data_variables(raw_dir)
    
    # Write result to data/processed/pre_imputation_validation.json
    output_path = processed_dir / "pre_imputation_validation.json"
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logging.info(f"Validation result written to {output_path}")
    
    return validation_result

def main():
    """
    CLI entry point.
    """
    # Configure logging if not already done
    configure_root_logger = logging.getLogger()
    if not configure_root_logger.handlers:
        from utils.logger import configure_root_logger as setup_logger
        setup_logger()
    
    result = run_validation()
    
    if result["status"] == "fail":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
