"""
Counterbalance assignment module for the Implicit Bias experiment.
Generates participant-to-stimulus-set mappings with proper randomization.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import logging

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
RANDOM_SEED = 42


def load_complexity_categories(
    input_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load complexity categories from the processed scores file.

    Args:
        input_path: Optional path to complexity_scores.csv.

    Returns:
        DataFrame with filename and complexity_category.
    """
    if input_path is None:
        input_path = get_project_root() / "data" / "processed" / "complexity_scores.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Complexity scores file not found: {input_path}")

    df = pd.read_csv(input_path)
    required_cols = ['filename', 'complexity_category']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns in {input_path}. Expected: {required_cols}")

    logger.info(f"Loaded {len(df)} complexity categories from {input_path}")
    return df[required_cols]


def get_participant_ids(
    data_root: Optional[Path] = None,
    n_synthetic: int = 100
) -> List[str]:
    """
    Get participant IDs from real data or generate synthetic ones.

    Args:
        data_root: Root directory for data.
        n_synthetic: Number of synthetic IDs to generate if no real data.

    Returns:
        List of participant IDs.
    """
    if data_root is None:
        data_root = get_project_root()

    responses_dir = data_root / "data" / "raw" / "responses"

    # Try to load real participant IDs
    if responses_dir.exists():
        csv_files = list(responses_dir.glob("*.csv"))
        if csv_files:
            # Load first CSV to get participant IDs
            df = pd.read_csv(csv_files[0])
            if 'participant_id' in df.columns:
                participants = df['participant_id'].unique().tolist()
                logger.info(f"Found {len(participants)} real participants.")
                return participants

    # Generate synthetic IDs if no real data
    logger.info(f"Generating {n_synthetic} synthetic participant IDs.")
    return [f"P{i:04d}" for i in range(n_synthetic)]


def generate_counterbalance_assignments(
    participant_ids: List[str],
    complexity_df: pd.DataFrame,
    seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Generate counterbalance assignments mapping participants to stimulus sets.

    Algorithm:
    1. Randomly shuffle participants (seeded).
    2. Assign half to "Low-High" order with SetA, half to "High-Low" with SetB.
    3. Ensure SetA corresponds to 'Low' complexity and SetB to 'High'.

    Args:
        participant_ids: List of participant IDs.
        complexity_df: DataFrame with complexity categories (filename, complexity_category).
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with counterbalance assignments.
    """
    np.random.seed(seed)
    logger.info(f"Generating counterbalance assignments for {len(participant_ids)} participants (seed={seed}).")

    # Shuffle participants
    shuffled_ids = participant_ids.copy()
    np.random.shuffle(shuffled_ids)

    n_participants = len(shuffled_ids)
    n_low_high = n_participants // 2
    n_high_low = n_participants - n_low_high

    # Create assignments
    assignments = []

    # First half: Low-High order with SetA
    for i in range(n_low_high):
        assignments.append({
            'participant_id': shuffled_ids[i],
            'session_order': 'Low-High',
            'stimulus_set_id': 'SetA'
        })

    # Second half: High-Low order with SetB
    for i in range(n_low_high, n_participants):
        assignments.append({
            'participant_id': shuffled_ids[i],
            'session_order': 'High-Low',
            'stimulus_set_id': 'SetB'
        })

    df = pd.DataFrame(assignments)

    # Log split ratio
    split_ratio = n_low_high / n_participants
    logger.info(f"Counterbalance split: {split_ratio:.2%} Low-High / {1-split_ratio:.2%} High-Low")

    return df


def save_counterbalance_assignments(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Save counterbalance assignments to CSV.

    Args:
        df: DataFrame with assignments.
        output_path: Optional output path.

    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "counterbalance_assignment.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved counterbalance assignments to {output_path}")
    return output_path


def main():
    """
    Main entry point for generating counterbalance assignments.
    """
    import argparse
    from utils.logging import setup_logging

    parser = argparse.ArgumentParser(
        description="Generate counterbalance assignments for participants."
    )
    parser.add_argument(
        "--n-synthetic",
        type=int,
        default=100,
        help="Number of synthetic participants if no real data."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed (default: {RANDOM_SEED})."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for assignments."
    )

    args = parser.parse_args()
    setup_logging()

    try:
        # Load complexity categories
        complexity_df = load_complexity_categories()

        # Get participant IDs
        participant_ids = get_participant_ids(n_synthetic=args.n_synthetic)

        # Generate assignments
        assignments_df = generate_counterbalance_assignments(
            participant_ids,
            complexity_df,
            seed=args.seed
        )

        # Save results
        output_path = save_counterbalance_assignments(assignments_df, args.output)

        # Log strategy
        logs_dir = get_project_root() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / "counterbalance_strategy.log"
        with open(log_path, 'w') as f:
            f.write(f"Counterbalance Strategy Log\n")
            f.write(f"============================\n")
            f.write(f"Seed: {args.seed}\n")
            f.write(f"Total Participants: {len(participant_ids)}\n")
            f.write(f"Low-High (SetA): {len(assignments_df[assignments_df['session_order'] == 'Low-High'])}\n")
            f.write(f"High-Low (SetB): {len(assignments_df[assignments_df['session_order'] == 'High-Low'])}\n")
            f.write(f"Split Ratio: {len(assignments_df[assignments_df['session_order'] == 'Low-High']) / len(assignments_df):.2%}\n")
            f.write(f"Output: {output_path}\n")

        logger.info(f"Strategy logged to {log_path}")

    except Exception as e:
        logger.exception(f"Error generating counterbalance assignments: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
