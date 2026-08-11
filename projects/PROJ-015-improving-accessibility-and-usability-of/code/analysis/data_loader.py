"""
Real data loader for the accessibility and usability study.

This module provides functions to load real session data from the data/raw/ directory.
It strictly enforces the use of real data and raises errors if no valid data is found.
"""

import os
import json
import glob
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def load_real_data(input_dir: str) -> pd.DataFrame:
    """
    Load real session data from the specified input directory.

    This function scans the input directory for JSON session files, validates them
    against the expected schema, and aggregates them into a single DataFrame.

    Args:
        input_dir (str): Path to the directory containing raw session JSON files.

    Returns:
        pd.DataFrame: A DataFrame containing all valid session records.

    Raises:
        FileNotFoundError: If no valid session files are found in the input directory.
        ValueError: If the input directory does not exist.
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    # Find all JSON files in the directory
    json_files = list(input_path.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(
            f"Real data not found in {input_dir}. Run simulator or recruit participants."
        )

    all_sessions = []
    valid_count = 0
    invalid_count = 0

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Basic validation: ensure required fields exist
            required_fields = ['participant_id', 'interface_type', 'status']
            if all(field in session_data for field in required_fields):
                # Check if this is simulated data (which should be excluded for real analysis)
                metadata = session_data.get('metadata', {})
                if metadata.get('source') == 'simulated':
                    logger.info(f"Skipping simulated session: {json_file.name}")
                    continue

                all_sessions.append(session_data)
                valid_count += 1
            else:
                logger.warning(f"Invalid session structure in {json_file.name}, skipping.")
                invalid_count += 1

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {json_file.name}: {e}")
            invalid_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {json_file.name}: {e}")
            invalid_count += 1

    if not all_sessions:
        raise FileNotFoundError(
            f"Real data not found in {input_dir}. Run simulator or recruit participants."
        )

    logger.info(f"Loaded {valid_count} valid real sessions from {input_dir}")
    if invalid_count > 0:
        logger.warning(f"Skipped {invalid_count} invalid or simulated sessions")

    # Convert list of dicts to DataFrame
    df = pd.DataFrame(all_sessions)

    # Ensure consistent column ordering if expected columns exist
    expected_cols = [
        'participant_id', 'interface_type', 'status', 'completion_time',
        'error_count', 'sus_score', 'explanation_engagement_time_seconds',
        'disability_type', 'accommodations_used', 'dropout_reason', 'timestamp'
    ]

    # Reorder columns to match expected schema if they exist
    existing_cols = [col for col in expected_cols if col in df.columns]
    if existing_cols:
        df = df[existing_cols]

    return df


def load_real_data_with_fallback(input_dir: str, fallback_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load real data with optional fallback to a different directory.

    This is a convenience wrapper that attempts to load from the primary directory,
    and if that fails, tries a fallback directory. It still raises an error if
    no real data is found in either location.

    Args:
        input_dir (str): Primary input directory.
        fallback_dir (Optional[str]): Fallback directory if primary is empty.

    Returns:
        pd.DataFrame: A DataFrame containing all valid session records.

    Raises:
        FileNotFoundError: If no valid session files are found in any directory.
    """
    try:
        return load_real_data(input_dir)
    except FileNotFoundError as e:
        if fallback_dir:
            logger.info(f"Primary directory empty, trying fallback: {fallback_dir}")
            try:
                return load_real_data(fallback_dir)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Real data not found in {input_dir} or {fallback_dir}. "
                    f"Run simulator or recruit participants."
                )
        else:
            raise


def main():
    """CLI entry point for data loading."""
    import argparse

    parser = argparse.ArgumentParser(description="Load real session data")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/raw",
        help="Directory containing raw session JSON files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/raw_sessions.csv",
        help="Output CSV file path"
    )

    args = parser.parse_args()

    logger.info(f"Attempting to load real data from {args.input_dir}")

    try:
        df = load_real_data(args.input_dir)
        df.to_csv(args.output, index=False)
        logger.info(f"Successfully loaded {len(df)} sessions and saved to {args.output}")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise


if __name__ == "__main__":
    main()