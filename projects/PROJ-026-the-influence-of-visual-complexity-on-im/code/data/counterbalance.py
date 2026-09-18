import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)
SEED = 42


def generate_counterbalance_assignments(
    n_participants: int = 100,
    split_ratio: float = 0.5,
    seed: int = SEED
) -> pd.DataFrame:
    """
    Generate counterbalance assignments for participants.

    Args:
        n_participants: Number of participants
        split_ratio: Ratio of participants starting with Low complexity
        seed: Random seed for reproducibility

    Returns:
        DataFrame with participant_id and session_order
    """
    rng = np.random.default_rng(seed)

    # Generate participant IDs
    participant_ids = [f"participant_{i:03d}" for i in range(n_participants)]

    # Assign session orders
    # session_order: 'Low-High' or 'High-Low'
    n_low_first = int(n_participants * split_ratio)
    n_high_first = n_participants - n_low_first

    orders = ['Low-High'] * n_low_first + ['High-Low'] * n_high_first
    rng.shuffle(orders)

    df = pd.DataFrame({
        'participant_id': participant_ids,
        'session_order': orders
    })

    logger.info(f"Generated {n_participants} counterbalance assignments")
    logger.info(f"  Low-High: {n_low_first}")
    logger.info(f"  High-Low: {n_high_first}")

    return df


def main() -> None:
    """Main entry point for counterbalance generation."""
    root = get_project_root()
    output_path = root / "data" / "processed" / "counterbalance_assignment.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate assignments
    df = generate_counterbalance_assignments()

    # Save
    df.to_csv(output_path, index=False)
    logger.info(f"Saved counterbalance assignments to {output_path}")


if __name__ == "__main__":
    main()
