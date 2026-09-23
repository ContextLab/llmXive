"""
Module: validate_raw.py
Task: T013a - Pre-Imputation Variable Check
Description: Verifies that data/raw contains ALL required variables before imputation.
             If any are missing, it triggers the synthetic data generator (T010).
             Writes validation status to data/processed/pre_imputation_validation.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.config import get_config
from utils.logger import get_logger, log_execution_start, log_execution_end
from data.download import generate_synthetic_dataset, write_state_decision

REQUIRED_VARIABLES = {
    "avatar_condition",
    "pre_self_esteem",
    "post_self_esteem",
    "comparison_tendency"
}

logger = get_logger(__name__)

def validate_raw_directory(raw_dir: Path) -> bool:
    """
    Checks if the raw directory contains any data files.
    Returns True if at least one .csv file is found, False otherwise.
    """
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return False
    
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in raw data directory: {raw_dir}")
        return False
    
    logger.info(f"Found {len(csv_files)} CSV file(s) in raw directory.")
    return True

def validate_raw_data_variables(data_dir: Path) -> Dict[str, Any]:
    """
    Validates that the data in data/raw contains all required variables.
    If missing, triggers synthetic data generation.
    
    Returns:
        Dict containing validation status and details.
    """
    config = get_config()
    raw_dir = config.paths.raw_data
    processed_dir = config.paths.processed_data
    state_dir = config.paths.state

    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    validation_result = {
        "status": "pass",
        "missing_vars": [],
        "timestamp": datetime.utcnow().isoformat(),
        "triggered_synthetic": False,
        "source_file": None
    }

    # Check if raw directory has data
    if not validate_raw_directory(raw_dir):
        logger.info("No real data found. Triggering synthetic data generation.")
        validation_result["status"] = "fail"
        validation_result["missing_vars"] = list(REQUIRED_VARIABLES)
        validation_result["reason"] = "No data files found in data/raw"
        # Trigger synthetic generation
        _trigger_synthetic_fallback(config, validation_result, state_dir)
        return validation_result

    # Load the first available CSV to check variables
    csv_files = list(raw_dir.glob("*.csv"))
    # Skip seed files if they exist in raw (though they should be json)
    data_files = [f for f in csv_files if not f.name.endswith("_seed.csv")]
    
    if not data_files:
        logger.warning("No valid data CSVs found (excluding seeds).")
        validation_result["status"] = "fail"
        validation_result["missing_vars"] = list(REQUIRED_VARIABLES)
        validation_result["reason"] = "No valid data CSVs found"
        _trigger_synthetic_fallback(config, validation_result, state_dir)
        return validation_result

    # Check the first data file for variables
    # In a real scenario, we might check all, but schema consistency is expected
    sample_file = data_files[0]
    validation_result["source_file"] = sample_file.name
    
    try:
        df = pd.read_csv(sample_file)
    except Exception as e:
        logger.error(f"Failed to read CSV {sample_file}: {e}")
        validation_result["status"] = "fail"
        validation_result["missing_vars"] = list(REQUIRED_VARIABLES)
        validation_result["reason"] = f"Failed to read data file: {e}"
        _trigger_synthetic_fallback(config, validation_result, state_dir)
        return validation_result

    current_vars = set(df.columns)
    missing_vars = REQUIRED_VARIABLES - current_vars

    if missing_vars:
        logger.warning(f"Missing required variables in {sample_file.name}: {missing_vars}")
        validation_result["status"] = "fail"
        validation_result["missing_vars"] = list(missing_vars)
        validation_result["reason"] = f"Missing variables: {', '.join(missing_vars)}"
        _trigger_synthetic_fallback(config, validation_result, state_dir)
    else:
        logger.info("All required variables present in raw data.")
        validation_result["status"] = "pass"
        validation_result["missing_vars"] = []

    # Write validation result to disk
    output_path = processed_dir / "pre_imputation_validation.json"
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation result written to {output_path}")
    return validation_result

def _trigger_synthetic_fallback(config, validation_result, state_dir):
    """
    Internal helper to trigger synthetic data generation when validation fails.
    """
    logger.info("Initiating synthetic data fallback generation...")
    
    try:
        # Generate synthetic dataset
        synthetic_df = generate_synthetic_dataset(n_samples=150) # N >= 100
        
        # Save synthetic data to raw
        synthetic_path = config.paths.raw_data / "synthetic_data.csv"
        synthetic_df.to_csv(synthetic_path, index=False)
        logger.info(f"Synthetic data saved to {synthetic_path}")
        
        # Update state decision
        write_state_decision(
            decision="synthetic",
            reason=validation_result.get("reason", "Missing variables triggered fallback"),
            source="synthetic_generator"
        )
        
        validation_result["triggered_synthetic"] = True
        validation_result["missing_vars"] = [] # Now present in synthetic
        validation_result["status"] = "pass" # After generation, it passes
        
        # Re-write the validation result to reflect the fix
        output_path = config.paths.processed_data / "pre_imputation_validation.json"
        with open(output_path, 'w') as f:
            json.dump(validation_result, f, indent=2)
        
        logger.info("Synthetic data generation and state update completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        validation_result["triggered_synthetic"] = False
        # Do not change status, it remains fail
        raise e

def run_validation():
    """
    Entry point for the validation task.
    """
    log_execution_start("T013a", "Pre-Imputation Variable Check")
    try:
        result = validate_raw_data_variables(Path("data"))
        log_execution_end("T013a", success=(result["status"] == "pass"))
        return result
    except Exception as e:
        logger.exception("Validation failed with exception")
        log_execution_end("T013a", success=False, error=str(e))
        raise

def main():
    """
    CLI entry point.
    """
    run_validation()

if __name__ == "__main__":
    main()
