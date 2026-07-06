"""
Data Collection Module for Narrative Framing Study (US2)

This module ingests raw survey data (simulated for local testing or imported from
real survey platforms), validates responses against the data model, maps them to
Participant entities, flags manipulation check failures, and exports a cleaned
dataset ready for statistical analysis.

Responsibilities:
- Ingest raw CSV/JSON survey exports
- Validate Likert scales (integers 1-7)
- Flag manipulation check failures based on framing recognition
- Exclude partial/incomplete responses
- Export cleaned data to data/processed/cleaned_responses.csv
"""

import argparse
import csv
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Project imports
from utils.logger import setup_logger, log_script_start, log_script_end, log_data_operation, error, warning, info
from utils.data_validation import (
    validate_liker_scale,
    validate_participant_id,
    validate_condition,
    validate_survey_response_row,
    ValidationResult,
    ValidationError
)

# Constants
LIKERT_MIN = 1
LIKERT_MAX = 7
MANIPULATION_CHECK_CORRECT = "Partner"  # Expected correct answer for "Partner" frame
MANIPULATION_CHECK_TOOL = "Tool"        # Expected correct answer for "Tool" frame
# Note: The actual correct answer depends on the condition the participant was assigned to.
# We assume the raw data contains the condition they saw.

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = DATA_PROCESSED_DIR / "cleaned_responses.csv"

# Column definitions
ATTITUDE_ITEMS = [f"attitude_item_{i}" for i in range(1, 8)]
USEFULNESS_ITEMS = [f"usefulness_item_{i}" for i in range(1, 4)]
TRUST_ITEMS = [f"trust_item_{i}" for i in range(1, 5)]
ALL_ITEM_COLUMNS = ATTITUDE_ITEMS + USEFULNESS_ITEMS + TRUST_ITEMS
REQUIRED_COLUMNS = ["participant_id", "condition", "manipulation_check_response"] + ALL_ITEM_COLUMNS
OUTPUT_COLUMNS = ["participant_id", "condition", "manipulation_check", "manipulation_check_failed"] + ALL_ITEM_COLUMNS


@dataclass
class Participant:
    """Entity representing a single participant's cleaned response."""
    participant_id: str
    condition: str  # 'Partner' or 'Tool'
    manipulation_check: str  # Their answer to the manipulation check question
    manipulation_check_failed: bool
    attitude_item_1: int
    attitude_item_2: int
    attitude_item_3: int
    attitude_item_4: int
    attitude_item_5: int
    attitude_item_6: int
    attitude_item_7: int
    usefulness_item_1: int
    usefulness_item_2: int
    usefulness_item_3: int
    trust_item_1: int
    trust_item_2: int
    trust_item_3: int
    trust_item_4: int


def setup_directories():
    """Ensure output directories exist."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_raw_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw survey data from a CSV or JSON file.
    Supports standard survey export formats.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    data = []
    suffix = file_path.suffix.lower()

    try:
        if suffix == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        elif suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_json = json.load(f)
                if isinstance(raw_json, list):
                    data = raw_json
                elif isinstance(raw_json, dict) and 'responses' in raw_json:
                    data = raw_json['responses']
                else:
                    # Try to treat the dict as a single record
                    data = [raw_json]
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        log_data_operation("load", file_path, len(data))
        return data

    except Exception as e:
        error(f"Failed to load raw data from {file_path}: {e}")
        raise


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize row keys to match expected column names.
    Handles common variations in survey export headers.
    """
    normalized = {}
    key_map = {
        'participant_id': ['participant_id', 'ParticipantID', 'P_ID', 'id'],
        'condition': ['condition', 'Condition', 'frame', 'Frame'],
        'manipulation_check_response': ['manipulation_check', 'ManipulationCheck', 'DidYouRead', 'FramingCheck'],
    }

    for target_key, possible_names in key_map.items():
        found = False
        for name in possible_names:
            if name in row:
                normalized[target_key] = row[name]
                found = True
                break
        if not found:
            # Default to snake_case version if not found
            normalized[target_key] = row.get(target_key, "")

    # Map item responses
    for i in range(1, 8):
        variants = [f"attitude_item_{i}", f"attitude_{i}", f"Q_attitude_{i}"]
        for v in variants:
            if v in row:
                normalized[f"attitude_item_{i}"] = row[v]
                break
        else:
            normalized[f"attitude_item_{i}"] = ""

    for i in range(1, 4):
        variants = [f"usefulness_item_{i}", f"usefulness_{i}", f"Q_usefulness_{i}"]
        for v in variants:
            if v in row:
                normalized[f"usefulness_item_{i}"] = row[v]
                break
        else:
            normalized[f"usefulness_item_{i}"] = ""

    for i in range(1, 5):
        variants = [f"trust_item_{i}", f"trust_{i}", f"Q_trust_{i}"]
        for v in variants:
            if v in row:
                normalized[f"trust_item_{i}"] = row[v]
                break
        else:
            normalized[f"trust_item_{i}"] = ""

    return normalized


def is_partial_response(row: Dict[str, Any]) -> bool:
    """
    Check if a response is partial (abandoned halfway).
    Heuristic: If any of the main scale items are missing or empty, consider it partial.
    """
    # Check if at least 50% of attitude items are present
    attitude_count = sum(1 for i in range(1, 8) if row.get(f"attitude_item_{i}", "").strip())
    if attitude_count < 4:
        return True

    # Check if condition is missing
    if not row.get("condition", "").strip():
        return True

    return False


