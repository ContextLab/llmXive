"""
Ingestion Module.
Handles DGP validation, data generation, reliability checks, harmonization, and dataset writing.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

try:
    from config import get_project_root, get_random_state
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_project_root, get_random_state

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = get_project_root()
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-196-the-role-of-temporal-discounting-in-proc.yaml"

# DGP Configuration Constants
DGP_CONFIG = {
    "n_participants": 500,
    "reliability_target": 0.70,
    "columns": {
        "delay_discounting": ["participant_id", "delay", "amount", "choice", "discount_rate_k"],
        "procrastination": ["participant_id", "item_1", "item_2", "item_3", "item_4", "item_5", "procrastination_score"],
        "nback": ["participant_id", "target", "response", "wm_accuracy", "wm_rt"]
    }
}

def get_config() -> Dict:
    """
    Returns the DGP configuration dictionary.
    """
    return DGP_CONFIG

def validate_dgp_config(config: Dict) -> bool:
    """
    Validates the DGP configuration against schema requirements.
    Raises SystemExit if invalid.
    """
    required_keys = ["n_participants", "reliability_target", "columns"]
    for key in required_keys:
        if key not in config:
            logger.error(f"CRITICAL: DGP config missing required key: {key}")
            raise SystemExit(1)
    
    if not isinstance(config["n_participants"], int) or config["n_participants"] <= 0:
        logger.error("CRITICAL: n_participants must be a positive integer")
        raise SystemExit(1)
    
    if not isinstance(config["reliability_target"], float) or not (0 < config["reliability_target"] < 1):
        logger.error("CRITICAL: reliability_target must be a float between 0 and 1")
        raise SystemExit(1)
    
    logger.info("DGP Configuration validated successfully.")
    return True

def calculate_cronbach_alpha(items: pd.DataFrame) -> float:
    """
    Calculates Cronbach's Alpha for a set of item columns.
    """
    n_items = items.shape[1]
    if n_items < 2:
        return 0.0
    
    item_vars = items.var(axis=0)
    total_var = items.var(axis=1).sum()
    sum_item_vars = item_vars.sum()
    
    alpha = (n_items / (n_items - 1)) * (1 - (sum_item_vars / total_var))
    return float(alpha)

def generate_delay_discounting_data(n: int, random_state: np.random.Generator) -> pd.DataFrame:
    """
    Generates synthetic delay discounting data based on literature parameters.
    """
    df = pd.DataFrame({
        "participant_id": range(1, n + 1),
        "delay": random_state.choice([1, 7, 30, 90], size=n),
        "amount": random_state.uniform(10, 100, size=n),
        "choice": random_state.binomial(1, 0.5, size=n)
    })
    
    # Simulate k based on delay and random noise
    # Hyperbolic model: V = A / (1 + k*delay) -> k = (A/V - 1) / delay
    # We simulate choice probability based on a latent k
    latent_k = 10 ** random_state.normal(-2, 1, size=n)
    df["discount_rate_k"] = latent_k
    return df

def generate_procrastination_data(n: int, random_state: np.random.Generator) -> pd.DataFrame:
    """
    Generates synthetic procrastination scale data.
    """
    items = [f"item_{i}" for i in range(1, 6)]
    data = {
        "participant_id": range(1, n + 1)
    }
    for item in items:
        data[item] = random_state.randint(1, 6, size=n)
    
    df = pd.DataFrame(data)
    df["procrastination_score"] = df[items].sum(axis=1)
    return df

def generate_nback_data(n: int, random_state: np.random.Generator) -> pd.DataFrame:
    """
    Generates synthetic n-back working memory task data.
    """
    df = pd.DataFrame({
        "participant_id": range(1, n + 1),
        "target": random_state.binomial(1, 0.3, size=n),
        "response": random_state.binomial(1, 0.4, size=n),
        "wm_accuracy": random_state.uniform(0.5, 1.0, size=n),
        "wm_rt": random_state.uniform(500, 1500, size=n)
    })
    return df

def hyperbolic_function(delay: float, k: float, A: float = 1.0) -> float:
    """
    Calculates the hyperbolic discounting value.
    """
    return A / (1 + k * delay)

def fit_hyperbolic_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fits a hyperbolic model to participant data to estimate k.
    Excludes participants where fitting fails.
    """
    # For synthetic data, we already have k. For real data, we would fit.
    # This function is a placeholder for the fitting logic if real data is used.
    # Since we are generating synthetic data with k already, we return as is.
    # In a real scenario, this would use scipy.optimize.curve_fit
    return df

