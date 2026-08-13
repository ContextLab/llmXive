"""
Data Ingestion Module for the Metaphorical Framing Study.

This module handles the loading and validation of real participant data
from survey responses, as well as experimental assignment data.
"""

import json
import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

# Constants for file paths relative to project root
SURVEY_RESPONSES_PATH = "data/raw/survey_responses.json"
ASSIGNMENTS_PATH = "data/processed/experimental_assignments.csv"

# Expected schema keys for real participant data
REQUIRED_KEYS = {"participant_id", "condition", "raw_responses"}


class DataIngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass


def load_real_participant_data(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load real participant data from the survey responses JSON file.

    This function implements the logic for FR-002 and US-1 to handle
    actual survey data. It strictly validates the schema and fails loudly
    if the data is missing or malformed.

    Args:
        file_path: Optional path to the survey responses file. Defaults to
                   data/raw/survey_responses.json.

    Returns:
        A list of dictionaries, where each dictionary represents a participant's
        response data with keys: participant_id, condition, raw_responses.

    Raises:
        DataIngestionError: If the file does not exist, is empty, or does not
                            conform to the required schema.
    """
    target_path = file_path or SURVEY_RESPONSES_PATH

    if not os.path.exists(target_path):
        raise DataIngestionError(
            f"Real participant data file not found: {target_path}. "
            "Please ensure survey responses have been collected and saved."
        )

    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataIngestionError(f"Invalid JSON format in {target_path}: {e}")

    if not isinstance(data, list):
        raise DataIngestionError(
            f"Expected a list of participant records in {target_path}, got {type(data)}."
        )

    if len(data) == 0:
        raise DataIngestionError(
            f"The survey responses file {target_path} is empty. "
            "No real participant data to process."
        )

    # Validate schema for each record
    for i, record in enumerate(data):
        if not isinstance(record, dict):
            raise DataIngestionError(
                f"Record at index {i} is not a dictionary."
            )

        missing_keys = REQUIRED_KEYS - set(record.keys())
        if missing_keys:
            raise DataIngestionError(
                f"Record at index {i} is missing required keys: {missing_keys}. "
                f"Expected schema: {REQUIRED_KEYS}"
            )

        # Optional: Validate types
        if not isinstance(record["participant_id"], (str, int)):
            raise DataIngestionError(
                f"Record at index {i}: 'participant_id' must be a string or int."
            )
        
        if not isinstance(record["condition"], str):
            raise DataIngestionError(
                f"Record at index {i}: 'condition' must be a string."
            )

        if not isinstance(record["raw_responses"], dict):
            raise DataIngestionError(
                f"Record at index {i}: 'raw_responses' must be a dictionary."
            )

    return data


def load_assignments(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load experimental assignments from the CSV file.

    Args:
        file_path: Optional path to the assignments CSV. Defaults to
                   data/processed/experimental_assignments.csv.

    Returns:
        A list of assignment dictionaries.

    Raises:
        DataIngestionError: If file is missing or malformed.
    """
    target_path = file_path or ASSIGNMENTS_PATH

    if not os.path.exists(target_path):
        raise DataIngestionError(
            f"Assignment file not found: {target_path}. "
            "Run T013 (experiment_runner) first to generate assignments."
        )

    assignments = []
    try:
        with open(target_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assignments.append(row)
    except Exception as e:
        raise DataIngestionError(f"Failed to read assignments from {target_path}: {e}")

    if not assignments:
        raise DataIngestionError(f"Assignment file {target_path} contains no data rows.")

    return assignments


def main():
    """
    CLI entry point to test loading real participant data.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Load and validate real participant data.")
    parser.add_argument(
        "--file",
        type=str,
        default=SURVEY_RESPONSES_PATH,
        help=f"Path to survey_responses.json (default: {SURVEY_RESPONSES_PATH})"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed validation info"
    )

    args = parser.parse_args()

    try:
        print(f"Loading real participant data from: {args.file}")
        data = load_real_participant_data(args.file)
        
        print(f"✓ Successfully loaded {len(data)} participant records.")
        
        if args.verbose and data:
            print("\nSample record structure:")
            sample = data[0]
            for key, value in sample.items():
                if key == "raw_responses" and isinstance(value, dict):
                    print(f"  {key}: dict with keys {list(value.keys())}")
                else:
                    print(f"  {key}: {value}")

    except DataIngestionError as e:
        print(f"✗ Data Ingestion Error: {e}")
        exit(1)
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()