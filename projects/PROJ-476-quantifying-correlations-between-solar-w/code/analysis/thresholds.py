import os
import json
import pandas as pd
import numpy as np
from scipy import signal
from typing import Dict, Any
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TRAIN_END
from code import logger
from code.analysis.neff import calculate_neff

def calculate_global_thresholds() -> Dict[str, Any]:
    """
    Calculate global Neff values and Bonferroni threshold for the full training period.
    
    Returns a dictionary containing:
    - neff_values: Dict mapping variable names to their calculated Neff
    - alpha_adj: The Bonferroni-adjusted alpha level (0.05 / 30)
    - total_tests: The fixed global divisor (30)
    - period: The time period used for calculation
    """
    # Load the full training dataset
    data_path = "data/processed/synced.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Required input file not found: {data_path}. "
            "Please run the US1 pipeline (T016) first to generate synced.csv."
        )
    
    df = pd.read_csv(data_path)
    
    # Filter to training period (1998-2017)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    train_df = df[
        (df['timestamp'].dt.year >= TRAIN_START) & 
        (df['timestamp'].dt.year <= TRAIN_END)
    ]
    
    if len(train_df) == 0:
        raise ValueError(f"No data found for training period {TRAIN_START}-{TRAIN_END}")
    
    logger.info(f"Calculating global thresholds on {len(train_df)} samples from {TRAIN_START} to {TRAIN_END}")
    
    neff_results = {}
    
    # Calculate Neff for all ACE and NOAA variables in the training set
    all_vars = ACE_VARS + NOAA_VARS
    for var in all_vars:
        if var in train_df.columns:
            series = train_df[var].dropna().values
            if len(series) > 10:  # Minimum samples for meaningful autocorrelation
                neff = calculate_neff(series)
                neff_results[var] = float(neff)
                logger.info(f"  {var}: Neff = {neff:.2f} (N={len(series)})")
            else:
                logger.warning(f"  {var}: Insufficient data points ({len(series)}) for Neff calculation")
                neff_results[var] = None
        else:
            logger.warning(f"  {var}: Column not found in dataset")
            neff_results[var] = None
    
    # Bonferroni correction: alpha_adj = 0.05 / 30
    # 3 parameters (N_p, T_p, He2+_ratio) * 2 indices (Kp, Dst) * 5 lags (0,1,2,3,6h) = 30
    total_tests = 30
    alpha = 0.05
    alpha_adj = alpha / total_tests
    
    threshold_data = {
        "neff_values": neff_results,
        "alpha_adj": float(alpha_adj),
        "total_tests": total_tests,
        "period": {
            "start": TRAIN_START,
            "end": TRAIN_END
        },
        "variables": {
            "ace": ACE_VARS,
            "noaa": NOAA_VARS
        },
        "methodology": {
            "neff_formula": "N * (1 - rho_1) / (1 + rho_1)",
            "preprocessing": "scipy.signal.detrend applied before lag-1 autocorrelation",
            "bonferroni_divisor": 30,
            "description": "Global thresholds calculated on full continuous time series (1998-2017)"
        }
    }
    
    return threshold_data

def validate_threshold_schema(data: Dict[str, Any]) -> bool:
    """
    Validate the threshold data against the expected schema structure.
    
    Args:
        data: The threshold dictionary to validate
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_keys = ["neff_values", "alpha_adj", "total_tests", "period"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in threshold data: {key}")
    
    if not isinstance(data["neff_values"], dict):
        raise ValueError("neff_values must be a dictionary")
    
    if not isinstance(data["alpha_adj"], (int, float)):
        raise ValueError("alpha_adj must be a numeric value")
    
    if not isinstance(data["total_tests"], int):
        raise ValueError("total_tests must be an integer")
    
    if not isinstance(data["period"], dict):
        raise ValueError("period must be a dictionary with start/end keys")
    
    if "start" not in data["period"] or "end" not in data["period"]:
        raise ValueError("period must contain 'start' and 'end' keys")
    
    logger.info("Threshold data validated successfully against schema")
    return True

def write_global_thresholds(output_path: str = "artifacts/thresholds/global_threshold.json") -> str:
    """
    Calculate global thresholds and write them to a JSON file.
    
    Args:
        output_path: Path to write the JSON file
        
    Returns:
        The path to the written file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Calculate thresholds
    threshold_data = calculate_global_thresholds()
    
    # Validate against schema
    validate_threshold_schema(threshold_data)
    
    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(threshold_data, f, indent=2)
    
    logger.info(f"Global thresholds written to {output_path}")
    logger.info(f"  Alpha adjusted: {threshold_data['alpha_adj']:.6f} (0.05 / {threshold_data['total_tests']})")
    logger.info(f"  Period: {threshold_data['period']['start']} to {threshold_data['period']['end']}")
    
    return output_path
