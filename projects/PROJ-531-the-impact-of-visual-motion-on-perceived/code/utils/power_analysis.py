"""
T016: Implement power analysis and sample size check.
Reads cleaned data, calculates N, and writes modeling_config.json.
"""
import json
import pandas as pd
from pathlib import Path
import logging
from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_power_analysis(data_path: str = "data/processed/raw_cleaned.csv"):
    """
    Calculate N and determine max_depth/abort_flag.
    Outputs: data/processed/modeling_config.json
    """
    if not Path(data_path).exists():
        logger.error(f"Cleaned data not found at {data_path}")
        return None
    
    df = pd.read_csv(data_path)
    n_samples = len(df)
    
    abort_flag = False
    max_depth = None # None implies default/unconstrained
    
    if n_samples < 80:
        abort_flag = True
        max_depth = None # Will abort anyway
    elif 80 <= n_samples < 100:
        max_depth = 3 # Per FR-014
        abort_flag = False
    else:
        max_depth = None # Default
        abort_flag = False
    
    config = {
        "n_samples": n_samples,
        "max_depth": max_depth,
        "abort_flag": abort_flag,
        "threshold_80": 80,
        "threshold_100": 100
    }
    
    output_path = Path("data/processed/modeling_config.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Wrote modeling_config.json to {output_path}. N={n_samples}, abort={abort_flag}")
    return config

def main():
    config = calculate_power_analysis()
    if config and config.get("abort_flag"):
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
