"""
Data loading module for the Implicit Bias experiment.
Handles loading of raw response logs and synthetic data generation for CI.
"""

import argparse
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging
import numpy as np

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)


def load_response_logs(
    data_root: Optional[Path] = None,
    null_effect: bool = False
) -> pd.DataFrame:
    """
    Load raw response logs from the data directory.

    Args:
        data_root: Root directory for data. Defaults to project root.
        null_effect: If True, generate synthetic data for CI/testing.
                     If False, requires real data files to exist.

    Returns:
        DataFrame containing response logs.

    Raises:
        RuntimeError: If real data is missing and null_effect is False.
    """
    if data_root is None:
        data_root = get_project_root()

    responses_dir = data_root / "data" / "raw" / "responses"
    logger.info(f"Looking for response logs in: {responses_dir}")

    if null_effect:
        logger.info("Generating synthetic response logs for CI (null-effect mode).")
        return generate_synthetic_response_logs(n_participants=100, seed=42)

    # Check for real data files
    if not responses_dir.exists():
        raise RuntimeError(
            f"Real data directory not found: {responses_dir}. "
            "Set --null-effect flag for synthetic data or provide real data."
        )

    # Find CSV files
    csv_files = list(responses_dir.glob("*.csv"))
    if not csv_files:
        raise RuntimeError(
            f"No CSV files found in {responses_dir}. "
            "Set --null-effect flag for synthetic data or provide real data."
        )

    logger.info(f"Found {len(csv_files)} response log files.")
    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            logger.debug(f"Loaded {file.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to load {file.name}: {e}")
            raise

    if not dfs:
        raise RuntimeError(
            "Could not load any valid response log files."
        )

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined response logs: {len(combined_df)} total rows")
    return combined_df


def generate_synthetic_response_logs(
    n_participants: int = 100,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic response logs for CI/testing.

    Args:
        n_participants: Number of synthetic participants.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with synthetic response logs.
    """
    np.random.seed(seed)
    logger.info(f"Generating synthetic data for {n_participants} participants.")

    # Define parameters
    n_trials_per_session = 40
    sessions = ["session_A", "session_B"]
    conditions = ["compatible", "incompatible"]

    data = []
    for p_id in range(n_participants):
        participant_id = f"P{p_id:04d}"
        for session in sessions:
            for condition in conditions:
                # Generate reaction times (normal distribution)
                mean_rt = np.random.uniform(600, 900)
                std_rt = np.random.uniform(100, 200)
                n_trials = np.random.randint(35, 45)

                rts = np.random.normal(mean_rt, std_rt, n_trials)
                # Ensure positive and within bounds
                rts = np.clip(rts, 300, 10000)

                # Generate accuracy (mostly correct)
                errors = np.random.binomial(1, 0.05, n_trials)
                is_correct = 1 - errors

                for i, (rt, correct) in enumerate(zip(rts, is_correct)):
                    data.append({
                        "participant_id": participant_id,
                        "session_id": session,
                        "condition": condition,
                        "trial_number": i + 1,
                        "reaction_time": rt,
                        "is_correct": correct,
                        "stimulus_category": np.random.choice(["A", "B"]),
                        "response_category": np.random.choice(["A", "B"]),
                        "timestamp": pd.Timestamp.now()
                    })

    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} synthetic response rows.")
    return df


def main():
    """
    Main entry point for loading response logs.
    """
    parser = argparse.ArgumentParser(
        description="Load response logs for analysis."
    )
    parser.add_argument(
        "--null-effect",
        action="store_true",
        help="Generate synthetic data for CI/testing."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for loaded data (optional)."
    )

    args = parser.parse_args()
    setup_logging()

    try:
        df = load_response_logs(null_effect=args.null_effect)
        logger.info(f"Successfully loaded {len(df)} rows.")

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"Saved data to {output_path}")
        else:
            print(df.head())

    except RuntimeError as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
