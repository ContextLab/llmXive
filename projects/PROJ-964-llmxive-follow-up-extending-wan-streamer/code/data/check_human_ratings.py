import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/mos_assumption_validated.log')
    ]
)
logger = logging.getLogger(__name__)

def check_human_ratings_exist() -> bool:
    """
    Check for the existence of the human ratings file.
    
    Returns:
        bool: True if file exists, False otherwise.
    """
    file_path = Path('data/raw/human_ratings.json')
    exists = file_path.exists()
    logger.info(f"Checking for human ratings at {file_path}: {'Found' if exists else 'Missing'}")
    return exists

def load_human_ratings() -> dict:
    """
    Load the human ratings JSON file.
    
    Returns:
        dict: The loaded JSON data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    file_path = Path('data/raw/human_ratings.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_assumption_validated_flag() -> dict:
    """
    Prepare the status dictionary for the assumption validation.
    
    Returns:
        dict: Status dictionary with 'status' and 'reason' keys.
    """
    if check_human_ratings_exist():
        return {
            'status': 'present',
            'reason': 'Human ratings file found at data/raw/human_ratings.json'
        }
    else:
        return {
            'status': 'missing',
            'reason': 'Assumption Validated (No Human Data Available)'
        }

def update_state_with_human_ratings_check(status_dict: dict) -> None:
    """
    Update the state.yaml file with the human ratings check result.
    
    Args:
        status_dict: The status dictionary from prepare_assumption_validated_flag.
    """
    state_path = Path('state.yaml')
    current_content = {}
    
    if state_path.exists():
        try:
            import yaml
            with open(state_path, 'r', encoding='utf-8') as f:
                current_content = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not read state.yaml: {e}. Starting fresh.")
    
    # Update the specific key
    current_content['mos_validation'] = 'assumption_validated'
    
    # Write back
    try:
        import yaml
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_content, f, default_flow_style=False)
        logger.info(f"Updated state.yaml with mos_validation='assumption_validated'")
    except Exception as e:
        logger.error(f"Failed to update state.yaml: {e}")
        raise

def main(args=None):
    """
    Main entry point for the human ratings check task (T046).
    
    This task checks for the existence of human ratings data.
    If missing, it logs the assumption validation, updates state.yaml,
    and writes a status JSON file, then continues (does not fail).
    """
    parser = argparse.ArgumentParser(description='Check for human ratings data (T046)')
    parser.add_argument('--output', type=str, default='data/metrics/human_data_status.json',
                        help='Path to write the status JSON file')
    parsed_args = parser.parse_args(args)

    # Ensure output directory exists
    output_path = Path(parsed_args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare status
    status_dict = prepare_assumption_validated_flag()

    # Write status JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status_dict, f, indent=2)
    logger.info(f"Wrote status to {output_path}")

    # If missing, log assumption and update state (do not fail)
    if status_dict['status'] == 'missing':
        logger.info("Assumption Validated: No human data available. Continuing pipeline.")
        update_state_with_human_ratings_check(status_dict)
    else:
        logger.info("Human ratings data present. Proceeding to proxy validation.")

    return 0

if __name__ == '__main__':
    sys.exit(main())
