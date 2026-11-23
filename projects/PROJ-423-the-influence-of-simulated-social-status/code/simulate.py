import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

# Import from sibling modules as per API surface
from config import (
    load_simulation_params,
    get_effect_size_high_low,
    get_effect_size_interaction,
    get_sample_size,
    get_random_seed,
    get_injected_interaction_effect,
)
from utils import set_seed, ensure_directory, save_json
from logger import setup_logger, get_logger

logger = setup_logger("simulate", "logs/simulate.log")

def generate_synthetic_data(
    n_subjects: int,
    seed: int,
    effect_high_low: float,
    effect_interaction: float,
    design_type: str = "between-subjects",
) -> pd.DataFrame:
    """
    Generates synthetic data for the social status risk-taking simulation.
    
    This function creates a dataset based on the hypothesized effect sizes
    derived from meta-analysis (stored in simulation_parameters.json).
    
    Args:
        n_subjects: Number of unique participants to simulate.
        seed: Random seed for reproducibility.
        effect_high_low: Cohen's d for the main effect of status.
        effect_interaction: Cohen's d for the status x behavior interaction.
        design_type: 'between-subjects' or 'within-subjects'.
        
    Returns:
        A pandas DataFrame containing the simulated dataset.
    """
    set_seed(seed)
    logger.info(f"Generating synthetic data with N={n_subjects} and seed={seed}")
    
    # Define conditions
    conditions = [
        ("High", "Risky"),
        ("High", "Conservative"),
        ("Low", "Risky"),
        ("Low", "Conservative"),
    ]
    
    data = []
    
    if design_type == "between-subjects":
        # Each participant sees only one condition
        subjects_per_condition = n_subjects // len(conditions)
        remainder = n_subjects % len(conditions)
        
        base_mean = 50.0
        base_std = 10.0
        
        for i, (status, behavior) in enumerate(conditions):
            count = subjects_per_condition + (1 if i < remainder else 0)
            
            # Calculate condition mean based on effect sizes
            # Simplified mapping: status effect adds/subtracts d/2, interaction adds d/2
            status_effect = (effect_high_low / 2) if status == "High" else (-effect_high_low / 2)
            behavior_effect = 0.0 # Main effect of behavior not explicitly parameterized, assume 0 for now
            interaction_effect = 0.0
            
            if status == "High" and behavior == "Risky":
                interaction_effect = effect_interaction / 2
            elif status == "Low" and behavior == "Conservative":
                interaction_effect = -effect_interaction / 2
            
            condition_mean = base_mean + status_effect + interaction_effect
            condition_std = base_std
            
            for _ in range(count):
                score = np.random.normal(condition_mean, condition_std)
                data.append({
                    "participant_id": f"sub_{len(data):04d}",
                    "status_level": status,
                    "observed_behavior": behavior,
                    "risk_taking_score": score
                })
                
    elif design_type == "within-subjects":
        # Each participant sees all conditions
        for subj_idx in range(n_subjects):
            base_mean = 50.0 + np.random.normal(0, 2) # Subject random intercept
            base_std = 10.0
            
            for status, behavior in conditions:
                status_effect = (effect_high_low / 2) if status == "High" else (-effect_high_low / 2)
                interaction_effect = 0.0
                
                if status == "High" and behavior == "Risky":
                    interaction_effect = effect_interaction / 2
                elif status == "Low" and behavior == "Conservative":
                    interaction_effect = -effect_interaction / 2
                
                condition_mean = base_mean + status_effect + interaction_effect
                score = np.random.normal(condition_mean, base_std)
                
                data.append({
                    "participant_id": f"sub_{subj_idx:04d}",
                    "status_level": status,
                    "observed_behavior": behavior,
                    "risk_taking_score": score
                })
    else:
        raise ValueError(f"Unsupported design_type: {design_type}")
        
    return pd.DataFrame(data)

def validate_design_adherence(df: pd.DataFrame) -> bool:
    """
    Validates that the generated data adheres to the experimental design.
    
    Checks:
    1. All required columns exist.
    2. Categorical factors have expected levels.
    3. **Variance Check**: status_level must have variance (not all same).
    
    Args:
        df: The generated DataFrame.
        
    Returns:
        True if validation passes.
        
    Raises:
        ValueError: If validation fails (e.g., no variance in status_level).
    """
    required_cols = ["participant_id", "status_level", "observed_behavior", "risk_taking_score"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Check categorical levels
    expected_status = {"High", "Low"}
    expected_behavior = {"Risky", "Conservative"}
    
    if not set(df["status_level"].unique()).issubset(expected_status):
        raise ValueError(f"Invalid status_level values found: {df['status_level'].unique()}")
        
    if not set(df["observed_behavior"].unique()).issubset(expected_behavior):
        raise ValueError(f"Invalid observed_behavior values found: {df['observed_behavior'].unique()}")
    
    # --- CRITICAL VALIDATION FOR T011 ---
    # Check for variance in status_level
    if df["status_level"].nunique() < 2:
        raise ValueError("Error: status_level has no variance. Experimental condition integrity violated.")
    
    # Check for variance in observed_behavior
    if df["observed_behavior"].nunique() < 2:
        raise ValueError("Error: observed_behavior has no variance. Experimental condition integrity violated.")
        
    logger.info("Validation passed: Data structure and variance checks successful.")
    return True

def main():
    """
    Main entry point for the simulation script.
    Parses arguments, generates data, validates, and saves output.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic research data for status-risk simulation")
    parser.add_argument("--output", type=str, default="data/raw/simulation_output.csv",
                      help="Path to save the output CSV")
    parser.add_argument("--config", type=str, default="code/simulation_parameters.json",
                      help="Path to the simulation parameters JSON")
    parser.add_argument("--seed", type=int, default=None,
                      help="Override random seed (optional)")
    
    args = parser.parse_args()
    
    try:
        # Load parameters
        if os.path.exists(args.config):
            with open(args.config, "r") as f:
                params = json.load(f)
        else:
            # Fallback to config module if file missing, though task implies file exists
            logger.warning(f"Config file {args.config} not found. Using defaults from config module.")
            params = {}
        
        n_subjects = params.get("n_subjects", get_sample_size())
        seed = args.seed if args.seed is not None else params.get("random_seed", get_random_seed())
        effect_high_low = params.get("effect_high_low", get_effect_size_high_low())
        effect_interaction = params.get("injected_interaction_effect", get_effect_size_interaction())
        design_type = params.get("design_type", "between-subjects")
        
        # Ensure output directory exists
        ensure_directory(args.output)
        
        logger.info(f"Starting simulation: N={n_subjects}, Design={design_type}")
        
        # Generate data
        df = generate_synthetic_data(
            n_subjects=n_subjects,
            seed=seed,
            effect_high_low=effect_high_low,
            effect_interaction=effect_interaction,
            design_type=design_type
        )
        
        # Validate data
        validate_design_adherence(df)
        
        # Save output
        df.to_csv(args.output, index=False)
        logger.info(f"Successfully saved simulation output to {args.output}")
        
        # Save metadata for checksums
        metadata = {
            "n_subjects": n_subjects,
            "design_type": design_type,
            "seed": seed,
            "status_levels": list(df["status_level"].unique()),
            "behavior_levels": list(df["observed_behavior"].unique())
        }
        meta_path = args.output.replace(".csv", "_meta.json")
        save_json(metadata, meta_path)
        
    except ValueError as e:
        logger.error(f"Simulation or validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during simulation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()