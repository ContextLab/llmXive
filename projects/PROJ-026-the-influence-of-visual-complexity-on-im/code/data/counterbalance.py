"""
Counterbalance assignment generation for User Story 2.

Generates a deterministic mapping of participant IDs to session orders
(Low-High vs High-Low) using a seeded random shuffle to ensure an equal split.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for counterbalancing
SEED = 42
SESSION_ORDER_A = "Low-High"
SESSION_ORDER_B = "High-Low"


def generate_counterbalance_assignments(
    num_participants: int = 100,
    seed: int = SEED
) -> pd.DataFrame:
    """
    Generate a counterbalance assignment map for a specified number of participants.

    Args:
        num_participants: Total number of participant IDs to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: participant_id, session_order
    """
    logger.info(f"Generating counterbalance assignments for {num_participants} participants (seed={seed})")

    # Set seed for reproducibility
    np.random.seed(seed)

    # Generate participant IDs (P001 to P{num_participants:03d})
    participant_ids = [f"P{i+1:03d}" for i in range(num_participants)]

    # Create the two session orders
    orders = [SESSION_ORDER_A, SESSION_ORDER_B]

    # Assign orders to participants ensuring an equal split
    # We create a list with equal numbers of A and B, then shuffle it
    if num_participants % 2 != 0:
        logger.warning(f"Number of participants ({num_participants}) is odd. "
                     f"Assignments will be off by one.")
        n_a = (num_participants // 2) + 1
        n_b = num_participants // 2
    else:
        n_a = num_participants // 2
        n_b = num_participants // 2

    assignment_list = [SESSION_ORDER_A] * n_a + [SESSION_ORDER_B] * n_b
    np.random.shuffle(assignment_list)

    # Create DataFrame
    df = pd.DataFrame({
        "participant_id": participant_ids,
        "session_order": assignment_list
    })

    # Log split ratio
    split_a = (df["session_order"] == SESSION_ORDER_A).sum()
    split_b = (df["session_order"] == SESSION_ORDER_B).sum()
    logger.info(f"Assignment split: {SESSION_ORDER_A}={split_a}, {SESSION_ORDER_B}={split_b}")

    return df


def main():
    """
    Main entry point for generating counterbalance assignments.
    Writes the output to data/processed/counterbalance_assignment.csv
    """
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "counterbalance_assignment.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate assignments (default 100 participants for CI/Testing)
    # In a real scenario, this might be driven by a config or command-line arg
    df = generate_counterbalance_assignments(num_participants=100)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Counterbalance assignments saved to {output_path}")

    # Verify file exists and has content
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("Verification: Output file exists and is non-empty.")
    else:
        logger.error("Verification failed: Output file missing or empty.")
        raise RuntimeError("Failed to write counterbalance assignments.")


if __name__ == "__main__":
    main()
