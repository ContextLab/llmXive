"""
Task T017b: Markov State Validation

Verifies that `data/processed/markov_state.json` exists, contains `order == 1`,
and writes a confirmation entry to `analysis/verification_log.json`.
"""
import json
import logging
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import config utilities from the project's config module
from config import get_data_dir, get_processed_dir

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_verification_log_path() -> Path:
    """Return the path to the verification log."""
    data_dir = get_data_dir()
    analysis_dir = data_dir.parent / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    return analysis_dir / "verification_log.json"

def load_verification_log() -> Dict[str, Any]:
    """Load existing verification log or return an empty dict."""
    path = get_verification_log_path()
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_verification_log(log_data: Dict[str, Any]) -> None:
    """Save the verification log to disk."""
    path = get_verification_log_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Verification log saved to {path}")

def validate_markov_state() -> bool:
    """
    Validate the markov_state.json file.
    
    Checks:
    1. File exists at data/processed/markov_state.json
    2. File contains 'order' key with value 1
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    processed_dir = get_processed_dir()
    markov_state_path = processed_dir / "markov_state.json"
    
    logger.info(f"Checking for markov_state.json at: {markov_state_path}")
    
    if not markov_state_path.exists():
        logger.error(f"markov_state.json not found at {markov_state_path}")
        return False
    
    try:
        with open(markov_state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse markov_state.json: {e}")
        return False
    
    if 'order' not in data:
        logger.error("markov_state.json does not contain 'order' key")
        return False
    
    if data['order'] != 1:
        logger.error(f"Expected order=1, found order={data['order']}")
        return False
    
    logger.info("markov_state.json validation passed: order == 1")
    return True

def run() -> bool:
    """
    Execute the T017b validation workflow.
    
    Returns:
        bool: True if validation passed and log updated, False otherwise.
    """
    logger.info("Starting T017b: Markov State Validation")
    
    is_valid = validate_markov_state()
    
    # Load existing log
    log_data = load_verification_log()
    
    # Create or update the entry for T017b
    log_entry = {
        "task_id": "T017b",
        "description": "Markov State Validation",
        "timestamp": None, # Will be set by caller if needed, or left for external tooling
        "status": "passed" if is_valid else "failed",
        "details": {
            "file_exists": True if (get_processed_dir() / "markov_state.json").exists() else False,
            "order_value": None,
            "order_is_one": False
        }
    }
    
    if is_valid:
        log_entry["details"]["order_value"] = 1
        log_entry["details"]["order_is_one"] = True
        logger.info("Validation successful. Updating verification log.")
    else:
        logger.warning("Validation failed. Updating verification log with failure details.")
    
    log_data["T017b"] = log_entry
    save_verification_log(log_data)
    
    return is_valid

def main() -> None:
    """Main entry point for the script."""
    success = run()
    if not success:
        logger.error("T017b validation failed.")
        sys.exit(1)
    else:
        logger.info("T017b validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()