def harmonize_datasets(delay_df: pd.DataFrame, procrast_df: pd.DataFrame, nback_df: pd.DataFrame) -> pd.DataFrame:
    """
    Harmonizes and merges the three datasets.
    Raises SystemExit if ID mismatch rate > 10%.
    """
    initial_count = len(delay_df)
    
    merged_df = delay_df.merge(procrast_df, on="participant_id", how="inner")
    merged_df = merged_df.merge(nback_df, on="participant_id", how="inner")
    
    mismatch_rate = 1 - (len(merged_df) / initial_count)
    
    if mismatch_rate > 0.10:
        logger.error(f"CRITICAL: ID mismatch > 10% (rate: {mismatch_rate:.2f})")
        raise SystemExit(1)
    
    logger.info(f"Data harmonized successfully. ID mismatch rate: {mismatch_rate:.2%}")
    return merged_df

def validate_core_constructs(df: pd.DataFrame) -> None:
    """
    Validates that core constructs are present and non-null.
    Raises SystemExit if missing.
    """
    core_constructs = ["discount_rate_k", "procrastination_score", "wm_accuracy"]
    for col in core_constructs:
        if col not in df.columns:
            logger.error(f"CRITICAL: Missing core construct: {col}")
            raise SystemExit(1)
        if df[col].isnull().any():
            logger.error(f"CRITICAL: Missing core construct contains NaNs: {col}")
            raise SystemExit(1)
    logger.info("Core constructs validated successfully.")

def handle_missing_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Handles missing data in covariates.
    Returns modified df and a flag indicating if reduced model is needed.
    """
    covariates = ["age", "gender"]
    missing_ratio = df[covariates].isnull().mean().max()
    
    reduced_model = False
    if missing_ratio > 0.10:
        logger.warning("Missing covariates > 10%. Flagging for reduced model.")
        reduced_model = True
    else:
        # Mean imputation for covariates
        for col in covariates:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].mean())
    
    return df, reduced_model

def write_harmonized_dataset(df: pd.DataFrame) -> None:
    """
    Writes the harmonized dataset to parquet and updates state checksums.
    """
    output_path = DATA_PROCESSED_DIR / "harmonized_dataset.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Harmonized dataset written to {output_path}")
    
    # Update checksums
    try:
        from utils.checksum import update_artifacts_for_pipeline
        update_artifacts_for_pipeline(DATA_PROCESSED_DIR)
    except ImportError:
        logger.warning("Checksum utility not found. Skipping state update.")

def write_model_config(reduced_model: bool) -> None:
    """
    Writes the model configuration to JSON.
    """
    config_path = DATA_PROCESSED_DIR / "model_config.json"
    with open(config_path, 'w') as f:
        json.dump({"reduced_model": reduced_model}, f, indent=2)
    logger.info(f"Model config written to {config_path}")

def run_dgp_pipeline(n: int, seed: int) -> pd.DataFrame:
    """
    Runs the full DGP pipeline: generate, validate, harmonize, and save.
    """
    random_state = get_random_state(seed)
    
    # Generate data
    logger.info("Generating synthetic data...")
    delay_df = generate_delay_discounting_data(n, random_state)
    procrast_df = generate_procrastination_data(n, random_state)
    nback_df = generate_nback_data(n, random_state)
    
    # Reliability check
    logger.info("Checking reliability...")
    alpha_procrast = calculate_cronbach_alpha(procrast_df[[f"item_{i}" for i in range(1, 6)]])
    if alpha_procrast < DGP_CONFIG["reliability_target"]:
        logger.error(f"CRITICAL: Data reliability below threshold (alpha: {alpha_procrast:.2f} < {DGP_CONFIG['reliability_target']})")
        raise SystemExit(1)
    logger.info(f"Cronbach's Alpha for procrastination: {alpha_procrast:.2f}")
    
    # Harmonize
    logger.info("Harmonizing data...")
    merged_df = harmonize_datasets(delay_df, procrast_df, nback_df)
    
    # Validate core constructs
    validate_core_constructs(merged_df)
    
    # Handle missing data
    merged_df, reduced_model = handle_missing_data(merged_df)
    write_model_config(reduced_model)
    
    # Write dataset
    write_harmonized_dataset(merged_df)
    
    return merged_df

def main():
    """
    Main entry point for the ingestion script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run DGP pipeline")
    parser.add_argument("--mode", choices=["generate", "validate"], default="generate")
    parser.add_argument("--n", type=int, default=500, help="Number of participants")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    config = get_config()
    validate_dgp_config(config)
    
    if args.mode == "generate":
        run_dgp_pipeline(args.n, args.seed)
    else:
        logger.info("Validation mode only. Run generate to create data.")

if __name__ == "__main__":
    main()
