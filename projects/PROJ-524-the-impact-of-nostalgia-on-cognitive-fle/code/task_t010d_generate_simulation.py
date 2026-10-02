"""
T010d: Generate Simulation Data
Triggered ONLY if T010b (Real Data Fetch) fails.
Generates synthetic WCST data with known effect sizes (nostalgia vs control).
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_synthetic_wcst_data(
    n_participants: int = 200,
    effect_size: float = 0.5,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic WCST data with known effect sizes.
    
    Args:
        n_participants: Total number of participants (100 nostalgia, 100 control)
        effect_size: Expected Cohen's d (nostalgia group performs better = fewer errors)
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with synthetic WCST data
    """
    np.random.seed(seed)
    
    # Ensure even split
    n_per_group = n_participants // 2
    
    # Generate Participant IDs
    participant_ids = [f"PART_{i:04d}" for i in range(n_participants)]
    
    # Assign Stimulus Types
    stimulus_types = ["nostalgia"] * n_per_group + ["control"] * n_per_group
    # Shuffle to avoid order bias
    np.random.shuffle(stimulus_types)
    
    # Generate Ages (all >= 65 as per requirement)
    # Mean 72, SD 6, min 65
    ages = np.random.normal(loc=72, scale=6, size=n_participants).astype(int)
    ages = np.clip(ages, 65, 95)
    
    # Generate MMSE scores (optional, some may be missing)
    # Mean 27, SD 2, min 18, max 30. Introduce ~10% missingness
    mmse_scores = np.random.normal(loc=27, scale=2, size=n_participants).astype(int)
    mmse_scores = np.clip(mmse_scores, 18, 30)
    
    # Randomly set 10% to NaN to simulate missing data
    missing_mask = np.random.random(n_participants) < 0.10
    mmse_scores[missing_mask] = np.nan
    
    # Generate Cognitive Metrics based on Stimulus Type
    # Nostalgia group: Fewer perseverative errors, more categories completed
    # Control group: More errors, fewer categories
    
    # Perseverative Errors (target: Nostalgia < Control)
    # Control: Mean 35, SD 10
    # Nostalgia: Mean = Control - (effect_size * SD)
    control_pe_mean = 35
    control_pe_sd = 10
    nostalgia_pe_mean = control_pe_mean - (effect_size * control_pe_sd)
    
    perseverative_errors = []
    for st in stimulus_types:
        if st == "control":
            val = np.random.normal(control_pe_mean, control_pe_sd)
        else:
            val = np.random.normal(nostalgia_pe_mean, control_pe_sd)
        perseverative_errors.append(max(0, int(val))) # Ensure non-negative
    
    # Categories Completed (target: Nostalgia > Control)
    # Control: Mean 4, SD 1.5
    # Nostalgia: Mean = Control + (effect_size * SD)
    control_cc_mean = 4
    control_cc_sd = 1.5
    nostalgia_cc_mean = control_cc_mean + (effect_size * control_cc_sd)
    
    categories_completed = []
    for st in stimulus_types:
        if st == "control":
            val = np.random.normal(control_cc_mean, control_cc_sd)
        else:
            val = np.random.normal(nostalgia_cc_mean, control_cc_sd)
        categories_completed.append(max(1, min(6, int(val)))) # WCST typically 1-6 categories
    
    # Create DataFrame
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'stimulus_type': stimulus_types,
        'age': ages,
        'MMSE': mmse_scores,
        'perseverative_errors': perseverative_errors,
        'categories_completed': categories_completed
    })
    
    logger.info(f"Generated {len(df)} synthetic records")
    logger.info(f"Stimulus distribution: {df['stimulus_type'].value_counts().to_dict()}")
    logger.info(f"Age range: {df['age'].min()} - {df['age'].max()}")
    
    return df

def save_simulation_metadata(
    output_path: Path,
    source: str = "Methodological Simulation",
    effect_size: float = 0.5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Save metadata indicating simulation mode.
    """
    metadata = {
        "dataset_source": source,
        "validation_study_doi": None,
        "stimuli_checksums": {},
        "simulation_mode": True,
        "simulation_parameters": {
            "effect_size": effect_size,
            "random_seed": seed,
            "n_participants": 200,
            "generation_timestamp": pd.Timestamp.now().isoformat()
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved simulation metadata to {output_path}")
    return metadata

def main():
    """
    Main entry point for T010d.
    Generates synthetic data and saves it to data/raw/raw_dataset.csv
    and metadata to data/raw/metadata.json.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    
    raw_dataset_path = data_raw_dir / "raw_dataset.csv"
    metadata_path = data_raw_dir / "metadata.json"
    
    logger.info("Starting T010d: Generate Simulation Data")
    
    try:
        # Generate data
        logger.info("Generating synthetic WCST data...")
        df = generate_synthetic_wcst_data(
            n_participants=200,
            effect_size=0.5,
            seed=42
        )
        
        # Save CSV
        df.to_csv(raw_dataset_path, index=False)
        logger.info(f"Saved synthetic data to {raw_dataset_path}")
        
        # Verify schema
        required_cols = ['participant_id', 'stimulus_type', 'age', 'perseverative_errors', 'categories_completed']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Verify age constraint
        if df['age'].min() < 65:
            raise ValueError(f"Age constraint violated: min age is {df['age'].min()}")
        
        logger.info("Schema and constraints verified.")
        
        # Save metadata
        save_simulation_metadata(metadata_path)
        
        logger.info("T010d completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate simulation data: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
