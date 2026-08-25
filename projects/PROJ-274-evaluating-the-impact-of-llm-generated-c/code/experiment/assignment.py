import json
import os
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure consistent logging configuration to avoid circular imports or missing handlers
# We configure a basic handler if none exists, but do not override existing root config if it has handlers
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)

# Constants for conditions
CONDITIONS = ['LLM', 'Human', 'None']

def load_participant_list(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads the list of recruited participants from a JSON file.
    
    Args:
        input_path: Path to the JSON file containing participant data.
                    If None, defaults to 'data/raw/recruited_participants.json'.
    
    Returns:
        List of participant dictionaries.
    
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    if input_path is None:
        input_path = 'data/raw/recruited_participants.json'
    
    path_obj = Path(input_path)
    if not path_obj.exists():
        logger.error(f"Participant list file not found: {input_path}")
        raise FileNotFoundError(f"Participant list file not found: {input_path}")
    
    logger.info(f"Loading participant list from {input_path}")
    with open(path_obj, 'r', encoding='utf-8') as f:
        participants = json.load(f)
    
    if not isinstance(participants, list):
        raise ValueError(f"Expected a list of participants in {input_path}, got {type(participants)}")
    
    logger.info(f"Loaded {len(participants)} participants")
    return participants

def stratified_random_assignment(participants: List[Dict[str, Any]], seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Performs stratified random assignment of participants to conditions (LLM, Human, None).
    
    This function ensures a balanced distribution across conditions. If the number of
    participants is not perfectly divisible by the number of conditions, the remainder
    is distributed randomly among the conditions.
    
    Args:
        participants: List of participant dictionaries. Each must have a 'participant_id'.
        seed: Random seed for reproducibility. If None, uses system time or global state.
    
    Returns:
        List of participant dictionaries with an added 'condition' field.
    """
    if seed is not None:
        random.seed(seed)
        logger.info(f"Random seed set to: {seed}")
    
    n_participants = len(participants)
    n_conditions = len(CONDITIONS)
    
    if n_participants == 0:
        logger.warning("No participants to assign.")
        return []
    
    # Create a list of condition slots to ensure balance
    # Each condition gets floor(N / K) slots initially
    base_count = n_participants // n_conditions
    remainder = n_participants % n_conditions
    
    condition_slots = []
    for i, cond in enumerate(CONDITIONS):
        count = base_count + (1 if i < remainder else 0)
        condition_slots.extend([cond] * count)
    
    # Shuffle the condition slots
    random.shuffle(condition_slots)
    
    # Assign conditions to participants
    assigned_participants = []
    for participant, condition in zip(participants, condition_slots):
        p_copy = participant.copy()
        p_copy['condition'] = condition
        assigned_participants.append(p_copy)
        logger.debug(f"Assigned participant {p_copy.get('participant_id', 'N/A')} to {condition}")
    
    # Verify balance (log summary)
    from collections import Counter
    counts = Counter(p['condition'] for p in assigned_participants)
    logger.info(f"Assignment complete. Distribution: {dict(counts)}")
    
    return assigned_participants

def save_assignment_log(assigned_participants: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Saves the assignment log to a JSON file.
    
    Args:
        assigned_participants: List of participant dictionaries with assigned conditions.
        output_path: Path to the output JSON file.
                    If None, defaults to 'data/processed/assignment_log.json'.
    
    Returns:
        The path to the saved file.
    
    Raises:
        OSError: If the directory cannot be created or the file cannot be written.
    """
    if output_path is None:
        output_path = 'data/processed/assignment_log.json'
    
    path_obj = Path(output_path)
    output_dir = path_obj.parent
    
    # Ensure output directory exists
    if not output_dir.exists():
        logger.info(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving assignment log to {output_path}")
    with open(path_obj, 'w', encoding='utf-8') as f:
        json.dump(assigned_participants, f, indent=2, ensure_ascii=False)
    
    logger.info("Assignment log saved successfully.")
    return output_path

def main():
    """
    Main entry point for the participant assignment script.
    Reads participants from data/raw/recruited_participants.json,
    assigns them to conditions, and saves the result to data/processed/assignment_log.json.
    """
    # Define paths
    input_path = 'data/raw/recruited_participants.json'
    output_path = 'data/processed/assignment_log.json'
    
    # Check if input file exists
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}. Cannot proceed with assignment.")
        # In a real pipeline, we might raise an exception or exit with error code
        # For this script, we raise to ensure the pipeline fails loudly as per constraints
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        # Load participants
        participants = load_participant_list(input_path)
        
        # Perform stratified random assignment
        # Using a fixed seed for reproducibility in the pipeline context
        assigned = stratified_random_assignment(participants, seed=42)
        
        # Save the assignment log
        save_assignment_log(assigned, output_path)
        
        logger.info(f"Task T014b completed successfully. Output: {output_path}")
        
    except Exception as e:
        logger.error(f"Error during participant assignment: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()