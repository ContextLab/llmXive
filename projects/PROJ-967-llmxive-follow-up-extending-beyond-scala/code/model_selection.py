import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def load_cleaned_data(logger, input_path):
    """Load the cleaned dataset from parquet."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")
    
    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} samples")
    return df

def select_model_type(n_samples, logger):
    """
    Select model type based on sample count.
    
    Rules:
    - N < 30: model_type = "fail"
    - 30 <= N < 300: model_type = "ridge" (low_power)
    - N >= 300: model_type = "rf" (Random Forest)
    """
    if n_samples < 30:
        return "fail", "Critical Power Limitation: N < 30"
    elif n_samples < 300:
        return "ridge", "Low Power: Using Ridge Regression"
    else:
        return "rf", "Sufficient Power: Using Random Forest"

def save_selection(selection_data, output_path, logger):
    """Save model selection results to JSON."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as f:
        json.dump(selection_data, f, indent=2)
    
    logger.info(f"Model selection saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Model selection based on sample count")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to cleaned dataset",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/model_selection.json",
        help="Path to output model selection JSON",
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()

    # Load cleaned data
    df = load_cleaned_data(logger, args.input)
    n_samples = len(df)

    # Select model type
    model_type, reason = select_model_type(n_samples, logger)

    # Prepare selection data
    selection_data = {
        "model_type": model_type,
        "n_samples": n_samples,
        "threshold": 30,
        "reason": reason,
        "status": "unsupported" if model_type == "fail" else "selected"
    }

    # If model_type is "fail", we still save the selection but mark status as unsupported
    # The pipeline will continue to generate a failure report in T027e

    # Save selection
    save_selection(selection_data, args.output, logger)

    logger.info(f"Model selection complete: {model_type} (N={n_samples})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
