import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_analysis_config(config_path: str = "data/metadata/analysis_config.json") -> dict:
    """
    Load the analysis configuration JSON.
    
    Args:
        config_path: Path to the analysis_config.json file.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = json.load(f)
    
    logger.info(f"Loaded analysis config from {config_path}")
    return config

def load_features(features_path: str = "data/processed/features.csv") -> pd.DataFrame:
    """
    Load the primary feature matrix.
    
    Args:
        features_path: Path to the features.csv file.
        
    Returns:
        DataFrame containing the features.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(features_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature file not found: {features_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded features from {features_path} with shape {df.shape}")
    return df

def generate_simulated_med_status(n_subjects: int, seed: int = 42) -> np.ndarray:
    """
    Generate simulated medication status covariate.
    
    Generates a Bernoulli distributed random variable with p=0.5.
    
    Args:
        n_subjects: Number of subjects to simulate.
        seed: Random seed for reproducibility.
        
    Returns:
        NumPy array of shape (n_subjects,) containing 0.0 or 1.0.
    """
    rng = np.random.default_rng(seed)
    # Bernoulli p=0.5
    simulated_med = rng.binomial(n=1, p=0.5, size=n_subjects).astype(float)
    logger.info(f"Generated simulated medication status for {n_subjects} subjects (seed={seed})")
    return simulated_med

def run_sensitivity_analysis(
    config_path: str = "data/metadata/analysis_config.json",
    features_path: str = "data/processed/features.csv",
    output_path: str = "data/processed/features_sim_med.csv"
) -> pd.DataFrame:
    """
    Run the sensitivity analysis data generation pipeline.
    
    This function:
    1. Reads the analysis configuration.
    2. Checks if medication status is available.
    3. If not available, generates a simulated covariate.
    4. Appends the simulated column to the features DataFrame.
    5. Saves the result to a new file.
    
    Args:
        config_path: Path to analysis_config.json.
        features_path: Path to features.csv.
        output_path: Path for the output features_sim_med.csv.
        
    Returns:
        The modified DataFrame with the simulated column.
        
    Raises:
        FileNotFoundError: If config is missing.
        ValueError: If medication status is already available (no simulation needed).
    """
    # 1. Load config
    config = load_analysis_config(config_path)
    
    # 2. Check medication status availability
    medication_status_available = config.get("medication_status_available", False)
    
    if medication_status_available:
        logger.warning("Medication status is already available. No simulation needed.")
        # Load original features and return them without modification, 
        # but strictly speaking the task implies simulation only when false.
        # However, to be safe and produce the output file as requested:
        df = load_features(features_path)
        # Ensure we don't accidentally add a column if it's already there
        if "sim_med_status" in df.columns:
            logger.info("sim_med_status column already exists in features.")
        else:
            logger.info("Adding placeholder sim_med_status column (already available).")
            # We still generate it to satisfy the schema requirement of the output file
            # even if the real data exists, but the task specifically says "If false... generate".
            # We will follow the task strictly: only generate if false.
            raise ValueError("Medication status is available. Simulation is not required per task logic.")
        return df

    # 3. Load features
    df = load_features(features_path)
    n_subjects = len(df)
    
    # 4. Generate simulated covariate
    sim_med = generate_simulated_med_status(n_subjects, seed=42)
    
    # 5. Append to DataFrame
    df["sim_med_status"] = sim_med
    
    # 6. Save to new file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    logger.info(f"Saved sensitivity analysis features to {output_path}")
    logger.info(f"Output shape: {df.shape} (Original: {df.shape[0]}x{df.shape[1]-1}, Added 1 column)")
    
    return df

def main():
    """
    Main entry point for the sensitivity analysis data generation.
    """
    logger.info("Starting Sensitivity Analysis Data Generation (T031)")
    
    try:
        run_sensitivity_analysis()
        logger.info("Sensitivity analysis data generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Configuration file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Simulation skipped: {e}")
        # This is a valid state if medication data exists, but per task spec
        # we might want to exit cleanly or handle it.
        # The task says "If ... false, generate...". If true, we do nothing.
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()