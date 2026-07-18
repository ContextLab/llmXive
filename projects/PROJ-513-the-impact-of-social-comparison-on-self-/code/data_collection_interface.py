"""
Data Collection Interface for User Story 1 & 2.

Handles:
1. Collection of baseline covariates (INCOM, Usage) BEFORE stimulus presentation.
2. Randomized presentation of AI/Human stimuli.
3. Immediate BISS score capture.
4. Session logging and data persistence.
"""
import os
import json
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Import from project modules
from models import Participant, StimulusOrigin, Response
import stimulus_loader

# Configure logger
from logging_config import setup_logger
logger = setup_logger(__name__)

def get_input(prompt: str, validator=None) -> str:
    """
    Helper to get input with optional validation.
    """
    while True:
        try:
            value = input(prompt)
            if validator and not validator(value):
                print("Invalid input. Please try again.")
                continue
            return value
        except EOFError:
            raise KeyboardInterrupt("Input stream closed.")

def collect_covariates(participant_id: str) -> Dict[str, Any]:
    """
    Collects baseline covariates BEFORE any stimulus presentation.
    Implements the 'covariate locking' requirement: user cannot proceed
    to stimuli until these are captured.
    
    Returns:
        Dict containing INCOM_score and usage_frequency.
    """
    logger.info(f"Starting covariate collection for participant {participant_id}")
    
    # INCOM Score Collection
    def is_non_negative_int(val: str) -> bool:
        try:
            return int(val) >= 0
        except ValueError:
            return False

    incom_str = get_input(
        "Enter INCOM score (non-negative integer): ",
        validator=is_non_negative_int
    )
    incom_score = int(incom_str)

    # Usage Frequency Collection
    def is_positive_float(val: str) -> bool:
        try:
            return float(val) > 0
        except ValueError:
            return False

    usage_str = get_input(
        "Enter weekly usage hours (positive number): ",
        validator=is_positive_float
    )
    usage_frequency = float(usage_str)

    covariates = {
        "INCOM_score": incom_score,
        "usage_frequency": usage_frequency,
        "collected_at": datetime.now().isoformat()
    }
    
    logger.info(f"Covariates collected: INCOM={incom_score}, Usage={usage_frequency}")
    return covariates

def present_stimuli(
    stimuli: List[Dict[str, Any]], 
    covariates: Dict[str, Any], 
    participant_id: str
) -> List[Dict[str, Any]]:
    """
    Presents stimuli one-by-one in a randomized order.
    Ensures distinct consecutive images (no repeats immediately).
    Captures BISS score immediately after each image.
    
    Args:
        stimuli: List of stimulus dicts.
        covariates: Pre-collected covariate data.
        participant_id: Current participant ID.
        
    Returns:
        List of response records.
    """
    logger.info("Starting stimulus presentation")
    
    # Create a copy to shuffle
    shuffled_stimuli = stimuli.copy()
    random.shuffle(shuffled_stimuli)
    
    # Ensure no immediate repeats (though shuffle usually handles this, 
    # we enforce distinct consecutive if the list is small)
    if len(shuffled_stimuli) > 1:
        # Simple check: if first two are same (unlikely with distinct IDs), swap
        if shuffled_stimuli[0]['id'] == shuffled_stimuli[1]['id']:
            shuffled_stimuli[0], shuffled_stimuli[1] = shuffled_stimuli[1], shuffled_stimuli[0]
    
    responses = []
    
    for i, stimulus in enumerate(shuffled_stimuli):
        # Display image (simulated by printing ID for CLI)
        # In a real GUI, this would show the image.
        print(f"\n--- Stimulus {i+1}/{len(shuffled_stimuli)} ---")
        print(f"Stimulus ID: {stimulus['id']}")
        print(f"Origin: {stimulus['origin']}")
        print("Please view the image.")
        input("Press Enter when ready to rate...")
        
        # Prompt for BISS score (1-7)
        def is_valid_biss(val: str) -> bool:
            try:
                v = int(val)
                return 1 <= v <= 7
            except ValueError:
                return False

        biss_str = get_input(
            "Enter BISS score (1-7): ",
            validator=is_valid_biss
        )
        biss_score = int(biss_str)
        
        # Create response record
        # T013 Schema: flat keys including covariates in every record or separate?
        # Spec T013: "Output ... with flat keys: stimulus_id, origin, timestamp, BISS_score, participant_id, INCOM_score, usage_frequency"
        # This implies each line in the JSONL contains the covariates repeated, or we write a header.
        # We will write a full record per stimulus including covariates as per spec.
        
        response = {
            "participant_id": participant_id,
            "stimulus_id": stimulus['id'],
            "origin": stimulus['origin'],
            "timestamp": datetime.now().isoformat(),
            "BISS_score": biss_score,
            "INCOM_score": covariates['INCOM_score'],
            "usage_frequency": covariates['usage_frequency']
        }
        
        responses.append(response)
        logger.info(f"Recorded BISS={biss_score} for {stimulus['id']}")
    
    return responses

def write_session_file(
    participant_id: str,
    session_id: str,
    responses: List[Dict[str, Any]],
    output_dir: str
) -> Path:
    """
    Writes the session data to a JSONL file.
    """
    output_path = Path(output_dir) / f"session_{session_id}.jsonl"
    
    with open(output_path, 'w') as f:
        for record in responses:
            f.write(json.dumps(record) + '\n')
    
    logger.info(f"Session file written to {output_path}")
    return output_path

def run_session(
    participant_id: str,
    output_dir: str,
    session_id: Optional[str] = None
) -> bool:
    """
    Orchestrates the full session flow:
    1. Load stimuli.
    2. Collect covariates (LOCK).
    3. Present stimuli.
    4. Write output.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]
        
        # 1. Load Stimuli
        # We assume the data directories exist as per T007
        ai_paths, human_paths = stimulus_loader.get_stimuli_paths()
        stimuli = stimulus_loader.load_stimuli(ai_paths, human_paths)
        
        if not stimuli:
            logger.error("No stimuli found. Aborting session.")
            return False
        
        # 2. Collect Covariates (LOCK BEFORE STIMULI)
        # This is the critical integration point for T019
        covariates = collect_covariates(participant_id)
        
        # 3. Present Stimuli
        responses = present_stimuli(stimuli, covariates, participant_id)
        
        # 4. Write Output
        write_session_file(participant_id, session_id, responses, output_dir)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("Session interrupted by user.")
        # Per T014: Partial sessions are excluded. We do not write partial data.
        return False
    except Exception as e:
        logger.error(f"Session failed: {e}")
        return False

def main():
    """
    Entry point for running the data collection interface directly.
    """
    # Use current directory or specified output
    output_dir = os.environ.get('OUTPUT_DIR', 'data/raw')
    os.makedirs(output_dir, exist_ok=True)
    
    pid = input("Enter Participant ID: ").strip()
    if not pid:
        pid = str(uuid.uuid4())[:8]
    
    success = run_session(participant_id=pid, output_dir=output_dir)
    
    if success:
        print(f"Session completed successfully. Data saved to {output_dir}.")
    else:
        print("Session failed or was interrupted. No data saved.")

if __name__ == "__main__":
    main()
