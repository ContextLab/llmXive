import os
import json
import pandas as pd
import numpy as np
from scipy import signal
from typing import Dict, Any
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TRAIN_END
from code import logger
from code.analysis.neff import calculate_neff
from code.analysis.correlation import load_synced_data

def calculate_global_thresholds() -> Dict[str, Any]:
    """
    Calculate global Neff values for all variables and the Bonferroni-adjusted alpha.
    
    Returns a dictionary containing:
    - neff_values: dict mapping variable name to calculated Neff
    - alpha_adj: float (0.05 / 30)
    - total_tests: int (30)
    - train_period: tuple (TRAIN_START, TRAIN_END)
    """
    logger.info("Loading synced data for global threshold calculation...")
    df = load_synced_data()
    
    # Filter to training period (1998-2017) as per config
    df_train = df[
        (df['timestamp'].dt.year >= TRAIN_START) & 
        (df['timestamp'].dt.year <= TRAIN_END)
    ].copy()
    
    if df_train.empty:
        raise ValueError("No data available in the training period (1998-2017).")
    
    logger.info(f"Training data shape: {df_train.shape}")
    
    # Calculate Neff for each ACE and NOAA variable
    neff_values = {}
    all_vars = ACE_VARS + NOAA_VARS
    
    for var in all_vars:
        if var in df_train.columns:
            series = df_train[var].dropna()
            if len(series) > 10:  # Need sufficient data
                neff = calculate_neff(series)
                neff_values[var] = float(neff)
                logger.info(f"Neff calculated for {var}: {neff:.2f}")
            else:
                logger.warning(f"Insufficient data for {var} to calculate Neff")
        else:
            logger.warning(f"Variable {var} not found in dataset, skipping Neff calculation")
    
    # Bonferroni correction: alpha = 0.05 / 30 (fixed global divisor)
    total_tests = 30  # 3 params * 2 indices * 5 lags
    alpha_adj = 0.05 / total_tests
    
    result = {
        "neff_values": neff_values,
        "alpha_adj": float(alpha_adj),
        "total_tests": total_tests,
        "train_period": [TRAIN_START, TRAIN_END],
        "description": "Global significance thresholds calculated on full training dataset (1998-2017)"
    }
    
    return result

def validate_threshold_schema(data: Dict[str, Any]) -> bool:
    """
    Validate the threshold data against the expected schema.
    Returns True if valid, raises ValueError if invalid.
    """
    required_keys = ["neff_values", "alpha_adj", "total_tests", "train_period"]
    
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in threshold data: {key}")
    
    if not isinstance(data["neff_values"], dict):
        raise ValueError("neff_values must be a dictionary")
    
    if not isinstance(data["alpha_adj"], (int, float)):
        raise ValueError("alpha_adj must be a number")
    
    if not isinstance(data["total_tests"], int):
        raise ValueError("total_tests must be an integer")
    
    if not isinstance(data["train_period"], list) or len(data["train_period"]) != 2:
        raise ValueError("train_period must be a list of two elements [start, end]")
    
    return True

def write_global_thresholds(output_path: str = "artifacts/thresholds/global_threshold.json") -> str:
    """
    Calculate global thresholds and write them to a JSON file.
    Validates against schema before writing.
    
    Args:
        output_path: Path to write the JSON file
        
    Returns:
        The path where the file was written
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info("Calculating global thresholds...")
    thresholds = calculate_global_thresholds()
    
    logger.info("Validating threshold data against schema...")
    validate_threshold_schema(thresholds)
    
    logger.info(f"Writing thresholds to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(thresholds, f, indent=2)
    
    logger.info(f"Global thresholds successfully written to {output_path}")
    return output_path
