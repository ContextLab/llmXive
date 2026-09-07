"""
Power analysis and sample size check module.

Reads the cleaned dataset from T017, calculates N, and determines
modeling configuration parameters based on sample size thresholds.
"""
import json
import pandas as pd
from pathlib import Path
import logging
from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

def calculate_power_analysis(
    input_path: str = "data/processed/cleaned_data.csv",
    output_path: str = "data/processed/modeling_config.json",
    min_samples_abort: int = 80,
    min_samples_reduced_depth: int = 100
) -> dict:
    """
    Calculate sample size and generate modeling configuration.

    Logic:
    - If N < 80: abort_flag = True, max_depth = None (or 0)
    - If 80 <= N < 100: abort_flag = False, max_depth = 3
    - If N >= 100: abort_flag = False, max_depth = None (default)

    Args:
        input_path: Path to the cleaned CSV file.
        output_path: Path to write the JSON config.
        min_samples_abort: Threshold below which the process should abort.
        min_samples_reduced_depth: Threshold below which max_depth is reduced.

    Returns:
        dict: The generated configuration dictionary.
    """
    logger.info(f"Loading data from {input_path} for power analysis...")
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")

    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        raise RuntimeError(f"Failed to read {input_path}: {e}")

    n_samples = len(df)
    logger.info(f"Sample size calculated: N = {n_samples}")

    # Determine configuration based on thresholds
    abort_flag = False
    max_depth = None  # Default to None (unconstrained)

    if n_samples < min_samples_abort:
        abort_flag = True
        max_depth = None
        logger.warning(f"Sample size {n_samples} is below abort threshold ({min_samples_abort}). Setting abort_flag=True.")
    elif n_samples < min_samples_reduced_depth:
        abort_flag = False
        max_depth = 3
        logger.info(f"Sample size {n_samples} is below reduced depth threshold ({min_samples_reduced_depth}). Setting max_depth=3.")
    else:
        abort_flag = False
        max_depth = None
        logger.info(f"Sample size {n_samples} meets all thresholds. No depth restriction.")

    config = {
        "n_samples": n_samples,
        "max_depth": max_depth,
        "abort_flag": abort_flag
    }

    logger.info(f"Writing modeling config to {output_path}")
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)

    return config

def main():
    """Entry point for the power analysis script."""
    try:
        config = calculate_power_analysis()
        print(f"Power analysis complete. Config: {config}")
        if config["abort_flag"]:
            print("WARNING: Abort flag is set. Subsequent tasks may need to handle this.")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()