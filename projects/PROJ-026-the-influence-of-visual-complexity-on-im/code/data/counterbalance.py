import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging
from ..utils.logging import log_counterbalance_strategy
from ..config import get_project_root, ensure_directories, get_data_path

def generate_counterbalance_assignments(seed: int = 42, n_participants: int = 100) -> pd.DataFrame:
    """
    Generate counterbalance assignment map for participants.
    
    Creates a mapping of participant IDs to session orders (Low-High vs High-Low).
    Uses a seeded random shuffle to ensure a 50/50 split for each starting condition.
    
    Args:
        seed: Random seed for reproducibility.
        n_participants: Number of participants to generate assignments for.
    
    Returns:
        DataFrame with columns: participant_id, session_order
    """
    np.random.seed(seed)
    
    # Create participant IDs
    participant_ids = [f"P{str(i).zfill(3)}" for i in range(1, n_participants + 1)]
    
    # Generate session orders: 50% "Low-High", 50% "High-Low"
    # Ensure exactly half for even numbers, or as close as possible
    n_low_high = n_participants // 2
    n_high_low = n_participants - n_low_high
    
    orders = ["Low-High"] * n_low_high + ["High-Low"] * n_high_low
    np.random.shuffle(orders)
    
    df = pd.DataFrame({
        "participant_id": participant_ids,
        "session_order": orders
    })
    
    return df

def main():
    """
    Main entry point to generate and save counterbalance assignments.
    Also logs the strategy used.
    """
    root = get_project_root()
    data_path = get_data_path()
    processed_path = data_path / "processed"
    ensure_directories([processed_path])
    
    # Generate assignments
    df = generate_counterbalance_assignments(seed=42, n_participants=100)
    
    # Save to CSV
    output_file = processed_path / "counterbalance_assignment.csv"
    df.to_csv(output_file, index=False)
    logging.info(f"Saved counterbalance assignments to {output_file}")
    
    # Log the strategy
    strategy_text = (
        "Counterbalancing Strategy: AB/BA Design (Low-High vs High-Low)\n"
        "\n"
        "Methodology:\n"
        "- Participants are randomly assigned to one of two session orders.\n"
        "- Group A (Low-High): Starts with Low Complexity stimuli, followed by High Complexity.\n"
        "- Group B (High-Low): Starts with High Complexity stimuli, followed by Low Complexity.\n"
        "\n"
        "Implementation Details:\n"
        "- Random seed set to 42 for reproducibility.\n"
        "- Assignment is a 50/50 split (or as close as possible for odd N).\n"
        "- Generated using numpy.random.shuffle on a pre-balanced list of orders.\n"
        "- Output saved to: data/processed/counterbalance_assignment.csv\n"
        "\n"
        "Purpose:\n"
        "This counterbalancing controls for order effects and practice effects,\n"
        "ensuring that any observed differences in implicit bias (D-scores) are\n"
        "attributable to the visual complexity manipulation rather than the\n"
        "sequence of presentation."
    )
    
    log_counterbalance_strategy(strategy_text, output_file="counterbalance_strategy.log")

if __name__ == "__main__":
    main()
