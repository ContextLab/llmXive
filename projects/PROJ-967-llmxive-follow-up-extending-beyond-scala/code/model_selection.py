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
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def load_cleaned_data(logger, path: str) -> pd.DataFrame:
    """Load the cleaned dataset produced by T024."""
    logger.info(f"Loading cleaned data from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned data file not found: {path}")
    
    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded {len(df)} rows from {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load cleaned data: {e}")
        raise

def select_model_type(df: pd.DataFrame, logger: logging.Logger) -> str:
    """
    Determine the model type based on the sample count N.
    
    Rules:
    - If N < 30: model_type = "fail"
    - If 30 <= N < 300: model_type = "ridge"
    - If N >= 300: model_type = "rf"
    """
    n = len(df)
    logger.info(f"Dataset sample count (N): {n}")
    
    if n < 30:
        model_type = "fail"
        reason = "Critical Power Limitation: N < 30"
        logger.warning(f"Model selection failed: {reason}")
    elif n < 300:
        model_type = "ridge"
        logger.info(f"Selected Ridge Regression (30 <= N < 300)")
    else:
        model_type = "rf"
        logger.info(f"Selected Random Forest (N >= 300)")
        
    return model_type

def save_selection(logger, model_type: str, reason: str | None, output_path: str):
    """Save the model selection result to a JSON file."""
    result = {
        "status": "success" if model_type != "fail" else "fail",
        "model_type": model_type,
    }
    if reason:
        result["reason"] = reason
        
    logger.info(f"Saving model selection to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Model selection saved: {model_type}")

def parse_args():
    parser = argparse.ArgumentParser(description="Model Selection Task (T027d)")
    parser.add_argument(
        "--input-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/cleaned_data.parquet",
        help="Path to the cleaned data parquet file",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/model_selection.json",
        help="Path to save the model selection JSON",
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()
    
    try:
        # Load the cleaned dataset
        df = load_cleaned_data(logger, args.input_path)
        
        # Select model type based on N
        model_type = select_model_type(df, logger)
        
        # Determine reason if failed
        reason = None
        if model_type == "fail":
            reason = "Critical Power Limitation: N < 30"
        
        # Save the selection
        save_selection(logger, model_type, reason, args.output_path)
        
        logger.info("Model selection task completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during model selection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
