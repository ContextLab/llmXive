import os
import sys
import json
import argparse
import pandas as pd
import numpy as np

from config import load_simulation_params, get_random_seed, get_effect_size_high_low, get_effect_size_interaction, get_sample_size
from logger import setup_logger
from utils import set_seed, ensure_directory, calculate_checksum, update_checksums

logger = setup_logger("simulate", "logs/simulate.log")

def generate_synthetic_data(n_subjects: int, seed: int, effect_size_high: float, effect_size_interaction: float) -> pd.DataFrame:
    """
    Generates synthetic data for the social status risk experiment.
    
    Args:
        n_subjects: Number of unique participants.
        seed: Random seed for reproducibility.
        effect_size_high: Base effect size for high status.
        effect_size_interaction: Interaction effect size.
        
    Returns:
        DataFrame with simulated participant data.
    """
    set_seed(seed)
    logger.info(f"Generating synthetic data with N={n_subjects} and seed={seed}")

    # Define conditions: 2 (Status: High/Low) x 2 (Behavior: Risky/Conservative)
    # We simulate a between-subjects design for this initial generation
    # to match the typical requirement of T011 validation (variance check).
    # 4 groups total.
    group_size = n_subjects // 4
    remainder = n_subjects % 4
    
    status_levels = ['High', 'Low', 'High', 'Low']
    observed_behaviors = ['Risky', 'Risky', 'Conservative', 'Conservative']
    
    # Generate participant IDs
    participant_ids = [f"P{i}" for i in range(1, n_subjects + 1)]
    
    # Assign conditions
    data = []
    idx = 0
    for i, (status, behavior) in enumerate(zip(status_levels, observed_behaviors)):
        count = group_size + (1 if i < remainder else 0)
        for _ in range(count):
            data.append({
                'participant_id': participant_ids[idx],
                'status_level': status,
                'observed_behavior': behavior
            })
            idx += 1
    
    df = pd.DataFrame(data)
    
    # Generate risk_taking_score based on parameters
    # Base score
    base_score = 50.0
    # Status effect (High > Low)
    status_effect = np.where(df['status_level'] == 'High', effect_size_high, 0.0)
    # Behavior effect (Risky > Conservative) - assumed main effect
    behavior_effect = np.where(df['observed_behavior'] == 'Risky', 10.0, -10.0)
    # Interaction effect
    interaction_mask = (df['status_level'] == 'High') & (df['observed_behavior'] == 'Risky')
    interaction_effect = np.where(interaction_mask, effect_size_interaction, 0.0)
    
    # Noise
    noise = np.random.normal(0, 10.0, size=len(df))
    
    df['risk_taking_score'] = base_score + status_effect + behavior_effect + interaction_effect + noise
    
    return df

def validate_design_adherence(df: pd.DataFrame) -> bool:
    """
    Validates that the generated data has the required variance in status_level.
    
    Constraint: Must raise a ValueError if status_level has no variance.
    
    Args:
        df: The generated DataFrame.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If experimental condition integrity is violated.
    """
    if 'status_level' not in df.columns:
        raise ValueError("Error: status_level column missing.")
    
    unique_statuses = df['status_level'].unique()
    if len(unique_statuses) < 2:
        # This triggers the specific error message required by T011
        raise ValueError("Error: status_level has no variance. Experimental condition integrity violated.")
    
    logger.info(f"Validation passed: Found {len(unique_statuses)} unique status levels: {list(unique_statuses)}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic research data for social status risk experiment.")
    parser.add_argument('--output', type=str, default='data/raw/simulation_output.csv',
                        help='Path to save the generated CSV.')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed. If None, uses seed from config.')
    args = parser.parse_args()

    try:
        # Load parameters
        params = load_simulation_params()
        seed = args.seed if args.seed is not None else params.get('random_seed', 42)
        n_subjects = params.get('n_subjects', 200)
        effect_size_high = params.get('effect_size_high', 0.5)
        effect_size_interaction = params.get('effect_size_interaction', 0.3)

        # Generate data
        df = generate_synthetic_data(n_subjects, seed, effect_size_high, effect_size_interaction)

        # Validate design adherence (T011 requirement)
        validate_design_adherence(df)

        # Ensure output directory exists
        ensure_directory(args.output)

        # Save to CSV
        df.to_csv(args.output, index=False)
        logger.info(f"Data saved to {args.output}")

        # Update checksums
        update_checksums(args.output)

        print(f"Success: Generated {len(df)} rows with seed {seed}.")

    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during simulation: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()