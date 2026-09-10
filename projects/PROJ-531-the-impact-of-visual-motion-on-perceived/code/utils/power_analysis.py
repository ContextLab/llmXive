import json
import pandas as pd
from pathlib import Path
import logging
from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_power_analysis(
    input_path: str,
    output_path: str,
    min_sample_threshold: int = 80,
    ideal_sample_threshold: int = 100
) -> dict:
    """
    Reads cleaned data, calculates sample size N, and determines modeling config.
    
    Logic:
    - If N < 80: abort_flag = True
    - If 80 <= N < 100: max_depth = 3
    - If N >= 100: max_depth = None (or default)
    
    Args:
        input_path: Path to data/processed/cleaned_data.csv
        output_path: Path to write data/processed/modeling_config.json
        min_sample_threshold: Minimum N to proceed (default 80)
        ideal_sample_threshold: N where we stop constraining max_depth (default 100)
        
    Returns:
        dict: The generated config dictionary
    """
    logger.info(f"Starting power analysis for sample size check. Input: {input_path}")
    
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Cleaned data file not found at {input_path}")
    
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise
    
    n_samples = len(df)
    logger.info(f"Calculated sample size N: {n_samples}")
    
    abort_flag = False
    max_depth = None
    
    if n_samples < min_sample_threshold:
        abort_flag = True
        max_depth = None
        logger.warning(f"Sample size {n_samples} is below threshold {min_sample_threshold}. Abort flag set to True.")
    elif n_samples < ideal_sample_threshold:
        max_depth = 3
        logger.info(f"Sample size {n_samples} is between {min_sample_threshold} and {ideal_sample_threshold}. Setting max_depth=3.")
    else:
        logger.info(f"Sample size {n_samples} meets ideal threshold. No max_depth constraint.")
    
    config = {
        "n_samples": n_samples,
        "max_depth": max_depth,
        "abort_flag": abort_flag,
        "min_sample_threshold": min_sample_threshold,
        "ideal_sample_threshold": ideal_sample_threshold
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Modeling config written to {output_path}")
    return config

def main():
    """Entry point for running power analysis as a script."""
    input_path = "data/processed/cleaned_data.csv"
    output_path = "data/processed/modeling_config.json"
    
    try:
        config = calculate_power_analysis(input_path, output_path)
        print(f"Power analysis complete. Config: {config}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error during power analysis: {e}")
        exit(1)

if __name__ == "__main__":
    main()