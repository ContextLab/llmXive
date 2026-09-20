import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging
import argparse
from config import get_project_root, get_data_path
from utils.logging import get_logger, log_counterbalance_strategy

logger = get_logger(__name__)

def generate_counterbalance_assignments(
    n_participants: int,
    seed: int = 42,
    split_ratio: float = 0.5
) -> pd.DataFrame:
    """
    Generate counterbalance assignments for participants.

    Args:
        n_participants: Total number of participants to assign.
        seed: Random seed for reproducibility.
        split_ratio: Ratio of participants starting with Low complexity (0.0 to 1.0).
                    Default 0.5 means balanced allocation.

    Returns:
        DataFrame with columns: participant_id, session_order, complexity_condition_order
    """
    logger.info(f"Generating counterbalance assignments for {n_participants} participants (seed={seed})")

    np.random.seed(seed)

    # Generate participant IDs
    participant_ids = [f"P{str(i+1).zfill(3)}" for i in range(n_participants)]

    # Determine session orders based on split ratio
    # Session order: 'Low-High' (starts with Low) or 'High-Low' (starts with High)
    n_low_first = int(n_participants * split_ratio)
    n_high_first = n_participants - n_low_first

    # Create the list of session orders
    session_orders = (
        ['Low-High'] * n_low_first + ['High-Low'] * n_high_first
    )

    # Shuffle to randomize which participant gets which order
    np.random.shuffle(session_orders)

    # Create the DataFrame
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'session_order': session_orders,
        'complexity_condition_order': session_orders  # Alias for clarity
    })

    return df

def main():
    """CLI entry point for counterbalance assignment generation."""
    parser = argparse.ArgumentParser(
        description="Generate counterbalance assignments for experimental sessions."
    )
    parser.add_argument(
        '--n-participants',
        type=int,
        default=60,
        help='Number of participants to assign (default: 60)'
    )
    parser.add_argument(
        '--split-ratio',
        type=float,
        default=0.5,
        help='Ratio of participants starting with Low complexity (default: 0.5 for balanced)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default=None,
        help='Custom output path. If not provided, uses default project path.'
    )

    args = parser.parse_args()

    # Validate split ratio
    if not 0.0 <= args.split_ratio <= 1.0:
        raise ValueError(f"split_ratio must be between 0.0 and 1.0, got {args.split_ratio}")

    # Determine output path
    project_root = get_project_root()
    if args.output_path:
        output_path = Path(args.output_path)
    else:
        output_path = get_data_path(project_root, "processed/counterbalance_assignment.csv")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating assignments: N={args.n_participants}, split_ratio={args.split_ratio}, seed={args.seed}")

    # Generate assignments
    df = generate_counterbalance_assignments(
        n_participants=args.n_participants,
        seed=args.seed,
        split_ratio=args.split_ratio
    )

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Counterbalance assignments saved to {output_path}")

    # Log the strategy for audit trail
    log_path = get_data_path(project_root, "../logs/counterbalance_strategy.log")
    log_counterbalance_strategy(
        log_path,
        seed=args.seed,
        split_ratio=args.split_ratio,
        n_participants=args.n_participants,
        n_low_first=int(args.n_participants * args.split_ratio),
        n_high_first=args.n_participants - int(args.n_participants * args.split_ratio)
    )

    logger.info(f"Counterbalance strategy logged to {log_path}")

    return df

if __name__ == "__main__":
    main()
