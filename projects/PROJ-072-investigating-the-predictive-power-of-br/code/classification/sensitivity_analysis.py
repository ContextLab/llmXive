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

def load_analysis_config(config_path: Path) -> dict:
    """Load the analysis configuration JSON."""
    if not config_path.exists():
        logger.error(f"Analysis config not found at {config_path}")
        raise FileNotFoundError(f"Analysis config not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def load_features(features_path: Path) -> pd.DataFrame:
    """Load the primary features CSV."""
    if not features_path.exists():
        logger.error(f"Features file not found at {features_path}")
        raise FileNotFoundError(f"Features file not found at {features_path}")
    
    df = pd.read_csv(features_path)
    logger.info(f"Loaded features with shape {df.shape}")
    return df

def generate_simulated_med_status(n_samples: int, seed: int = 42) -> np.ndarray:
    """
    Generate simulated medication status covariate.
    Bernoulli distribution with p=0.5.
    """
    rng = np.random.default_rng(seed)
    # 0 = control, 1 = medicated (arbitrary coding for simulation)
    return rng.binomial(n=1, p=0.5, size=n_samples)

def run_sensitivity_analysis(
    config_path: Path,
    features_path: Path,
    output_path: Path
) -> bool:
    """
    Main logic for T031: Sensitivity analysis data generation.
    
    Reads analysis_config.json. If medication_status_available is false,
    generates simulated covariate and appends to features.csv, saving
    as features_sim_med.csv.
    """
    logger.info("Starting sensitivity analysis data generation (T031)...")
    
    # 1. Load config
    try:
        config = load_analysis_config(config_path)
    except FileNotFoundError:
        logger.warning("Analysis config not found. Assuming medication data unavailable.")
        medication_available = False
    else:
        medication_available = config.get('medication_status_available', False)
    
    # 2. Check condition
    if medication_available:
        logger.info("medication_status_available is True. Skipping simulation.")
        logger.info("No new file generated. Primary analysis has real data.")
        return True
    
    logger.info("medication_status_available is False. Generating simulated covariate.")
    
    # 3. Load features
    try:
        df_features = load_features(features_path)
    except FileNotFoundError:
        logger.error("Cannot proceed: features.csv not found. US2 must complete first.")
        return False
    
    if df_features.empty:
        logger.error("Features dataframe is empty.")
        return False
    
    # 4. Generate simulation
    n_subjects = len(df_features)
    logger.info(f"Generating simulated medication status for {n_subjects} subjects.")
    
    sim_med_status = generate_simulated_med_status(n_subjects, seed=42)
    
    # 5. Append to dataframe
    df_sim = df_features.copy()
    df_sim['sim_med_status'] = sim_med_status
    
    # 6. Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_sim.to_csv(output_path, index=False)
    
    logger.info(f"Successfully saved simulated features to {output_path}")
    logger.info(f"New shape: {df_sim.shape}")
    logger.info(f"Columns: {list(df_sim.columns)}")
    
    return True

def main():
    """Entry point for T031."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / 'data' / 'metadata' / 'analysis_config.json'
    features_path = project_root / 'data' / 'processed' / 'features.csv'
    output_path = project_root / 'data' / 'processed' / 'features_sim_med.csv'
    
    success = run_sensitivity_analysis(config_path, features_path, output_path)
    
    if not success:
        logger.error("Sensitivity analysis generation failed.")
        sys.exit(1)
    else:
        logger.info("Sensitivity analysis generation completed successfully.")
        sys.exit(0)

if __name__ == '__main__':
    main()
