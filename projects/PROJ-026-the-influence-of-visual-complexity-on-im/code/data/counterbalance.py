import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
from ..config import get_project_root, get_data_path

def generate_counterbalance_assignments(
    n_participants: int = 100,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate counterbalance assignments for participants.
    
    Args:
        n_participants: Number of participants.
        seed: Random seed.
        
    Returns:
        DataFrame with participant IDs and session orders.
    """
    np.random.seed(seed)
    
    participant_ids = [f"P{i:03d}" for i in range(1, n_participants + 1)]
    orders = np.random.choice(["Low-High", "High-Low"], size=n_participants)
    
    # Ensure roughly 50/50 split
    low_high_count = np.sum(orders == "Low-High")
    high_low_count = n_participants - low_high_count
    
    diff = abs(low_high_count - high_low_count)
    if diff > 1:
        # Adjust to be as close to 50/50 as possible
        target = n_participants // 2
        if low_high_count > target:
            indices = np.where(orders == "Low-High")[0][:low_high_count - target]
            orders[indices] = "High-Low"
        else:
            indices = np.where(orders == "High-Low")[0][:high_low_count - target]
            orders[indices] = "Low-High"
    
    df = pd.DataFrame({
        "participant_id": participant_ids,
        "session_order": orders
    })
    
    return df

def main() -> int:
    """Main entry point for counterbalance generation."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    data_path = get_data_path()
    output_path = data_path / "processed" / "counterbalance_assignment.csv"
    
    try:
        df = generate_counterbalance_assignments(n_participants=100, seed=42)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logging.info(f"Generated counterbalance assignments at {output_path}")
        return 0
    except Exception as e:
        logging.error(f"Failed to generate assignments: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
