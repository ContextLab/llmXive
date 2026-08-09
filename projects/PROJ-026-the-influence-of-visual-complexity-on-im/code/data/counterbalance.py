import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging

from ..config import get_project_root
from ..utils.logging import log_counterbalance_strategy, get_logger

logger = get_logger("counterbalance")

def generate_counterbalance_assignments(
    participant_ids: List[str],
    seed: int = 42,
    split_ratio: float = 0.5
) -> pd.DataFrame:
    """
    Generate counterbalancing assignments for participants.

    This function assigns each participant to one of two session orders:
    - 'Low-High': Start with Low complexity stimuli, then High complexity
    - 'High-Low': Start with High complexity stimuli, then Low complexity

    The assignment is randomized with a fixed seed to ensure reproducibility
    and a near 50/50 split between the two conditions.

    Args:
        participant_ids: List of participant identifiers.
        seed: Random seed for reproducibility (default: 42).
        split_ratio: Target ratio for the first condition (default: 0.5).

    Returns:
        A DataFrame with columns: ['participant_id', 'session_order']
    """
    logger.info(f"Generating counterbalance assignments for {len(participant_ids)} participants.")
    logger.info(f"Using random seed: {seed}, target split ratio: {split_ratio}")

    np.random.seed(seed)

    # Create assignment list
    n_participants = len(participant_ids)
    n_condition_a = int(n_participants * split_ratio)

    # Create list of conditions
    conditions = ['Low-High'] * n_condition_a + ['High-Low'] * (n_participants - n_condition_a)

    # Shuffle to randomize assignment
    np.random.shuffle(conditions)

    # Create DataFrame
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'session_order': conditions
    })

    # Log the strategy details
    strategy_details = (
        f"Counterbalancing Strategy: Latin Square (AB/BA design)\n"
        f"Total Participants: {n_participants}\n"
        f"Condition A (Low-High): {sum(conditions == 'Low-High')} participants\n"
        f"Condition B (High-Low): {sum(conditions == 'High-Low')} participants\n"
        f"Random Seed: {seed}\n"
        f"Split Ratio: {split_ratio}\n"
        f"Assignment Method: Seeded random shuffle of pre-balanced condition list\n"
        f"Output: data/processed/counterbalance_assignment.csv"
    )

    log_counterbalance_strategy(strategy_details)

    return df

def main():
    """
    Main entry point for generating counterbalance assignments.

    This function creates a synthetic list of participant IDs (for CI/testing),
    generates the counterbalance assignments, and saves them to a CSV file.
    """
    # Create a synthetic list of participant IDs for testing
    # In a real scenario, this would be loaded from actual participant logs
    participant_ids = [f"P{str(i).zfill(3)}" for i in range(1, 101)]

    # Generate assignments
    assignments_df = generate_counterbalance_assignments(participant_ids, seed=42)

    # Save to CSV
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "counterbalance_assignment.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    assignments_df.to_csv(output_path, index=False)
    logger.info(f"Counterbalance assignments saved to {output_path}")

    # Print summary
    print(f"\nCounterbalance Assignment Summary:")
    print(f"Total Participants: {len(assignments_df)}")
    print(f"Low-High: {len(assignments_df[assignments_df['session_order'] == 'Low-High'])}")
    print(f"High-Low: {len(assignments_df[assignments_df['session_order'] == 'High-Low'])}")

    return assignments_df

if __name__ == "__main__":
    main()