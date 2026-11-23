"""
Experiment Runner Module (T013)

Assigns participants to experimental conditions (Battle, Journey, Medical).
Handles both simulated participant lists and real survey response ingestion.
Outputs a deterministic CSV of assignments for downstream processing.
"""
import os
import csv
import json
import argparse
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Import shared utilities
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Constants
CONDITIONS = ["Battle", "Journey", "Medical"]
INPUT_SIMULATED = "data/raw/simulated_participants.csv"
INPUT_REAL = "data/raw/survey_responses.json"
OUTPUT_FILE = "data/processed/experimental_assignments.csv"

class ExperimentRunnerError(Exception):
    """Custom exception for experiment runner errors."""
    pass

def load_simulated_participants(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads simulated participants from a CSV file.
    Expected columns: participant_id, [optional metadata]
    """
    if not os.path.exists(filepath):
        raise ExperimentRunnerError(f"Simulated participant file not found: {filepath}")
    
    participants = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'participant_id' not in row:
                raise ExperimentRunnerError("Simulated participant CSV missing 'participant_id' column")
            participants.append(row)
    
    logger.info(f"Loaded {len(participants)} simulated participants from {filepath}")
    return participants

def load_real_survey_responses(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads real survey responses from a JSON file.
    Expects a list of objects or a dict with a 'responses' key.
    Extracts participant_id from the data.
    """
    if not os.path.exists(filepath):
        raise ExperimentRunnerError(f"Real survey response file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        if 'responses' in data:
            responses = data['responses']
        elif 'data' in data:
            responses = data['data']
        else:
            raise ExperimentRunnerError("Real survey JSON must contain 'responses' or 'data' key")
    elif isinstance(data, list):
        responses = data
    else:
        raise ExperimentRunnerError("Real survey JSON must be a list or dict with 'responses'/'data'")
    
    participants = []
    for item in responses:
        if 'participant_id' not in item:
            # Try to generate one if missing (should not happen in valid data)
            pid = item.get('id', item.get('participantId', None))
            if pid is None:
                raise ExperimentRunnerError("Real survey data missing 'participant_id' in a response entry")
            item['participant_id'] = pid
        participants.append(item)
    
    logger.info(f"Loaded {len(participants)} real survey responses from {filepath}")
    return participants

def assign_condition(participant_id: str) -> str:
    """
    Deterministically assigns a condition based on participant_id hash.
    Ensures reproducibility across runs.
    """
    # Hash the ID to get a consistent integer
    hash_obj = hashlib.md5(participant_id.encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Map to condition index (0, 1, or 2)
    condition_index = hash_int % len(CONDITIONS)
    return CONDITIONS[condition_index]

def run_experiment(input_file: Optional[str] = None, source_type: Optional[str] = None) -> None:
    """
    Main execution logic to assign conditions and write output.
    
    Args:
        input_file: Path to input CSV (simulated) or JSON (real).
        source_type: 'simulated' or 'real'. If None, inferred from file extension/content.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    participants = []
    
    if input_file:
        # Use provided file
        if source_type is None:
            if input_file.endswith('.csv'):
                source_type = 'simulated'
            elif input_file.endswith('.json'):
                source_type = 'real'
            else:
                raise ExperimentRunnerError(f"Cannot determine source type for extension: {input_file}")
        
        if source_type == 'simulated':
            participants = load_simulated_participants(input_file)
        else:
            participants = load_real_survey_responses(input_file)
    else:
        # Fallback to default paths if no input specified
        logger.info("No input file specified, checking defaults...")
        if os.path.exists(INPUT_SIMULATED):
            source_type = 'simulated'
            participants = load_simulated_participants(INPUT_SIMULATED)
        elif os.path.exists(INPUT_REAL):
            source_type = 'real'
            participants = load_real_survey_responses(INPUT_REAL)
        else:
            raise ExperimentRunnerError(
                f"No input file provided and neither {INPUT_SIMULATED} nor {INPUT_REAL} exists."
            )
    
    if not participants:
        raise ExperimentRunnerError("No participants found to assign conditions.")
    
    # Process assignments
    assignments = []
    for p in participants:
        pid = p['participant_id']
        condition = assign_condition(pid)
        assignments.append({
            'participant_id': pid,
            'condition': condition,
            'assignment_timestamp': datetime.now().isoformat(),
            'source_type': source_type
        })
        # Log a sample
        if len(assignments) <= 3:
            logger.debug(f"Assigned {pid} -> {condition}")
    
    # Write output
    fieldnames = ['participant_id', 'condition', 'assignment_timestamp', 'source_type']
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(assignments)
    
    logger.info(f"Successfully assigned {len(assignments)} participants. Output written to {OUTPUT_FILE}")

def main():
    parser = argparse.ArgumentParser(description="Assign participants to experimental conditions.")
    parser.add_argument(
        '--input', '-i', 
        type=str, 
        default=None,
        help="Path to input CSV (simulated) or JSON (real). If omitted, checks defaults."
    )
    parser.add_argument(
        '--type', '-t',
        type=str,
        choices=['simulated', 'real'],
        default=None,
        help="Explicitly specify source type if file extension is ambiguous."
    )
    
    args = parser.parse_args()
    
    try:
        run_experiment(input_file=args.input, source_type=args.type)
    except ExperimentRunnerError as e:
        logger.error(f"Experiment runner failed: {e}")
        raise

if __name__ == "__main__":
    main()
