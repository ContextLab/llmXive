"""
Task T015: Random presentation order generator.

Reads the counterbalanced trials from T014 and generates a random
presentation order for each participant. Outputs a CSV where each
row represents a single trial instance with a defined order index.

Verification:
  - Each participant's order list is a permutation of their trial set.
  - Reproducible given the fixed seed in config.py.
"""

import argparse
import csv
import logging
import os
import random
from datetime import datetime
from pathlib import Path

from config import get_processed_data_dir, get_project_root
from logging_config import setup_logging, get_logger


def load_counterbalanced_trials(input_path: Path) -> list:
    """
    Load the counterbalanced trials CSV.

    Expected columns (from T014):
      participant_id, stimulus_id, text, emoji_count, punctuation_type,
      length_category, scenario_id, cue_intensity, context

    Returns:
        List of dictionaries representing the rows.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    trials = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trials.append(row)
    return trials


def generate_random_orders(trials: list, seed: int) -> list:
    """
    Generate a random presentation order for each participant.

    Logic:
      1. Group trials by participant_id.
      2. For each participant, shuffle their specific list of trials.
      3. Assign an 'order' index (1-based) to each trial in the shuffled list.
      4. Flatten the results back into a single list.

    Args:
        trials: List of trial dictionaries.
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries with added 'order' key.
    """
    random.seed(seed)

    # Group by participant
    participant_groups = {}
    for trial in trials:
        pid = trial['participant_id']
        if pid not in participant_groups:
            participant_groups[pid] = []
        participant_groups[pid].append(trial)

    ordered_trials = []
    for pid, p_trials in participant_groups.items():
        # Shuffle the trials for this participant
        random.shuffle(p_trials)
        # Assign order
        for idx, trial in enumerate(p_trials, start=1):
            trial['order'] = idx
            ordered_trials.append(trial)

    return ordered_trials


def save_orders(ordered_trials: list, output_path: Path):
    """
    Save the ordered trials to a CSV file.

    Args:
        ordered_trials: List of trial dictionaries.
        output_path: Path to the output CSV.
    """
    if not ordered_trials:
        raise ValueError("No trials to save.")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'participant_id', 'stimulus_id', 'text', 'emoji_count',
        'punctuation_type', 'length_category', 'scenario_id',
        'cue_intensity', 'context', 'order'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ordered_trials)


def verify_orders(input_path: Path, output_path: Path) -> bool:
    """
    Verify that the output file contains valid permutations.

    Checks:
      1. Every participant in input exists in output.
      2. For each participant, the set of stimulus_ids in output
         matches the set in input.
      3. The 'order' column contains a sequence 1..N for each participant.

    Returns:
        True if verification passes, raises AssertionError otherwise.
    """
    if not output_path.exists():
        raise FileNotFoundError(f"Output file not found: {output_path}")

    input_trials = load_counterbalanced_trials(input_path)
    output_trials = []
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            output_trials.append(row)

    # Group input by participant
    input_groups = {}
    for t in input_trials:
        pid = t['participant_id']
        if pid not in input_groups:
            input_groups[pid] = set()
        input_groups[pid].add(t['stimulus_id'])

    # Group output by participant
    output_groups = {}
    for t in output_trials:
        pid = t['participant_id']
        if pid not in output_groups:
            output_groups[pid] = []
        output_groups[pid].append(t)

    # Check counts and sets
    if set(input_groups.keys()) != set(output_groups.keys()):
        raise AssertionError("Participant sets do not match between input and output.")

    for pid, in_stimuli in input_groups.items():
        out_trials = output_groups[pid]
        out_stimuli = {t['stimulus_id'] for t in out_trials}

        if in_stimuli != out_stimuli:
            raise AssertionError(
                f"Participant {pid}: Stimulus sets do not match. "
                f"Input: {in_stimuli}, Output: {out_stimuli}"
            )

        orders = [int(t['order']) for t in out_trials]
        orders.sort()
        expected_orders = list(range(1, len(out_trials) + 1))

        if orders != expected_orders:
            raise AssertionError(
                f"Participant {pid}: Order sequence is not a permutation of 1..N. "
                f"Got: {orders}"
            )

    return True


def main():
    """Main entry point for the script."""
    setup_logging()
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(
        description="Generate random presentation orders for participants."
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help="Path to counterbalanced trials CSV. Defaults to project standard."
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Path to output presentation orders CSV. Defaults to project standard."
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help="Run verification checks after generation."
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )

    args = parser.parse_args()

    project_root = get_project_root()
    processed_dir = get_processed_data_dir()

    if args.input is None:
        input_path = processed_dir / "counterbalanced_trials.csv"
    else:
        input_path = Path(args.input)

    if args.output is None:
        output_path = processed_dir / "presentation_orders.csv"
    else:
        output_path = Path(args.output)

    logger.info(f"Loading counterbalanced trials from: {input_path}")
    try:
        trials = load_counterbalanced_trials(input_path)
        logger.info(f"Loaded {len(trials)} trials.")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    logger.info(f"Generating random orders with seed={args.seed}")
    ordered_trials = generate_random_orders(trials, seed=args.seed)
    logger.info(f"Generated {len(ordered_trials)} ordered trials.")

    logger.info(f"Saving to: {output_path}")
    save_orders(ordered_trials, output_path)
    logger.info("Saved successfully.")

    if args.verify:
        logger.info("Running verification...")
        try:
            verify_orders(input_path, output_path)
            logger.info("Verification PASSED: All orders are valid permutations.")
        except AssertionError as e:
            logger.error(f"Verification FAILED: {e}")
            raise
        except FileNotFoundError as e:
            logger.error(f"Verification FAILED: {e}")
            raise

    logger.info("Task T015 completed successfully.")


if __name__ == "__main__":
    main()
