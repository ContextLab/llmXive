"""
Counterbalance assignment generation module.

Generates a CSV mapping participant IDs to session orders (Low-High vs High-Low)
using a seeded random shuffle to ensure reproducibility across runs.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging
from config import get_project_root, get_data_path
from utils.logging import get_logger, log_counterbalance_strategy

logger = get_logger(__name__)

def generate_counterbalance_assignments(
    participant_ids: List[str],
    seed: int = 42,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Generate counterbalance assignments for a list of participant IDs.

    Assigns each participant to either 'Low-High' or 'High-Low' session order
    using a seeded random shuffle to ensure reproducibility.

    Args:
        participant_ids: List of participant IDs to assign.
        seed: Random seed for reproducibility (default: 42).
        output_path: Path to write the CSV file. If None, uses default path.

    Returns:
        DataFrame with columns: participant_id, session_order, complexity_condition_1, complexity_condition_2

    Raises:
        ValueError: If participant_ids list is empty.
    """
    if not participant_ids:
        raise ValueError("participant_ids list cannot be empty")

    # Set random seed for reproducibility
    np.random.seed(seed)

    # Create session orders: half 'Low-High', half 'High-Low'
    n_participants = len(participant_ids)
    n_low_high = n_participants // 2
    n_high_low = n_participants - n_low_high

    session_orders = (
        ['Low-High'] * n_low_high +
        ['High-Low'] * n_high_low
    )

    # Shuffle the session orders
    np.random.shuffle(session_orders)

    # Create DataFrame
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'session_order': session_orders,
        'complexity_condition_1': [
            'Low' if order == 'Low-High' else 'High'
            for order in session_orders
        ],
        'complexity_condition_2': [
            'High' if order == 'Low-High' else 'Low'
            for order in session_orders
        ]
    })

    # Log the strategy
    if output_path is None:
        output_path = get_data_path('processed/counterbalance_assignment.csv')
    
    log_counterbalance_strategy(
        seed=seed,
        n_participants=n_participants,
        n_low_high=n_low_high,
        n_high_low=n_high_low,
        split_ratio=f"{n_low_high}:{n_high_low}",
        output_path=output_path
    )

    logger.info(f"Generated counterbalance assignments for {n_participants} participants")
    logger.info(f"Split: {n_low_high} Low-High, {n_high_low} High-Low")

    return df

def main():
    """
    Main entry point for generating counterbalance assignments.
    
    This function is called by the main pipeline to ensure session-order
    metadata is always available for both real data and synthetic modes.
    """
    logger.info("Starting counterbalance assignment generation")

    # Get project root and ensure directories exist
    project_root = get_project_root()
    output_path = get_data_path('processed/counterbalance_assignment.csv')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # In a real pipeline, participant IDs would come from the loaded data
    # For now, we read from the aggregated d_scores if available, or generate from stimulus list
    aggregated_path = get_data_path('processed/aggregated_d_scores.csv')
    stimuli_path = get_data_path('processed/complexity_scores.csv')
    
    participant_ids = []
    
    # Try to get participant IDs from aggregated d_scores first
    if os.path.exists(aggregated_path):
        try:
            df_agg = pd.read_csv(aggregated_path)
            participant_ids = df_agg['participant_id'].unique().tolist()
            logger.info(f"Loaded {len(participant_ids)} participant IDs from aggregated d_scores")
        except Exception as e:
            logger.warning(f"Could not load participant IDs from aggregated d_scores: {e}")
    
    # If no participants found, try to infer from complexity scores (stimuli count)
    # This is a fallback for when we need to generate assignments but don't have response data yet
    if not participant_ids and os.path.exists(stimuli_path):
        try:
            df_stim = pd.read_csv(stimuli_path)
            # Use the number of valid stimuli as a proxy for participant count
            # In a real scenario, this would be the number of participants
            n_stimuli = len(df_stim[df_stim['status'] == 'valid'])
            participant_ids = [f"PID_{i:04d}" for i in range(n_stimuli)]
            logger.info(f"Generated {len(participant_ids)} participant IDs from stimuli count")
        except Exception as e:
            logger.warning(f"Could not load participant IDs from complexity scores: {e}")
    
    # If still no participant IDs, raise an error
    if not participant_ids:
        raise RuntimeError(
            "Could not determine participant IDs. "
            "Ensure that either aggregated_d_scores.csv or complexity_scores.csv exists."
        )

    # Generate assignments
    df_assignments = generate_counterbalance_assignments(
        participant_ids=participant_ids,
        seed=42,
        output_path=output_path
    )

    # Save to CSV
    df_assignments.to_csv(output_path, index=False)
    logger.info(f"Counterbalance assignments saved to {output_path}")

    return df_assignments

if __name__ == "__main__":
    main()
