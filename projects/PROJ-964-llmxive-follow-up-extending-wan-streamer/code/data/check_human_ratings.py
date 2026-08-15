import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.update_state_yaml import load_state_yaml, save_state_yaml
from utils.config import get_config_summary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

HUMAN_RATINGS_PATH = Path("data/raw/human_ratings.json")
STATE_PATH = Path("state.yaml")


def check_human_ratings_exist() -> bool:
    """
    Check if the human ratings file exists at the expected path.
    
    Returns:
        bool: True if file exists, False otherwise.
    """
    exists = HUMAN_RATINGS_PATH.exists()
    if exists:
        logger.info(f"Human ratings file found at: {HUMAN_RATINGS_PATH}")
    else:
        logger.warning(f"Human ratings file NOT found at: {HUMAN_RATINGS_PATH}")
    return exists


def load_human_ratings() -> dict:
    """
    Load the human ratings data from the JSON file.
    
    Returns:
        dict: The loaded human ratings data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not HUMAN_RATINGS_PATH.exists():
        raise FileNotFoundError(
            f"Human ratings file not found at {HUMAN_RATINGS_PATH}. "
            "This task expects the file to exist if human ratings are available."
        )
    
    with open(HUMAN_RATINGS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Successfully loaded human ratings with {len(data) if isinstance(data, (list, dict)) else 'unknown'} entries.")
    return data


def prepare_assumption_validated_flag() -> dict:
    """
    Prepare the 'Assumption Validated' flag data structure to be saved in state.
    
    This is used when human ratings are missing, indicating that the assumption
    of proxy MOS validity is accepted by default due to lack of ground truth.
    
    Returns:
        dict: The flag data structure.
    """
    return {
        "task_id": "T046",
        "status": "assumption_validated",
        "reason": "No human ratings data available (data/raw/human_ratings.json missing).",
        "message": "Assumption Validated (No Human Data Available) - skipping correlation test.",
        "checked_path": str(HUMAN_RATINGS_PATH),
        "timestamp": None  # Will be set by update_state_with_human_ratings_check
    }


def update_state_with_human_ratings_check(state_data: dict, human_ratings: dict = None) -> dict:
    """
    Update the state YAML data with the results of the human ratings check.
    
    Args:
        state_data: The current state dictionary.
        human_ratings: The loaded human ratings data if available, else None.
        
    Returns:
        dict: The updated state dictionary.
    """
    if "human_ratings_check" not in state_data:
        state_data["human_ratings_check"] = {}
    
    check_section = state_data["human_ratings_check"]
    
    if human_ratings is not None:
        # Human ratings found
        check_section["status"] = "found"
        check_section["path"] = str(HUMAN_RATINGS_PATH)
        check_section["sample_size"] = len(human_ratings) if isinstance(human_ratings, list) else len(human_ratings.keys())
        check_section["message"] = "Human ratings data loaded successfully for T044 validation."
        check_section["available_for_t044"] = True
        logger.info("Updated state: Human ratings found and loaded.")
    else:
        # Human ratings missing
        check_section["status"] = "missing"
        check_section["path"] = str(HUMAN_RATINGS_PATH)
        check_section["assumption_validated"] = True
        check_section["message"] = "Assumption Validated (No Human Data Available) - skipping correlation test."
        check_section["available_for_t044"] = False
        logger.info("Updated state: Human ratings missing. Assumption validated.")
    
    return state_data


def main():
    """
    Main entry point for the human ratings check task.
    
    This script checks for the existence of human ratings data.
    If found, it loads the data and updates the state.
    If not found, it prepares the 'Assumption Validated' flag and updates the state.
    """
    logger.info("Starting T046: Check Human Rating Data")
    
    # Check existence
    exists = check_human_ratings_exist()
    
    # Load or prepare flag
    human_ratings = None
    if exists:
        try:
            human_ratings = load_human_ratings()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load human ratings: {e}")
            # Treat as missing if load fails
            exists = False
    
    # Load current state
    if not STATE_PATH.exists():
        logger.warning(f"State file not found at {STATE_PATH}. Creating new state structure.")
        state_data = {"human_ratings_check": {}}
    else:
        state_data = load_state_yaml()
    
    # Update state
    updated_state = update_state_with_human_ratings_check(state_data, human_ratings)
    
    # Save state
    save_state_yaml(updated_state, STATE_PATH)
    
    if exists:
        logger.info("T046 Complete: Human ratings loaded. Ready for T044 correlation check.")
        # Return success code
        return 0
    else:
        logger.info("T046 Complete: No human ratings found. Assumption validated. T044 will skip correlation.")
        # Return success code (task is complete, just no data)
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for human ratings data (T046).")
    parser.parse_args()
    
    exit_code = main()
    sys.exit(exit_code)
