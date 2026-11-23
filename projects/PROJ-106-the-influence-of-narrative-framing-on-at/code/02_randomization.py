import argparse
import json
import os
import sys
import random
import uuid
from pathlib import Path
from datetime import datetime

# Import from sibling utilities as per API surface
from utils.logger import log_script_start, log_script_end, log_audit_event, get_logger
from utils.random_utils import set_global_seed, ensure_seed_set

logger = get_logger(__name__)

def generate_participant_id():
    """Generate a unique, non-sequential Participant ID."""
    return str(uuid.uuid4())

def assign_condition():
    """
    Assign a condition (Partner or Tool) with a 50/50 split probability.
    Returns 'Partner' or 'Tool'.
    """
    return random.choice(['Partner', 'Tool'])

def run_randomization(n_participants, seed=None):
    """
    Run randomization for a batch of participants.
    Returns a list of dicts with participant_id, condition.
    """
    if seed is not None:
        set_global_seed(seed)
    else:
        ensure_seed_set()

    results = []
    for _ in range(n_participants):
        pid = generate_participant_id()
        condition = assign_condition()
        results.append({
            'participant_id': pid,
            'condition': condition
        })
    return results

def validate_balance(assignments):
    """
    Validate that the distribution of conditions is roughly 50/50.
    Returns True if the split is within statistical tolerance (e.g., ±10%).
    """
    if not assignments:
        return True
    
    counts = {'Partner': 0, 'Tool': 0}
    for a in assignments:
        counts[a['condition']] += 1
    
    total = len(assignments)
    partner_ratio = counts['Partner'] / total
    
    # Allow a tolerance of 10% deviation from 0.5
    return 0.4 <= partner_ratio <= 0.6

def save_randomization_log(assignments, output_path, seed=None):
    """
    Write randomization metadata to a JSON file.
    This is called IMMEDIATELY after assignment to prevent drift.
    
    Args:
        assignments: List of dicts with participant_id, condition.
        output_path: Path to the output JSON file.
        seed: The seed used for reproducibility (optional).
    """
    # Ensure the directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat()
    
    log_data = {
        'timestamp': timestamp,
        'seed': seed,
        'total_participants': len(assignments),
        'assignments': assignments
    }

    # Calculate summary stats for the log header
    if assignments:
        partner_count = sum(1 for a in assignments if a['condition'] == 'Partner')
        tool_count = sum(1 for a in assignments if a['condition'] == 'Tool')
        log_data['summary'] = {
            'partner_count': partner_count,
            'tool_count': tool_count,
            'partner_ratio': partner_count / len(assignments)
        }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

    log_audit_event(f"Randomization log written to {output_path}", logger)
    return output_path

def main():
    """
    CLI entry point for running randomization and saving the log.
    Usage: python code/02_randomization.py --n 100 --seed 42 --output data/processed/randomization_log.json
    """
    parser = argparse.ArgumentParser(description="Randomize participants and log immediately.")
    parser.add_argument('--n', type=int, default=10, help='Number of participants to randomize.')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility.')
    parser.add_argument('--output', type=str, default='data/processed/randomization_log.json', help='Output JSON path.')
    
    args = parser.parse_args()

    log_script_start("02_randomization", args, logger)

    # Run randomization
    assignments = run_randomization(args.n, seed=args.seed)

    # Validate balance (log warning if off, but proceed as this is a simulation/batch run)
    if not validate_balance(assignments):
        logger.warning("Randomization distribution is not within 50/50 tolerance.")

    # CRITICAL: Write to disk immediately to prevent drift
    save_randomization_log(assignments, args.output, seed=args.seed)

    log_script_end("02_randomization", logger)
    print(f"Successfully randomized {args.n} participants. Log saved to {args.output}")

if __name__ == '__main__':
    main()
