"""
Model Selection Task (T027d)

Reads the cleaned dataset, counts samples, and selects the model type
based on dataset size thresholds. Writes the decision to a JSON file.

Execution Order: MUST run before T027a (Training Split) and T022c (Mahalanobis).
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def load_cleaned_data(logger, input_path):
    """
    Load the cleaned dataset from the specified Parquet file.
    
    Args:
        logger: Logger instance
        input_path: Path to the cleaned_data.parquet file
        
    Returns:
        pd.DataFrame: The loaded dataset
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the file cannot be read
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")
    
    logger.info(f"Loading cleaned data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def select_model_type(df, logger):
    """
    Determine the model type based on the number of samples.
    
    Rules:
    - N < 30: model_type = "synthetic" (pipeline stops)
    - 30 <= N < 300: model_type = "ridge" (Ridge Regression)
    - N >= 300: model_type = "rf" (Random Forest)
    
    Args:
        df: The cleaned dataset
        logger: Logger instance
        
    Returns:
        str: The selected model type
    """
    n = len(df)
    logger.info(f"Dataset size: N = {n}")
    
    if n < 30:
        model_type = "synthetic"
        logger.warning(f"N < 30 ({n}). Setting model_type to 'synthetic'. Pipeline will stop after reporting.")
    elif n < 300:
        model_type = "ridge"
        logger.info(f"30 <= N < 300 ({n}). Setting model_type to 'ridge'.")
    else:
        model_type = "rf"
        logger.info(f"N >= 300 ({n}). Setting model_type to 'rf'. Mahalanobis distance will be computed (T022c).")
    
    return model_type

def save_selection(model_type, n_samples, output_path, logger):
    """
    Save the model selection decision to a JSON file.
    
    Args:
        model_type: The selected model type string
        n_samples: The number of samples in the dataset
        output_path: Path to the output JSON file
        logger: Logger instance
    """
    result = {
        "model_type": model_type,
        "sample_count": n_samples,
        "thresholds": {
            "min_ridge": 30,
            "min_rf": 300
        },
        "status": "completed"
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Model selection saved to {output_path}")
    logger.info(f"Selected model: {model_type}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Model Selection Task (T027d)")
    parser.add_argument(
        "--input-path",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to the cleaned data Parquet file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/model_selection.json",
        help="Path to save the model selection JSON"
    )
    return parser.parse_args()

def main():
    """Main entry point for the model selection task."""
    logger = setup_logging()
    args = parse_args()
    
    try:
        # Load cleaned data
        df = load_cleaned_data(logger, args.input_path)
        
        # Select model type
        model_type = select_model_type(df, logger)
        
        # Save result
        save_selection(model_type, len(df), args.output_path, logger)
        
        logger.info("Model selection task completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during model selection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()