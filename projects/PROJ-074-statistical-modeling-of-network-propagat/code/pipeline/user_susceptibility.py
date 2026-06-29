"""
User susceptibility score computation for misinformation cascade modeling.

Implements the proxy susceptibility score formula per FR-003 Clarification:
(historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0

Input: CSV file with columns including historical_degree, historical_shares
Output: CSV file with added susceptibility_score column
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from pipeline.utils import set_global_seed, setup_logger

# Configure module logger
logger = setup_logger("user_susceptibility")


def compute_susceptibility_score(row: pd.Series) -> float:
    """
    Compute proxy susceptibility score using historical network context.

    Formula (per FR-003 Clarification):
    (historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0

    Args:
        row: DataFrame row containing historical_degree and historical_shares

    Returns:
        1.0 if user meets both thresholds, 0.0 otherwise
    """
    historical_degree = row.get("historical_degree", 0)
    historical_shares = row.get("historical_shares", 0)

    if historical_degree >= 2 and historical_shares >= 1:
        return 1.0
    return 0.0


def compute_susceptibility_scores(
    input_path: str,
    output_path: str,
    seed: int = 12345,
) -> Path:
    """
    Load cascade/feature data, compute susceptibility scores, and write output.

    Args:
        input_path: Path to input CSV with historical_degree and historical_shares
        output_path: Path to write output CSV with susceptibility_score column
        seed: Random seed for reproducibility

    Returns:
        Path to the output file
    """
    set_global_seed(seed)
    logger.info(f"Loading input data from {input_path}")

    # Load input data
    df = pd.read_csv(input_path)

    # Validate required columns exist
    required_cols = ["historical_degree", "historical_shares"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Input data shape: {df.shape}")
    logger.info(f"Computing susceptibility scores for {len(df)} records")

    # Compute susceptibility score for each row
    df["susceptibility_score"] = df.apply(compute_susceptibility_score, axis=1)

    # Log summary statistics
    score_counts = df["susceptibility_score"].value_counts()
    logger.info(f"Susceptibility score distribution: {score_counts.to_dict()}")
    logger.info(
        f"Susceptibility rate: {df['susceptibility_score'].mean():.4f}"
    )

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Output written to {output_path}")

    return output_file


def main() -> int:
    """
    Entry point for susceptibility score computation script.

    Usage:
        python code/pipeline/user_susceptibility.py \
            --input data/intermediate/features_raw.csv \
            --output results/features.csv

    Returns:
        0 on success, 1 on failure
    """
    parser = argparse.ArgumentParser(
        description="Compute user susceptibility scores from historical network context"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input CSV with historical_degree and historical_shares columns",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output CSV with susceptibility_score column added",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Random seed for reproducibility (default: 12345)",
    )

    args = parser.parse_args()

    try:
        compute_susceptibility_scores(
            input_path=args.input,
            output_path=args.output,
            seed=args.seed,
        )
        logger.info("Susceptibility score computation completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Susceptibility score computation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
