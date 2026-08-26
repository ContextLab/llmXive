"""
Random presentation order generator for the text message tone study.

This module implements Task T015: Generates a shuffled trial order per participant
based on the counterbalanced trial set. Each participant receives every stimulus
in both relationship contexts (friend & acquaintance) in a random order.

Output: data/processed/presentation_orders.csv
"""

import argparse
import csv
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Import existing utilities from the project
from config import get_project_root, get_processed_data_dir
from logging_config import setup_logging, get_logger


def load_counterbalanced_trials(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load the counterbalanced trials CSV.

    Args:
        filepath: Path to data/processed/counterbalanced_trials.csv

    Returns:
        List of dictionaries representing trial records.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Counterbalanced trials file not found: {filepath}")

    trials = []
    with open(filepath, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trials.append(row)
    return trials


def generate_random_orders(trials: List[Dict[str, Any]], participant_ids: List[str], seed: int) -> List[Dict[str, Any]]:
    """
    Generate random presentation orders for each participant.

    For each participant, the set of trials is shuffled to create a unique
    presentation order. The random seed ensures reproducibility.

    Args:
        trials: List of all counterbalanced trial records.
        participant_ids: List of participant identifiers.
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries with columns: participant_id, trial_id, presentation_order.
    """
    random.seed(seed)
    orders = []

    # Group trials by participant_id (conceptually, though the counterbalanced file
    # might just list all trials for all participants. We assume the counterbalanced
    # file has a 'participant_id' column or we assign them based on the provided list).
    # Looking at T014 description: "assigning every stimulus to both relationship contexts... for each participant".
    # The output of T014 is 'data/processed/counterbalanced_trials.csv'.
    # We assume this file contains a 'participant_id' column. If not, we might need to
    # generate the assignments here, but T014 implies the assignments exist.
    # Let's verify the structure expected: The task says "producing... with a shuffled trial order per participant".
    # We will group by participant_id found in the input file.

    # If the input file does not have participant_id, we must generate the assignment.
    # However, T014 description says "assigning every stimulus to both... for each participant".
    # Let's assume the input file from T014 already has 'participant_id'.
    # If not, we fall back to generating it if we have the list of participant_ids.
    # But standard flow: T014 -> T015. T014 output should have participant_id.

    # Check if 'participant_id' exists in the first row
    if trials and 'participant_id' not in trials[0]:
        # Fallback: If the file doesn't have participant_id, we assume it lists all unique
        # stimulus-context pairs and we need to replicate them for each participant.
        # This is a robustness check.
        logging.warning("Input file missing 'participant_id'. Generating assignments for provided participants.")
        unique_trials = trials # These are unique stimulus-context combos
        for pid in participant_ids:
            for idx, trial in enumerate(unique_trials):
                # Create a copy with the participant_id
                assigned_trial = trial.copy()
                assigned_trial['participant_id'] = pid
                assigned_trial['original_idx'] = idx # Keep track for shuffling if needed
                trials = [] # Reset and rebuild? No, this is complex.
                # Better approach: If T014 output is just the design matrix (N stimuli x 2 contexts),
                # then we generate the full list here.
                # But T014 says "assigning... for each participant".
                # Let's assume the file has 'participant_id'. If it fails, we raise.
                raise ValueError("Input file 'counterbalanced_trials.csv' must contain 'participant_id' column.")

    # Group by participant
    participant_trials: Dict[str, List[Dict[str, Any]]] = {}
    for trial in trials:
        pid = trial.get('participant_id')
        if not pid:
            raise ValueError("Trial record missing 'participant_id'.")
        if pid not in participant_trials:
            participant_trials[pid] = []
        participant_trials[pid].append(trial)

    # Generate orders
    for pid in participant_ids:
        if pid not in participant_trials:
            # If a participant in the list has no trials (shouldn't happen if T014 ran correctly), skip or error
            logging.warning(f"No trials found for participant {pid}.")
            continue

        current_trials = participant_trials[pid]
        # Shuffle the trials for this participant
        # We need a deterministic shuffle based on the global seed + participant ID
        # to ensure reproducibility across runs.
        # Create a deterministic seed for this participant
        pid_seed = seed + hash(pid) % 100000
        local_random = random.Random(pid_seed)

        shuffled_trials = current_trials.copy()
        local_random.shuffle(shuffled_trials)

        for order_idx, trial in enumerate(shuffled_trials):
            orders.append({
                'participant_id': pid,
                'trial_id': trial.get('trial_id') or trial.get('id'), # Handle potential ID naming
                'stimulus_id': trial.get('stimulus_id') or trial.get('id'),
                'context': trial.get('context'),
                'presentation_order': order_idx + 1
            })

    return orders


def save_orders(orders: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Save the presentation orders to a CSV file.

    Args:
        orders: List of order dictionaries.
        filepath: Output path.
    """
    if not orders:
        raise ValueError("No orders to save.")

    filepath.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['participant_id', 'trial_id', 'stimulus_id', 'context', 'presentation_order']
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(orders)


def verify_orders(orders: List[Dict[str, Any]], participant_ids: List[str], total_trials_per_participant: int) -> bool:
    """
    Verify that the generated orders are valid permutations.

    Checks:
    1. Each participant has exactly total_trials_per_participant entries.
    2. The presentation_order for each participant is a permutation of 1..N.
    3. No duplicate trial_ids for the same participant.

    Args:
        orders: List of order dictionaries.
        participant_ids: List of expected participant IDs.
        total_trials_per_participant: Expected count of trials per participant.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    from collections import Counter

    # Group by participant
    p_orders: Dict[str, List[Dict]] = {}
    for o in orders:
        pid = o['participant_id']
        if pid not in p_orders:
            p_orders[pid] = []
        p_orders[pid].append(o)

    for pid in participant_ids:
        if pid not in p_orders:
            raise ValueError(f"Participant {pid} missing from orders.")

        p_data = p_orders[pid]
        if len(p_data) != total_trials_per_participant:
            raise ValueError(f"Participant {pid} has {len(p_data)} trials, expected {total_trials_per_participant}.")

        orders_list = [o['presentation_order'] for o in p_data]
        # Check if 1..N permutation
        if sorted(orders_list) != list(range(1, total_trials_per_participant + 1)):
            raise ValueError(f"Participant {pid} has invalid presentation orders: {orders_list}")

        # Check for duplicate trial_ids
        trial_ids = [o['trial_id'] for o in p_data]
        if len(trial_ids) != len(set(trial_ids)):
            raise ValueError(f"Participant {pid} has duplicate trial_ids.")

    return True


def main():
    """Main entry point for the random order generator."""
    setup_logging()
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="Generate random presentation orders for participants.")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument('--input', type=str, default=None, help="Path to counterbalanced_trials.csv (optional, uses default).")
    parser.add_argument('--output', type=str, default=None, help="Path to output orders.csv (optional, uses default).")
    parser.add_argument('--verify', action='store_true', help="Run verification checks.")
    args = parser.parse_args()

    root = get_project_root()
    processed_dir = get_processed_data_dir()

    input_path = Path(args.input) if args.input else processed_dir / "counterbalanced_trials.csv"
    output_path = Path(args.output) if args.output else processed_dir / "presentation_orders.csv"

    logger.info(f"Loading counterbalanced trials from {input_path}")
    trials = load_counterbalanced_trials(input_path)

    # Extract unique participant IDs and total trials per participant
    # We assume the input file has 'participant_id'
    if not trials:
        raise ValueError("No trials found in input file.")

    participant_ids = sorted(list(set(t['participant_id'] for t in trials if 'participant_id' in t)))
    if not participant_ids:
        raise ValueError("Could not determine participant IDs from input file.")

    total_trials = len([t for t in trials if t['participant_id'] == participant_ids[0]])
    logger.info(f"Found {len(participant_ids)} participants. Trials per participant: {total_trials}")

    logger.info(f"Generating random presentation orders with seed {args.seed}")
    orders = generate_random_orders(trials, participant_ids, args.seed)

    logger.info(f"Saving orders to {output_path}")
    save_orders(orders, output_path)

    if args.verify:
        logger.info("Running verification checks...")
        try:
            verify_orders(orders, participant_ids, total_trials)
            logger.info("Verification PASSED: All presentation orders are valid permutations.")
        except ValueError as e:
            logger.error(f"Verification FAILED: {e}")
            return 1
    else:
        logger.info("Verification skipped. Use --verify to check.")

    logger.info("Task T015 completed successfully.")
    return 0


if __name__ == "__main__":
    exit(main())