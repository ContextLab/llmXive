import argparse
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)


def load_response_logs(
    logs_path: Optional[Path] = None,
    null_effect: bool = False
) -> pd.DataFrame:
    """
    Load raw response logs from CSV.

    Args:
        logs_path: Path to response logs CSV
        null_effect: If True, generate synthetic data for CI testing

    Returns:
        DataFrame with response logs

    Raises:
        RuntimeError: If real data is missing and null_effect is False
    """
    if logs_path is None:
        root = get_project_root()
        logs_path = root / "data" / "raw" / "responses" / "response_logs.csv"

    if null_effect:
        logger.info("Generating synthetic response logs for CI testing (null-effect mode)")
        return generate_synthetic_response_logs()

    if not logs_path.exists():
        error_msg = f"Real response logs not found: {logs_path}. " \
                    "Set --null-effect flag for CI testing or provide real data."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Loading response logs from {logs_path}")
    df = pd.read_csv(logs_path)

    # Validate required columns
    required_cols = ['participant_id', 'session_id', 'reaction_time', 'is_correct', 'timestamp']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return df


def generate_synthetic_response_logs(
    n_participants: int = 50,
    n_trials_per_session: int = 40
) -> pd.DataFrame:
    """
    Generate synthetic response logs for CI testing.
    """
    import numpy as np

    np.random.seed(42)

    records = []

    for i in range(n_participants):
        pid = f"participant_{i:03d}"

        # Generate two sessions: Low and High complexity
        for session_idx, condition in enumerate(['Low', 'High']):
            session_id = f"session_{session_idx}_{condition}"

            for trial in range(n_trials_per_session):
                # Simulate reaction times (normal distribution)
                rt = np.random.normal(600, 100)
                rt = np.clip(rt, 300, 10000)

                # Simulate correctness (90% accuracy)
                is_correct = np.random.random() > 0.1

                records.append({
                    'participant_id': pid,
                    'session_id': session_id,
                    'reaction_time': rt,
                    'is_correct': is_correct,
                    'is_error': not is_correct,
                    'timestamp': f"2024-01-01T12:{trial:02d}:00"
                })

    df = pd.DataFrame(records)
    logger.info(f"Generated {len(df)} synthetic trials for {n_participants} participants")

    return df


def main() -> None:
    """Main entry point for data loading."""
    parser = argparse.ArgumentParser(description="Load response logs")
    parser.add_argument(
        '--null-effect',
        action='store_true',
        help='Generate synthetic data for CI testing'
    )
    parser.add_argument(
        '--input-path',
        type=str,
        default=None,
        help='Path to input CSV file'
    )

    args = parser.parse_args()

    input_path = Path(args.input_path) if args.input_path else None

    try:
        df = load_response_logs(input_path, null_effect=args.null_effect)
        logger.info(f"Loaded {len(df)} records")
        print(df.head())

    except RuntimeError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
