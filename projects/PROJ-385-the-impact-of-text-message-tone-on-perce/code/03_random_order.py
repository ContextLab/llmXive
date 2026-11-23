"""
T015: Random presentation order generator.

Produces data/processed/presentation_orders.csv with a shuffled trial order per participant.
Depends on: T014 (data/processed/counterbalanced_trials.csv).
"""
import argparse
import csv
import logging
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# Adjust imports to match project structure (relative to code/ directory)
try:
    from config import get_processed_data_dir, get_project_root
    from logging_config import setup_logging, get_logger
except ImportError:
    # Fallback for direct execution if path setup is different
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import get_processed_data_dir, get_project_root
    from logging_config import setup_logging, get_logger

def load_counterbalanced_trials(input_path: Path) -> list:
    """Load the counterbalanced trials from CSV."""
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
    Generate random presentation orders for each participant.
    
    Groups trials by participant_id, shuffles them, and assigns an order number (1..N).
    """
    # Group trials by participant
    participant_trials = {}
    for trial in trials:
        pid = trial['participant_id']
        if pid not in participant_trials:
            participant_trials[pid] = []
        participant_trials[pid].append(trial)
    
    # Set seed for reproducibility
    random.seed(seed)
    
    orders = []
    for pid, p_trials in participant_trials.items():
        # Shuffle the trials for this participant
        random.shuffle(p_trials)
        
        # Assign order numbers
        for idx, trial in enumerate(p_trials, start=1):
            order_row = {
                'participant_id': pid,
                'stimulus_id': trial['stimulus_id'],
                'text': trial['text'],
                'emoji_count': trial['emoji_count'],
                'punctuation_type': trial['punctuation_type'],
                'length_category': trial['length_category'],
                'scenario_id': trial['scenario_id'],
                'cue_intensity': trial['cue_intensity'],
                'context': trial['context'],
                'order': idx
            }
            orders.append(order_row)
    
    return orders

def save_orders(orders: list, output_path: Path) -> None:
    """Save the generated orders to a CSV file."""
    if not orders:
        raise ValueError("No orders to save.")
    
    fieldnames = [
        'participant_id', 'stimulus_id', 'text', 'emoji_count',
        'punctuation_type', 'length_category', 'scenario_id',
        'cue_intensity', 'context', 'order'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(orders)

def verify_orders(orders: list, input_trials: list, logger: logging.Logger) -> bool:
    """
    Verify that the generated orders are valid permutations.
    
    Checks:
    1. Every participant in input has an entry in output.
    2. The order numbers for each participant are a permutation of 1..N.
    """
    # Count trials per participant in input
    input_counts = {}
    for t in input_trials:
        pid = t['participant_id']
        input_counts[pid] = input_counts.get(pid, 0) + 1
    
    # Count orders per participant in output
    output_counts = {}
    output_orders = {}
    for o in orders:
        pid = o['participant_id']
        order_num = int(o['order'])
        output_counts[pid] = output_counts.get(pid, 0) + 1
        if pid not in output_orders:
            output_orders[pid] = []
        output_orders[pid].append(order_num)
    
    # Check counts match
    if set(input_counts.keys()) != set(output_counts.keys()):
        missing = set(input_counts.keys()) - set(output_counts.keys())
        extra = set(output_counts.keys()) - set(input_counts.keys())
        logger.error(f"Participant mismatch. Missing: {missing}, Extra: {extra}")
        return False
    
    # Check permutation property
    for pid, orders_list in output_orders.items():
        expected_count = input_counts[pid]
        if len(orders_list) != expected_count:
            logger.error(f"Participant {pid}: expected {expected_count} orders, got {len(orders_list)}")
            return False
        
        # Check if it's a permutation of 1..N
        sorted_orders = sorted(orders_list)
        expected_sequence = list(range(1, expected_count + 1))
        if sorted_orders != expected_sequence:
            logger.error(f"Participant {pid}: invalid permutation {sorted_orders}")
            return False
    
    logger.info("Verification passed: All participants have valid permutations.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate random presentation orders for participants.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to counterbalanced_trials.csv. Defaults to project default."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output presentation_orders.csv. Defaults to project default."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification checks after generation."
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting random order generation (T015).")
    
    project_root = get_project_root()
    processed_dir = get_processed_data_dir()
    
    input_path = Path(args.input) if args.input else processed_dir / "counterbalanced_trials.csv"
    output_path = Path(args.output) if args.output else processed_dir / "presentation_orders.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load input
        logger.info(f"Loading counterbalanced trials from {input_path}")
        trials = load_counterbalanced_trials(input_path)
        logger.info(f"Loaded {len(trials)} trials.")
        
        # Generate orders
        logger.info(f"Generating random orders with seed={args.seed}")
        orders = generate_random_orders(trials, args.seed)
        logger.info(f"Generated {len(orders)} order entries.")
        
        # Save output
        logger.info(f"Saving orders to {output_path}")
        save_orders(orders, output_path)
        logger.info("Order generation complete.")
        
        # Verify if requested
        if args.verify:
            logger.info("Running verification checks...")
            is_valid = verify_orders(orders, trials, logger)
            if not is_valid:
                logger.error("Verification failed.")
                sys.exit(1)
            else:
                logger.info("Verification successful.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
