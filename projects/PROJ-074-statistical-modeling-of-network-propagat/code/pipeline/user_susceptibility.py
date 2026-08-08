"""
User Susceptibility Feature Engineering Module.

This module computes user susceptibility scores based on historical sharing behavior.
The formula used is: (historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0

Input Sources:
  - Feature data CSV (specified in --input) containing user_id, historical_degree, historical_shares

Transformation Steps:
  1. Load feature data
  2. Apply susceptibility formula per user
  3. Aggregate scores per cascade

Output Files:
  - Susceptibility features CSV (specified in --output)
  - Logs written to pipeline.log
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from pipeline.utils import set_global_seed, setup_logger


def compute_susceptibility_score(historical_degree: int, historical_shares: int) -> float:
    """
    Compute susceptibility score for a single user based on historical behavior.

    Formula: (historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0

    Args:
        historical_degree: User's historical degree in the network.
        historical_shares: User's historical number of shares.

    Returns:
        1.0 if susceptible, 0.0 otherwise.
    """
    return 1.0 if (historical_degree >= 2 and historical_shares >= 1) else 0.0


def compute_susceptibility_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute susceptibility scores for all users in the dataframe.

    Args:
        df: DataFrame with columns 'historical_degree' and 'historical_shares'.

    Returns:
        DataFrame with an added 'susceptibility_score' column.
    """
    df['susceptibility_score'] = df.apply(
        lambda row: compute_susceptibility_score(row['historical_degree'], row['historical_shares']),
        axis=1
    )
    return df


def main():
    """Main entry point for user susceptibility computation."""
    parser = argparse.ArgumentParser(description='Compute user susceptibility scores.')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to input CSV with user features.')
    parser.add_argument('--output', type=str, required=True,
                        help='Path for output CSV with susceptibility scores.')
    parser.add_argument('--seed', type=int, default=12345,
                        help='Random seed for reproducibility.')
    parser.add_argument('--log', type=str, default='pipeline.log',
                        help='Path to log file.')

    args = parser.parse_args()

    # Setup logging and seed
    logger = setup_logger(args.log)
    set_global_seed(args.seed)
    logger.info("Starting user susceptibility computation.")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output file: {args.output}")

    try:
        # Load input data
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} rows from {args.input}")

        # Verify required columns
        required_cols = ['historical_degree', 'historical_shares']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Compute scores
        df = compute_susceptibility_scores(df)
        logger.info("Computed susceptibility scores for all users.")

        # Write output
        df.to_csv(args.output, index=False)
        logger.info(f"Wrote {len(df)} rows to {args.output}")
        logger.info("User susceptibility computation completed successfully.")

    except Exception as e:
        logger.error(f"Error during susceptibility computation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
