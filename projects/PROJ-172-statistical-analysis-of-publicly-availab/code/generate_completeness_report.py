import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from config import ensure_directories
from utils.logging import get_logger, log_info, log_error

# Import the validation function from the existing data_validation module
# This ensures we use the same logic that T016a implemented
from data_validation import validate_data_completeness

logger = get_logger(__name__)

PROCESSED_DATA_PATH = Path("data/processed/processed_games.csv")
REPORT_OUTPUT_PATH = Path("artifacts/reports/data_completeness_report.json")

def load_processed_data() -> Optional[Dict[str, Any]]:
    """
    Load the processed dataset and metadata required for the completeness report.
    Returns None if the file does not exist or cannot be loaded.
    """
    if not PROCESSED_DATA_PATH.exists():
        log_error(f"Processed data file not found: {PROCESSED_DATA_PATH}")
        return None

    try:
        # We expect a JSON file containing the dataframe stats or a path to the CSV
        # based on the pipeline flow. If it's a CSV, we might need to load it again
        # or rely on the validation module to handle the path.
        # For robustness, we attempt to load the JSON state first, then fall back to CSV analysis.
        state_file = Path("state/data_state.json")
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
                # Check if we have metadata about the last run
                if 'completeness_stats' in state:
                    return state['completeness_stats']
        
        # If no state, we assume the CSV exists and we need to re-calculate
        # This matches the behavior of T016a which likely wrote to state or returned values
        # We will call the validation function which handles the CSV
        return None 
    except Exception as e:
        log_error(f"Error loading processed data state: {e}")
        return None

def generate_report() -> Dict[str, Any]:
    """
    Generate the data completeness report artifact.
    
    This function:
    1. Loads the processed data (or stats from state).
    2. Calls validate_data_completeness to get the rate and flags.
    3. Constructs the JSON report.
    4. Writes it to artifacts/reports/data_completeness_report.json.
    
    Returns the report dictionary.
    """
    log_info("Generating data completeness report...")
    
    # Ensure output directory exists
    ensure_directories([REPORT_OUTPUT_PATH.parent])

    # Attempt to load existing stats from state first (if T016a wrote them there)
    state_path = Path("state/data_state.json")
    existing_stats = None
    
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
                if 'completeness_stats' in state:
                    existing_stats = state['completeness_stats']
                    log_info("Found existing completeness stats in state.")
        except Exception as e:
            log_error(f"Could not read state file: {e}")

    # If we don't have stats, we must re-run validation against the CSV
    if existing_stats is None:
        log_info("Re-calculating completeness stats from CSV...")
        if not PROCESSED_DATA_PATH.exists():
            raise FileNotFoundError(
                f"Processed data file {PROCESSED_DATA_PATH} not found. "
                "Ensure T015 (temporal split) and previous pipeline steps have run."
            )
        
        # Call the validation function defined in T016a
        # This function returns a dict with 'completeness_rate', 'is_real_data', etc.
        try:
            validation_result = validate_data_completeness(PROCESSED_DATA_PATH)
            existing_stats = validation_result
        except ValueError as e:
            # T016a raises ValueError if completeness < 95% and is_real_data is True.
            # We catch it here to still generate the report but flag the failure.
            log_error(f"Data completeness check failed: {e}")
            # Construct a partial report indicating the failure
            existing_stats = {
                "completeness_rate": 0.0,
                "required_threshold": 0.95,
                "is_real_data": True,
                "status": "FAILED_THRESHOLD",
                "error_message": str(e)
            }
        except Exception as e:
            log_error(f"Unexpected error during validation: {e}")
            raise

    # Construct the final report structure
    report = {
        "artifact_type": "data_completeness_report",
        "generated_at": None, # Will be set by caller or left for timestamp if needed
        "data_source": str(PROCESSED_DATA_PATH),
        "completeness_rate": existing_stats.get("completeness_rate", 0.0),
        "required_threshold": 0.95,
        "is_real_data": existing_stats.get("is_real_data", False),
        "empirical_hypothesis_untested": existing_stats.get("empirical_hypothesis_untested", False),
        "status": existing_stats.get("status", "UNKNOWN"),
        "details": existing_stats.get("details", {})
    }

    # Write the report to disk
    with open(REPORT_OUTPUT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    log_info(f"Data completeness report written to {REPORT_OUTPUT_PATH}")
    
    return report

def main():
    """
    Entry point for the script.
    """
    try:
        report = generate_report()
        print(json.dumps(report, indent=2))
        return 0
    except Exception as e:
        log_error(f"Failed to generate completeness report: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
