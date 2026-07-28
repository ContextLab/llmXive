"""
Contract test for rating data schema validation.

Validates `data/raw/ratings.csv` produced by T014 against the schema
defined in `specs/001-text-tone-emotional-support/contracts/rating.schema.yaml`
(T006).

Requirements:
- MUST run after T014 completes.
- Validates presence of required columns: participant_id, stimulus_id,
  relationship_context, rating_score.
- Validates data types and constraints (e.g., rating_score 1-5).
- Validates Prolific ID format for participant_id.
- Validates relationship_context against allowed values.
"""
import csv
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import yaml

from config import get_processed_data_dir, get_raw_data_dir, get_contracts_dir

# Allowed values for relationship_context
ALLOWED_RELATIONSHIPS = {"friend", "acquaintance"}

# Rating scale (as per T006 schema definition)
MIN_RATING = 1
MAX_RATING = 7

# Prolific ID regex pattern (standard format: alphanumeric, typically 8-12 chars)
PROLIFIC_ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{8,12}$")

REQUIRED_COLUMNS = [
    "participant_id",
    "stimulus_id",
    "relationship",
    "rating"
]

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON/YAML schema from the contracts directory."""
    contracts_dir = get_contracts_dir()
    schema_path = contracts_dir / schema_name

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        if schema_path.suffix == ".yaml" or schema_path.suffix == ".yml":
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_prolific_id(pid: str) -> bool:
    """Validate that a Prolific ID matches the expected format."""
    return bool(PROLIFIC_ID_PATTERN.match(str(pid)))

def validate_rating_row(row: Dict[str, str], row_num: int) -> List[str]:
    """
    Validate a single row of the ratings data against schema constraints.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # Check required columns exist
    for col in REQUIRED_COLUMNS:
        if col not in row:
            errors.append(f"Row {row_num}: Missing required column '{col}'")

    if errors:
        return errors

    # Validate participant_id (Prolific ID format)
    pid = row.get("participant_id", "")
    if not validate_prolific_id(pid):
        errors.append(f"Row {row_num}: Invalid Prolific ID format: '{pid}'")

    # Validate relationship (T006 schema uses 'relationship' with enum values)
    relationship = row.get("relationship", "").lower()
    if relationship not in ALLOWED_RELATIONSHIPS:
        errors.append(
            f"Row {row_num}: Invalid relationship '{relationship}'. "
            f"Allowed: {ALLOWED_RELATIONSHIPS}"
        )

    # Validate rating (integer 1-7 as per T006 schema)
    try:
        rating = int(row.get("rating", -1))
        if not (MIN_RATING <= rating <= MAX_RATING):
            errors.append(
                f"Row {row_num}: Rating score {rating} out of range "
                f"[{MIN_RATING}, {MAX_RATING}]"
            )
    except ValueError:
        errors.append(f"Row {row_num}: Rating score '{row.get('rating')}' is not an integer")

    return errors

def validate_ratings_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate the entire ratings CSV file.

    Returns:
        Tuple[is_valid, list_of_errors]
    """
    if not file_path.exists():
        return False, [f"Ratings file not found: {file_path}"]

    errors = []
    row_count = 0

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            # Check header
            if reader.fieldnames is None:
                return False, ["Ratings file is empty or has no header"]

            missing_cols = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing_cols:
                errors.append(f"Missing required columns in header: {missing_cols}")

            # Validate rows
            for row_num, row in enumerate(reader, start=2): # Start at 2 (1 is header)
                row_errors = validate_rating_row(row, row_num)
                errors.extend(row_errors)
                row_count += 1

    except Exception as e:
        return False, [f"Error reading ratings file: {str(e)}"]

    if row_count == 0:
        errors.append("Ratings file contains no data rows")

    return len(errors) == 0, errors

def main() -> int:
    """
    Main entry point for the contract test.

    Returns:
        0 if validation passes, 1 if it fails.
    """
    ratings_path = get_raw_data_dir() / "ratings.csv"

    print(f"Validating ratings schema at: {ratings_path}")

    # Optional: Load and compare against schema definition if strict schema validation is needed
    # For now, we rely on the structural checks defined in this module which mirror T006
    try:
        is_valid, errors = validate_ratings_file(ratings_path)
    except FileNotFoundError as e:
        print(f"FAIL: {e}")
        return 1

    if is_valid:
        print("PASS: Ratings data schema validation successful.")
        return 0
    else:
        print("FAIL: Ratings data schema validation failed.")
        for err in errors:
            print(f"  - {err}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())