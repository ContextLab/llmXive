import json
import pandas as pd
from pathlib import Path
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_power_analysis(input_csv_path: str, output_config_path: str) -> dict:
    """
    Read cleaned data, calculate sample size N, and determine modeling config.
    
    Logic:
    - If N < 80: abort_flag = True
    - If 80 <= N < 100: max_depth = 3
    - If N >= 100: max_depth = None (unconstrained)
    
    Args:
        input_csv_path: Path to data/processed/cleaned_data.csv
        output_config_path: Path to write data/processed/modeling_config.json
        
    Returns:
        dict containing n_samples, max_depth, abort_flag
    """
    logger.info(f"Reading cleaned data from {input_csv_path}")
    df = pd.read_csv(input_csv_path)
    n_samples = len(df)
    logger.info(f"Calculated sample size N = {n_samples}")
    
    abort_flag = False
    max_depth = None  # None implies no constraint for RF/Tree models
    
    if n_samples < 80:
        abort_flag = True
        logger.warning(f"Sample size N={n_samples} is below minimum threshold (80). abort_flag set to True.")
    elif n_samples < 100:
        max_depth = 3
        logger.info(f"Sample size N={n_samples} is in range [80, 100). Setting max_depth=3 for tree models.")
    else:
        logger.info(f"Sample size N={n_samples} is sufficient (>=100). No max_depth constraint.")
    
    config = {
        "n_samples": n_samples,
        "max_depth": max_depth,
        "abort_flag": abort_flag
    }
    
    output_path = Path(output_config_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Wrote modeling config to {output_config_path}")
    return config

def main():
    """Entry point for power analysis task."""
    # Paths relative to project root
    input_csv = "data/processed/cleaned_data.csv"
    output_json = "data/processed/modeling_config.json"
    
    if not Path(input_csv).exists():
        logger.error(f"Input file {input_csv} not found. Cannot perform power analysis.")
        raise FileNotFoundError(f"Input file {input_csv} not found.")
    
    config = calculate_power_analysis(input_csv, output_json)
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()