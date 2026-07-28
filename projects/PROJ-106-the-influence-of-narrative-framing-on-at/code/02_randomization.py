import argparse
import json
import os
import sys
import random
import uuid
from datetime import datetime
from pathlib import Path

# Import from sibling modules
from utils.logger import log_script_start, log_script_end, log_data_operation, get_logger
from utils.random_utils import set_global_seed, ensure_seed_set

logger = get_logger(__name__)

def generate_participant_id():
    """Generate a unique, anonymous participant ID."""
    return str(uuid.uuid4())[:8].upper()

def assign_condition():
    """Randomly assign a participant to 'Partner' or 'Tool' condition (50/50)."""
    return random.choice(['Partner', 'Tool'])

def run_randomization(num_participants=1):
    """
    Generate a list of participants with assigned conditions.
    
    Args:
        num_participants: Number of participants to simulate/generate.
        
    Returns:
        List of dicts with 'participant_id' and 'condition'.
    """
    ensure_seed_set()
    participants = []
    for _ in range(num_participants):
        pid = generate_participant_id()
        condition = assign_condition()
        participants.append({
            'participant_id': pid,
            'condition': condition
        })
    return participants

def validate_balance(participants):
    """
    Validate that the randomization is balanced (within statistical tolerance).
    
    Args:
        participants: List of participant dicts.
        
    Returns:
        Tuple (is_balanced: bool, details: dict)
    """
    if not participants:
        return False, {"error": "No participants to validate"}
    
    counts = {'Partner': 0, 'Tool': 0}
    for p in participants:
        counts[p['condition']] += 1
    
    total = len(participants)
    ratio = counts['Partner'] / total if total > 0 else 0
    
    # Allow 40-60% split for small samples, tighter for large
    tolerance = 0.1 if total < 100 else 0.05
    is_balanced = 0.5 - tolerance <= ratio <= 0.5 + tolerance
    
    return is_balanced, {
        'partner_count': counts['Partner'],
        'tool_count': counts['Tool'],
        'total': total,
        'ratio': ratio,
        'balanced': is_balanced
    }

def save_randomization_log(participants, output_path):
    """
    Save randomization metadata to a JSON file IMMEDIATELY.
    
    This function writes the log BEFORE any survey display to prevent drift,
    as required by Constitution III and US-1.
    
    Args:
        participants: List of participant dicts with 'participant_id' and 'condition'.
        output_path: Path to the output JSON file.
        
    Returns:
        Path to the written file.
    """
    log_data_operation("Starting randomization log write", path=str(output_path))
    
    # Ensure directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare log entries with timestamps
    log_entries = []
    for p in participants:
        entry = {
            'participant_id': p['participant_id'],
            'condition': p['condition'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'script_version': '02_randomization_v1'
        }
        log_entries.append(entry)
    
    # Write to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_entries, f, indent=2)
        
        log_data_operation(f"Successfully wrote {len(log_entries)} entries to randomization log", path=str(output_file))
        return output_file
    except IOError as e:
        logger.error(f"Failed to write randomization log: {e}")
        raise

def main():
    """
    Main entry point for the randomization script.
    
    This script generates participant IDs, assigns conditions,
    and IMMEDIATELY writes the metadata to a log file to prevent drift.
    """
    parser = argparse.ArgumentParser(description="Randomize participants to conditions and log immediately")
    parser.add_argument('--num', type=int, default=10, help="Number of participants to generate")
    parser.add_argument('--output', type=str, default="data/processed/randomization_log.json", 
                      help="Path to output log file")
    parser.add_argument('--seed', type=int, default=None, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    if args.seed is not None:
        set_global_seed(args.seed)
    
    log_script_start("02_randomization", args)
    
    try:
        # Generate randomization
        participants = run_randomization(args.num)
        
        # Validate balance
        is_balanced, details = validate_balance(participants)
        logger.info(f"Randomization balance check: {details}")
        
        # CRITICAL: Write log IMMEDIATELY before any survey display
        output_path = Path(args.output)
        written_path = save_randomization_log(participants, output_path)
        
        log_script_end("02_randomization", success=True, output=str(written_path))
        
        return 0
    except Exception as e:
        logger.exception(f"Randomization script failed: {e}")
        log_script_end("02_randomization", success=False, error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())