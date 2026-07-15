import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
from ..config import get_project_root, get_data_path
from ..utils.logging import get_logger, log_counterbalance_strategy

def generate_counterbalance_assignments(
    n_participants: int = 100,
    seed: int = 42,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Generate a counterbalance assignment map for participants.
    
    Creates a DataFrame mapping participant IDs to session orders (Low-High vs High-Low)
    using a seeded random shuffle to ensure a 50/50 split.
    
    Args:
        n_participants: Total number of participants to generate assignments for.
        seed: Random seed for reproducibility (default: 42).
        output_path: Optional path to save the CSV. If None, saves to 
                     data/processed/counterbalance_assignment.csv.
                     
    Returns:
        DataFrame with columns: participant_id, session_order
    """
    # Ensure output path
    if output_path is None:
        data_path = get_data_path()
        processed_dir = data_path / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = processed_dir / "counterbalance_assignment.csv"
    
    # Generate participant IDs
    participant_ids = [f"P{str(i).zfill(4)}" for i in range(1, n_participants + 1)]
    
    # Create orders list: ensure exact 50/50 split if possible
    n_low_high = n_participants // 2
    n_high_low = n_participants - n_low_high
    
    orders = ["LOW-HIGH"] * n_low_high + ["HIGH-LOW"] * n_high_low
    
    # Shuffle orders using the seed
    rng = np.random.default_rng(seed)
    rng.shuffle(orders)
    
    # Create DataFrame
    df = pd.DataFrame({
        "participant_id": participant_ids,
        "session_order": orders
    })
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    logger = get_logger(__name__)
    logger.info(f"Generated counterbalance assignments for {n_participants} participants.")
    logger.info(f"Saved to: {output_path}")
    
    return df

def main():
    """
    Entry point for generating counterbalance assignments.
    Also logs the strategy used.
    """
    logger = get_logger(__name__)
    logger.info("Starting counterbalance assignment generation...")
    
    # Log the strategy first
    strategy_log_path = log_counterbalance_strategy()
    logger.info(f"Strategy logged to: {strategy_log_path}")
    
    # Generate assignments (default 100 participants for testing/CI)
    # In a real run, this might be driven by actual participant count
    df = generate_counterbalance_assignments(n_participants=100, seed=42)
    
    # Verify split
    counts = df['session_order'].value_counts()
    logger.info(f"Assignment split: {counts.to_dict()}")
    
    if abs(counts['LOW-HIGH'] - counts['HIGH-LOW']) > 1:
        logger.warning("Warning: Assignment split is not exactly 50/50.")
    else:
        logger.info("Assignment split is balanced.")

if __name__ == "__main__":
    main()