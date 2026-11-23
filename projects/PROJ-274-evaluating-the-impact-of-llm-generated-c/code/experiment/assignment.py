import json
import os
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import hashlib

# Ensure project paths are set up correctly relative to the project root
# This handles the case where the script is run from the project root
# or from a subdirectory.
def _setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = _setup_logging()

def load_participant_list(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads the participant list from a JSON file.
    
    Args:
        input_path: Path to the participants_raw.json file.
        
    Returns:
        List of participant dictionaries.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading participants from {input_path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of participants in {input_path}, got {type(data)}")
        
    logger.info(f"Loaded {len(data)} participants")
    return data

def stratified_random_assignment(participants: List[Dict[str, Any]], seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Performs stratified random assignment of participants to conditions.
    
    Conditions: 'LLM', 'Human', 'None'
    Logic: 
      1. Shuffle the list of participants.
      2. Distribute them round-robin to ensure balance across conditions.
      3. If N is not divisible by 3, the extra participants are assigned
         to the first few conditions in the list order (LLM, Human, None).
    
    Args:
        participants: List of participant dictionaries.
        seed: Optional random seed for reproducibility.
        
    Returns:
        List of participant dictionaries with an added 'condition' field.
    """
    if seed is not None:
        random.seed(seed)
        logger.info(f"Random seed set to {seed}")
    else:
        logger.info("No seed provided, using system random state")

    conditions = ['LLM', 'Human', 'None']
    n = len(participants)
    
    if n == 0:
        logger.warning("No participants to assign.")
        return []

    # Shuffle participants to ensure randomness before assignment
    shuffled = participants.copy()
    random.shuffle(shuffled)
    
    assigned = []
    for i, participant in enumerate(shuffled):
        # Round-robin assignment to ensure balance
        condition = conditions[i % len(conditions)]
        participant_copy = participant.copy()
        participant_copy['condition'] = condition
        assigned.append(participant_copy)
        logger.debug(f"Assigned participant {participant.get('id', 'unknown')} to {condition}")

    # Verify balance
    counts = {c: 0 for c in conditions}
    for p in assigned:
        counts[p['condition']] += 1
    
    logger.info(f"Assignment complete. Distribution: {counts}")
    return assigned

def save_assignment_log(assignment_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the assignment log to a JSON file.
    
    Args:
        assignment_data: List of assigned participant dictionaries.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving assignment log to {output_path}")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(assignment_data, f, indent=2)
    
    # Calculate checksum for integrity
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    logger.info(f"Assignment log saved. SHA256: {checksum}")

def main():
    """
    Main entry point for the participant assignment script.
    Reads from data/raw/participants_raw.json and writes to data/processed/assignment_log.json.
    """
    # Define paths relative to project root
    # Assuming script is run from project root: python code/experiment/assignment.py
    project_root = Path(__file__).resolve().parent.parent.parent
    input_file = project_root / "data" / "raw" / "participants_raw.json"
    output_file = project_root / "data" / "processed" / "assignment_log.json"
    
    # Allow overriding via environment variables for testing
    if os.getenv('ASSIGNMENT_INPUT'):
        input_file = Path(os.getenv('ASSIGNMENT_INPUT'))
    if os.getenv('ASSIGNMENT_OUTPUT'):
        output_file = Path(os.getenv('ASSIGNMENT_OUTPUT'))

    try:
        # Load participants
        participants = load_participant_list(str(input_file))
        
        # Assign conditions
        # Using a fixed seed for reproducibility as per Constitution Principle I (T004)
        # unless overridden by environment variable
        seed = int(os.getenv('ASSIGNMENT_SEED', '42'))
        assigned_participants = stratified_random_assignment(participants, seed=seed)
        
        # Save results
        save_assignment_log(assigned_participants, str(output_file))
        
        logger.info("Assignment task completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during assignment: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