def validate_and_process_row(row: Dict[str, Any]) -> Optional[Participant]:
    """
    Validate a single row and convert it to a Participant entity.
    Returns None if the row is invalid or partial.
    """
    # Check for partial response
    if is_partial_response(row):
        info(f"Skipping partial response: {row.get('participant_id', 'unknown')}")
        return None

    # Validate participant ID
    pid = row.get("participant_id", "").strip()
    if not validate_participant_id(pid):
        warning(f"Invalid participant ID format: {pid}")
        return None

    # Validate condition
    condition = row.get("condition", "").strip()
    if not validate_condition(condition):
        warning(f"Invalid condition: {condition} for participant {pid}")
        return None

    # Validate manipulation check
    mc_response = row.get("manipulation_check_response", "").strip()
    if not mc_response:
        # If missing, mark as failed
        mc_failed = True
    else:
        # Determine if correct based on condition
        # If condition is 'Partner', correct answer is 'Partner'
        # If condition is 'Tool', correct answer is 'Tool'
        if condition == "Partner":
            mc_failed = (mc_response.lower() != "partner")
        elif condition == "Tool":
            mc_failed = (mc_response.lower() != "tool")
        else:
            mc_failed = True  # Unknown condition, fail

    # Validate Likert scales
    validated_items = {}
    all_valid = True

    for item in ALL_ITEM_COLUMNS:
        val_str = row.get(item, "").strip()
        if not val_str:
            warning(f"Missing value for {item} in participant {pid}")
            all_valid = False
            break

        try:
            val_int = int(float(val_str))
            if not validate_liker_scale(val_int):
                warning(f"Likert scale out of range ({val_int}) for {item} in participant {pid}")
                all_valid = False
                break
            validated_items[item] = val_int
        except (ValueError, TypeError):
            warning(f"Non-integer value for {item} ({val_str}) in participant {pid}")
            all_valid = False
            break

    if not all_valid:
        return None

    # Construct Participant entity
    return Participant(
        participant_id=pid,
        condition=condition,
        manipulation_check=mc_response,
        manipulation_check_failed=mc_failed,
        **validated_items
    )


def ingest_and_clean(input_file: Path) -> List[Participant]:
    """
    Main pipeline to ingest raw data and produce cleaned Participant entities.
    """
    raw_data = load_raw_data(input_file)
    cleaned_participants = []
    skipped_count = 0

    for i, raw_row in enumerate(raw_data):
        normalized_row = normalize_row(raw_row)
        participant = validate_and_process_row(normalized_row)

        if participant:
            cleaned_participants.append(participant)
        else:
            skipped_count += 1

    log_data_operation("clean", input_file, len(cleaned_participants), skipped=skipped_count)
    info(f"Successfully processed {len(cleaned_participants)} participants, skipped {skipped_count}")

    return cleaned_participants


def export_cleaned_data(participants: List[Participant], output_path: Path):
    """
    Export cleaned participants to CSV.
    """
    if not participants:
        warning("No participants to export.")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for p in participants:
            writer.writerow(asdict(p))

    log_data_operation("export", output_path, len(participants))
    info(f"Exported {len(participants)} cleaned responses to {output_path}")


def run_data_collection(input_file: Optional[Path] = None):
    """
    Entry point for the data collection pipeline.
    """
    setup_logger()
    log_script_start("04_data_collection")

    try:
        setup_directories()

        if input_file is None:
            # Default to a simulated input if none provided for local testing
            # In production, this would be a real file path
            default_input = DATA_RAW_DIR / "survey_export.csv"
            if default_input.exists():
                input_file = default_input
            else:
                # If no real file exists, we cannot proceed with real data
                # The task requires real data. If the file doesn't exist, we fail loudly.
                # However, for the purpose of this implementation, we will create a
                # minimal simulated dataset ONLY IF the task description implies
                # "simulated or imported". The prompt says "simulated or imported".
                # But constraint 9 says "NEVER fabricate values".
                # The task says: "ingest raw survey data (simulated or imported)".
                # This is a conflict. Constraint 9 is higher priority: "Real data only".
                # If no real file exists, we should fail.
                # But to make the script runnable for verification in an empty environment,
                # we will check if a specific "real" file exists. If not, we raise an error.
                # However, the prompt for T019 says "simulated or imported".
                # Let's assume for the sake of the pipeline that if no file is provided,
                # we look for the pilot study output or a generated raw file.
                # Since T024/T025 ran, maybe they generated raw data?
                # Let's assume the user provides the file via argument.
                # If not provided and no default exists, we raise FileNotFoundError.
                raise FileNotFoundError(
                    "No input file provided and no default raw data found. "
                    "Please provide a path to raw survey data via --input or place "
                    "data at data/raw/survey_export.csv."
                )

        cleaned_participants = ingest_and_clean(input_file)
        export_cleaned_data(cleaned_participants, OUTPUT_FILE)

        log_script_end("04_data_collection", success=True)

    except Exception as e:
        error(f"Data collection pipeline failed: {e}")
        log_script_end("04_data_collection", success=False, error=str(e))
        raise


def main():
    parser = argparse.ArgumentParser(description="Ingest and clean raw survey data.")
    parser.add_argument(
        "--input",
        type=Path,
        required=False,
        help="Path to raw survey data file (CSV or JSON). Defaults to data/raw/survey_export.csv."
    )
    args = parser.parse_args()

    run_data_collection(args.input)


if __name__ == "__main__":
    main()
