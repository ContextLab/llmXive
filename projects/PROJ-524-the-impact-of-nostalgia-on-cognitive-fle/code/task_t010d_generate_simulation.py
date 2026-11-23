import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

logger = logging.getLogger(__name__)

def generate_synthetic_wcst_data(n_participants: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic WCST (Wisconsin Card Sorting Test) data for simulation purposes.
    
    Parameters:
    -----------
    n_participants : int
        Number of participants to generate.
    seed : int
        Random seed for reproducibility.
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with synthetic WCST data.
    """
    np.random.seed(seed)
    
    # Generate participant IDs
    participant_ids = [f"PID_{i:04d}" for i in range(1, n_participants + 1)]
    
    # Generate ages (65-85 as per requirement)
    ages = np.random.randint(65, 86, size=n_participants)
    
    # Generate stimulus types (nostalgia/control)
    stimulus_types = np.random.choice(['nostalgia', 'control'], size=n_participants)
    
    # Generate perseverative errors (simulating WCST metric)
    # Nostalgia group typically shows fewer errors
    base_errors = np.random.normal(loc=15, scale=5, size=n_participants)
    # Apply a small effect for nostalgia group (lower errors)
    nostalgia_mask = stimulus_types == 'nostalgia'
    base_errors[nostalgia_mask] = base_errors[nostalgia_mask] - 2.0
    perseverative_errors = np.clip(base_errors, 0, 50).round(2)
    
    # Generate categories completed (simulating WCST metric)
    # Nostalgia group typically completes more categories
    base_categories = np.random.normal(loc=4, scale=1.5, size=n_participants)
    base_categories[nostalgia_mask] = base_categories[nostalgia_mask] + 0.5
    categories_completed = np.clip(base_categories, 0, 7).round(2)
    
    # Optional MMSE scores (24-30 for healthy aging, some impairment)
    mmse_scores = np.random.normal(loc=27, scale=2, size=n_participants)
    # Introduce some missing values (5% missing rate)
    missing_mask = np.random.random(size=n_participants) < 0.05
    mmse_scores[missing_mask] = np.nan
    mmse_scores = np.clip(mmse_scores, 0, 30).round(1)
    
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'age': ages,
        'stimulus_type': stimulus_types,
        'perseverative_errors': perseverative_errors,
        'categories_completed': categories_completed,
        'MMSE': mmse_scores
    })
    
    return df

def save_simulation_metadata(metadata: Dict[str, Any], path: str) -> None:
    """Saves simulation metadata to a JSON file."""
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)
    log_info(f"Simulation metadata saved to {path}")

def main():
    """Main entry point for simulation data generation task."""
    setup_logging()
    config = get_config()
    ensure_dirs()
    
    log_info("Starting simulation data generation (T010d)...")
    
    # Generate synthetic data
    df = generate_synthetic_wcst_data(n_participants=200, seed=42)
    
    # Validate age constraint (all >= 65)
    if (df['age'] < 65).any():
        log_error("ERROR: Generated data contains participants with age < 65")
        raise ValueError("Age constraint violation: all participants must be >= 65")
    
    log_info(f"Generated {len(df)} synthetic participant records")
    log_info(f"Age range: {df['age'].min()} - {df['age'].max()}")
    log_info(f"Stimulus distribution: {df['stimulus_type'].value_counts().to_dict()}")
    
    # Save raw dataset
    raw_path = Path(config['data_raw_dir']) / 'raw_dataset.csv'
    df.to_csv(raw_path, index=False)
    log_info(f"Raw dataset saved to {raw_path}")
    
    # Prepare and save metadata
    metadata = {
        "dataset_source": "SIMULATION_MODE",
        "validation_study_doi": None,
        "simulation_mode": True,
        "generation_timestamp": get_timestamp(),
        "n_participants": len(df),
        "age_range": [int(df['age'].min()), int(df['age'].max())],
        "stimulus_distribution": df['stimulus_type'].value_counts().to_dict(),
        "INFO_SIMULATION_MODE": "This dataset was generated synthetically for methodological simulation as real data was unavailable."
    }
    
    metadata_path = Path(config['data_raw_dir']) / 'metadata.json'
    save_simulation_metadata(metadata, str(metadata_path))
    
    log_info("Simulation data generation completed successfully.")
    log_info("All outputs labeled as SIMULATION_MODE.")

if __name__ == "__main__":
    main()