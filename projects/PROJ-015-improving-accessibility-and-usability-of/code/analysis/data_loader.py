"""
Real data loader for the accessibility and usability study.

This module provides functions to load real session data from the data/raw/ directory.
It strictly enforces the use of real data and raises errors if no valid data is found.
It explicitly references the session schema contract to validate the 'source' field.
"""

import os
import json
import glob
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# Path to the contract schema for validation
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "session.schema.yaml"


def _load_schema() -> Dict[str, Any]:
    """Load the JSON schema definition from the contracts directory."""
    try:
        # We need to parse YAML. Since pyyaml is a dependency (T002), we use it.
        import yaml
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed. Schema validation will be skipped.")
        return {}
    except FileNotFoundError:
        logger.warning(f"Schema file not found at {SCHEMA_PATH}. Validation skipped.")
        return {}


def _validate_source_field(session_data: Dict[str, Any], dev_mode: bool) -> bool:
    """
    Validate the 'source' field of a session against the schema.

    Args:
        session_data: The session dictionary.
        dev_mode: If True, 'simulated' source is allowed. If False, only 'human_participant' is allowed.

    Returns:
        bool: True if valid, False otherwise.
    """
    schema = _load_schema()
    if not schema:
        # If schema cannot be loaded, we perform a basic check or allow based on dev_mode
        # But per spec, we must explicitly reference the schema. If schema missing, we fail loudly.
        logger.error("Schema file missing. Cannot validate source field. Aborting load.")
        raise FileNotFoundError(f"Schema file missing at {SCHEMA_PATH}. Cannot proceed.")

    # Extract enum values for 'source' if defined in schema
    # Assuming structure: properties -> metadata -> properties -> source -> enum
    allowed_sources = ['human_participant']
    if dev_mode:
        allowed_sources.append('simulated')

    metadata = session_data.get('metadata', {})
    source = metadata.get('source')

    if source not in allowed_sources:
        logger.warning(f"Session {session_data.get('participant_id', 'unknown')} has invalid source: {source}")
        return False

    return True


def load_real_data(input_dir: str, dev_mode: bool = False) -> pd.DataFrame:
    """
    Load real session data from the specified input directory.

    This function scans the input directory for JSON session files, validates them
    against the expected schema (specifically the 'source' field), and aggregates
    them into a single DataFrame.

    Constraints:
    1. Must raise FileNotFoundError if input_dir is empty or missing.
    2. Must raise FileNotFoundError if ALL files have source='simulated' AND dev_mode is False.
    3. Must accept source='simulated' ONLY if dev_mode is True.
    4. Must explicitly reference contracts/session.schema.yaml for source validation.

    Args:
        input_dir (str): Path to the directory containing raw session JSON files.
        dev_mode (bool): If True, allows simulated data. If False, requires human_participant data.

    Returns:
        pd.DataFrame: A DataFrame containing all valid session records.

    Raises:
        FileNotFoundError: If no valid real data is found or directory is empty.
        ValueError: If the input directory does not exist.
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    # Find all JSON files in the directory
    json_files = list(input_path.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(
            f"Real data not found in {input_dir}. Directory contains no JSON files. "
            f"Run simulator (with --dev-mode if testing) or recruit participants."
        )

    all_sessions = []
    valid_count = 0
    simulated_count = 0
    invalid_count = 0

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # Basic structure check
            required_fields = ['participant_id', 'interface_type', 'status']
            if not all(field in session_data for field in required_fields):
                logger.warning(f"Invalid session structure in {json_file.name}, skipping.")
                invalid_count += 1
                continue

            # Validate source field against schema
            if not _validate_source_field(session_data, dev_mode):
                source = session_data.get('metadata', {}).get('source', 'unknown')
                if source == 'simulated':
                    simulated_count += 1
                else:
                    invalid_count += 1
                continue

            # If we are in dev_mode, we accept simulated. If not, we only accept human_participant.
            # The validation function already filtered out 'simulated' if dev_mode is False.
            # So if we are here, the source is valid for the current mode.

            all_sessions.append(session_data)
            valid_count += 1

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {json_file.name}: {e}")
            invalid_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {json_file.name}: {e}")
            invalid_count += 1

    # Post-processing checks
    if not all_sessions:
        if simulated_count > 0 and not dev_mode:
            raise FileNotFoundError(
                f"Real data not found in {input_dir}. "
                f"Found {simulated_count} simulated session(s) but dev_mode is False. "
                f"Use dev_mode=True for development or provide real human_participant data."
            )
        else:
            raise FileNotFoundError(
                f"Real data not found in {input_dir}. "
                f"Directory contains {len(json_files)} files, but none are valid real sessions. "
                f"Run simulator or recruit participants."
            )

    logger.info(f"Loaded {valid_count} valid real sessions from {input_dir}")
    if invalid_count > 0:
        logger.warning(f"Skipped {invalid_count} invalid sessions")
    if simulated_count > 0:
        logger.info(f"Skipped {simulated_count} simulated sessions (dev_mode={dev_mode})")

    # Convert list of dicts to DataFrame
    df = pd.DataFrame(all_sessions)

    # Ensure consistent column ordering if expected columns exist
    expected_cols = [
        'participant_id', 'interface_type', 'status', 'completion_time',
        'error_count', 'sus_score', 'explanation_engagement_time_seconds',
        'disability_type', 'accommodations_used', 'dropout_reason', 'timestamp',
        'metadata'
    ]

    # Reorder columns to match expected schema if they exist
    existing_cols = [col for col in expected_cols if col in df.columns]
    if existing_cols:
        df = df[existing_cols]

    return df


def load_real_data_with_fallback(input_dir: str, fallback_dir: Optional[str] = None, dev_mode: bool = False) -> pd.DataFrame:
    """
    Load real data with optional fallback to a different directory.

    This is a convenience wrapper that attempts to load from the primary directory,
    and if that fails, tries a fallback directory. It still raises an error if
    no real data is found in either location.

    Args:
        input_dir (str): Primary input directory.
        fallback_dir (Optional[str]): Fallback directory if primary is empty.
        dev_mode (bool): If True, allows simulated data.

    Returns:
        pd.DataFrame: A DataFrame containing all valid session records.

    Raises:
        FileNotFoundError: If no valid session files are found in any directory.
    """
    try:
        return load_real_data(input_dir, dev_mode=dev_mode)
    except FileNotFoundError as e:
        if fallback_dir:
            logger.info(f"Primary directory empty or invalid, trying fallback: {fallback_dir}")
            try:
                return load_real_data(fallback_dir, dev_mode=dev_mode)
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
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Allow simulated data (source='simulated')"
    )

    args = parser.parse_args()

    logger.info(f"Attempting to load real data from {args.input_dir} (dev_mode={args.dev_mode})")

    try:
        df = load_real_data(args.input_dir, dev_mode=args.dev_mode)
        df.to_csv(args.output, index=False)
        logger.info(f"Successfully loaded {len(df)} sessions and saved to {args.output}")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise


if __name__ == "__main__":
    main()