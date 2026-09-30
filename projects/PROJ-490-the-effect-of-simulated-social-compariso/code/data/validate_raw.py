import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.config import get_config
from utils.logger import get_logger, log_execution_start, log_execution_end
from utils.validators import DataFetchError

# Required variables for the study
REQUIRED_VARS = {
    "avatar_condition",
    "pre_self_esteem",
    "post_self_esteem",
    "comparison_tendency"
}

logger = get_logger(__name__)

def validate_raw_directory(raw_dir: Path) -> bool:
    """
    Check if the raw data directory exists and contains files.
    """
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return False
    
    files = list(raw_dir.glob("*"))
    if not files:
        logger.warning(f"Raw data directory is empty: {raw_dir}")
        return False
    
    logger.info(f"Found {len(files)} file(s) in raw directory.")
    return True

def validate_raw_data_variables(data_path: Path) -> Dict[str, Any]:
    """
    Load the data file (CSV) from the raw directory and verify it contains
    all required variables: avatar_condition, pre_self_esteem, post_self_esteem, comparison_tendency.
    
    Returns a validation object:
    {
        "status": "pass" | "fail",
        "missing_vars": [],
        "timestamp": "ISO8601",
        "file": "path_to_file"
    }
    
    If variables are missing, it triggers the synthetic generation path (T010)
    by raising a specific error or returning a status that the main loop handles.
    """
    import pandas as pd
    from datetime import datetime

    # Find CSV files in raw_dir
    csv_files = list(data_path.glob("*.csv"))
    
    if not csv_files:
        logger.error(f"No CSV files found in {data_path}")
        return {
            "status": "fail",
            "missing_vars": list(REQUIRED_VARS),
            "timestamp": datetime.utcnow().isoformat(),
            "file": None,
            "reason": "No CSV files found"
        }

    # Assume the first CSV is the data file (or the one matching expected naming if known)
    # In a real scenario, we might look for specific names, but T012 saves the output.
    # We'll try to load the first one found.
    data_file = csv_files[0]
    logger.info(f"Validating variables in: {data_file}")

    try:
        df = pd.read_csv(data_file)
    except Exception as e:
        logger.error(f"Failed to read CSV {data_file}: {e}")
        return {
            "status": "fail",
            "missing_vars": list(REQUIRED_VARS),
            "timestamp": datetime.utcnow().isoformat(),
            "file": str(data_file),
            "reason": f"Read error: {str(e)}"
        }

    actual_vars = set(df.columns)
    missing = REQUIRED_VARS - actual_vars

    result = {
        "status": "pass" if not missing else "fail",
        "missing_vars": list(missing),
        "timestamp": datetime.utcnow().isoformat(),
        "file": str(data_file),
        "row_count": len(df)
    }

    if missing:
        logger.error(f"Missing required variables: {missing}")
        logger.error("Triggering synthetic data generation path.")
        # We do NOT raise an exception here to allow the caller (main.py) to handle the flow,
        # but we return the fail status which main.py will interpret to trigger T010.
    else:
        logger.info("All required variables present.")

    return result

def run_validation() -> Dict[str, Any]:
    """
    Orchestrates the validation of the raw data directory.
    Writes the result to data/processed/pre_imputation_validation.json.
    """
    log_execution_start(logger, "T013a")
    
    config = get_config()
    raw_dir = config.raw_data_dir
    processed_dir = config.processed_data_dir

    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Check directory existence
    if not validate_raw_directory(raw_dir):
        # If directory doesn't exist, we can't validate variables.
        # This implies we need to generate data first, but T012 should have run.
        # We'll treat this as a fail.
        validation_result = {
            "status": "fail",
            "missing_vars": list(REQUIRED_VARS),
            "timestamp": datetime.utcnow().isoformat(),
            "file": None,
            "reason": "Raw directory missing or empty"
        }
    else:
        # Step 2: Check variables
        validation_result = validate_raw_data_variables(raw_dir)

    # Step 3: Write output artifact
    output_path = processed_dir / "pre_imputation_validation.json"
    try:
        with open(output_path, "w") as f:
            json.dump(validation_result, f, indent=2)
        logger.info(f"Validation result written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write validation result: {e}")
        raise

    log_execution_end(logger, "T013a")
    return validation_result

def main():
    """
    Entry point for the validation script.
    """
    try:
        result = run_validation()
        if result["status"] == "fail":
            # In the context of the pipeline, if this fails, main.py should trigger T010.
            # We return a non-zero exit code to signal failure to the orchestrator if needed,
            # but the artifact is written so the state is recorded.
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Validation failed with exception: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()