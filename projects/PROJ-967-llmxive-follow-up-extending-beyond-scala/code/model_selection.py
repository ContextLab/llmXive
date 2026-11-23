import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

def setup_logging():
    """Configure basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

def load_cleaned_data(input_path: str) -> pd.DataFrame:
    """Load the cleaned dataset from parquet."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {input_path}")
    return pd.read_parquet(path)

def select_model_type(sample_count: int) -> tuple[str, str]:
    """
    Determine model type based on sample count N.

    Rules:
    - N < 30: model_type = "fail", reason = "Critical Power Limitation: N < 30"
    - 30 <= N < 300: model_type = "ridge", reason = "Low sample count; using Ridge Regression"
    - N >= 300: model_type = "rf", reason = "Sufficient sample count; using Random Forest"
    """
    if sample_count < 30:
        return "fail", "Critical Power Limitation: N < 30"
    elif sample_count < 300:
        return "ridge", "Low sample count; using Ridge Regression"
    else:
        return "rf", "Sufficient sample count; using Random Forest"

def save_selection(
    output_path: str, model_type: str, reason: str, sample_count: int
) -> None:
    """Write the model selection decision to a JSON file."""
    result = {
        "model_type": model_type,
        "reason": reason,
        "sample_count": sample_count,
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logging.info(f"Model selection saved to {output_path}: {model_type}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Data Sufficiency Check & Model Selection (T027d)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/cleaned_data.parquet",
        help="Path to cleaned data parquet file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/model_selection.json",
        help="Path to output model selection JSON file",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging()
    logging.info("Starting Data Sufficiency Check & Model Selection (T027d)")

    try:
        df = load_cleaned_data(args.input)
        sample_count = len(df)
        logging.info(f"Loaded {sample_count} samples from {args.input}")

        model_type, reason = select_model_type(sample_count)
        logging.info(f"Selected model: {model_type} ({reason})")

        save_selection(args.output, model_type, reason, sample_count)
        logging.info("Task T027d completed successfully.")

    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during model selection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()