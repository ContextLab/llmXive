import os
import sys
import argparse
from pathlib import Path
import pandas as pd
from utils.logger import get_logger
from analysis.stat_utils import log_normality_test

logger = get_logger(__name__)

def main():
    """
    Orchestrates the normality audit step.
    Loads cleaned data, runs Shapiro-Wilk, and writes the log.
    """
    parser = argparse.ArgumentParser(description="Run Normality Audit")
    parser.add_argument("--input", type=str, required=True, help="Path to cleaned_sessions.csv")
    parser.add_argument("--output", type=str, default="data/processed/normality_log.txt", help="Path to output log")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logger.info(f"Loading cleaned data from {args.input}")
    try:
        data = pd.read_csv(args.input)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Executing Shapiro-Wilk normality test on difference scores.")
    try:
        results = log_normality_test(data, str(output_path))
        logger.info("Normality audit completed successfully.")
    except Exception as e:
        logger.error(f"Normality audit failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
