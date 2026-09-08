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

def load_cleaned_data(logger: logging.Logger) -> pd.DataFrame:
    """
    Load the cleaned dataset from data/processed/cleaned_data.parquet.
    Raises FileNotFoundError if the file does not exist.
    """
    input_path = Path("data/processed/cleaned_data.parquet")
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")

    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} samples")
    return df

def select_model_type(n_samples: int, logger: logging.Logger) -> dict:
    """
    Select the model type based on sample count N.
    
    Rules:
    - N < 30: model_type = "fail"
    - 30 <= N < 300: model_type = "ridge" (low_power)
    - N >= 300: model_type = "rf" (random_forest)
    
    Returns a dict with selection details.
    """
    if n_samples < 30:
        model_type = "fail"
        reason = "Critical Power Limitation: N < 30"
        status = "unsupported"
    elif n_samples < 300:
        model_type = "ridge"
        reason = "Low power regime: 30 <= N < 300"
        status = "selected"
    else:
        model_type = "rf"
        reason = "Sufficient power: N >= 300"
        status = "selected"

    result = {
        "model_type": model_type,
        "n_samples": n_samples,
        "threshold_low": 30,
        "threshold_high": 300,
        "reason": reason,
        "status": status,
    }
    logger.info(f"Model selection: {model_type} ({reason})")
    return result

def save_selection(selection: dict, logger: logging.Logger) -> None:
    """
    Write the model selection result to data/processed/model_selection.json.
    """
    output_path = Path("data/processed/model_selection.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(selection, f, indent=2)

    logger.info(f"Saved model selection to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Model selection based on sample count."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to the cleaned dataset parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/model_selection.json",
        help="Path to the output model selection JSON file.",
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()

    try:
        df = load_cleaned_data(logger)
        n_samples = len(df)
        selection = select_model_type(n_samples, logger)
        save_selection(selection, logger)
        logger.info("Model selection completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during model selection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()