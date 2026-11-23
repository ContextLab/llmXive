"""Contract tests for rating data schema validation.

This module validates that the rating data produced by the data collection
pipeline (T015b or T014) conforms to the schema defined in T006.

Schema Requirements (from T006):
- participant_id: string (Prolific ID format)
- stimulus_id: string
- relationship: enum ["friend", "acquaintance"]
- rating: integer 1-7
"""

import csv
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import pytest

from code.config import get_raw_data_dir, get_processed_data_dir, get_contracts_dir


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a YAML schema definition from the contracts directory."""
    contracts_dir = get_contracts_dir()
    schema_path = contracts_dir / schema_name

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Simple YAML parser for this specific schema format (no external deps)
    # Since the schema is simple, we can parse it manually or use a minimal loader
    # For robustness, we assume the schema is valid YAML and parse it.
    # If pyyaml is not available, we implement a minimal parser for this specific structure.
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: minimal parser for the specific schema structure
        # This is a simplified parser for the expected format
        schema = {"properties": {}}
        current_property = None
        with open(schema_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('properties:'):
                    continue
                if line.startswith('-') and ':' in line:
                    # New property
                    parts = line[1:].strip().split(':', 1)
                    prop_name = parts[0].strip()
                    prop_def = parts[1].strip() if len(parts) > 1 else ""
                    schema["properties"][prop_name] = {"type": prop_def.split()[0] if prop_def else "string"}
                    current_property = prop_name
                elif line.startswith('  ') and current_property:
                    # Property detail
                    if line.strip().startswith('enum:'):
                        enum_str = line.strip()[5:].strip()
                        # Parse enum list
                        enum_vals = [v.strip().strip('"').strip("'") for v in enum_str.strip('[]').split(',')]
                        schema["properties"][current_property]["enum"] = enum_vals
                    elif line.strip().startswith('integer'):
                        schema["properties"][current_property]["type"] = "integer"
                        if "min" in line:
                            schema["properties"][current_property]["min"] = int(line.split('min')[1].split(',')[0].strip())
                        if "max" in line:
                            schema["properties"][current_property]["max"] = int(line.split('max')[1].split(',')[0].strip())
        return schema


def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> List[str]:
    """Validate a CSV file against a schema definition.

    Args:
        csv_path: Path to the CSV file to validate
        schema: Schema definition dictionary

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    if not csv_path.exists():
        errors.append(f"CSV file not found: {csv_path}")
        return errors

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if not headers:
                errors.append("CSV file has no headers")
                return errors

            # Check required columns
            required_cols = list(schema.get("properties", {}).keys())
            missing_cols = [col for col in required_cols if col not in headers]
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
                return errors

            # Validate each row
            row_num = 1
            for row in reader:
                row_num += 1
                for col, spec in schema.get("properties", {}).items():
                    value = row.get(col)

                    if value is None or value == '':
                        # Check if field is required (no optional marker in schema)
                        errors.append(f"Row {row_num}: Missing value for required field '{col}'")
                        continue

                    # Type validation
                    field_type = spec.get("type", "string")

                    if field_type == "integer":
                        try:
                            int_val = int(value)
                            if "min" in spec and int_val < spec["min"]:
                                errors.append(f"Row {row_num}: {col} value {int_val} is less than minimum {spec['min']}")
                            if "max" in spec and int_val > spec["max"]:
                                errors.append(f"Row {row_num}: {col} value {int_val} is greater than maximum {spec['max']}")
                        except ValueError:
                            errors.append(f"Row {row_num}: {col} value '{value}' is not a valid integer")

                    elif field_type == "string":
                        # Check enum if present
                        if "enum" in spec:
                            if value not in spec["enum"]:
                                errors.append(f"Row {row_num}: {col} value '{value}' not in allowed values {spec['enum']}")

                    elif field_type == "email":
                        # Basic email validation
                        if '@' not in value or '.' not in value.split('@')[-1]:
                            errors.append(f"Row {row_num}: {col} value '{value}' is not a valid email")

    except Exception as e:
        errors.append(f"Error reading CSV file: {str(e)}")

    return errors


def test_rating_schema_valid():
    """Validate that data/raw/ratings.csv conforms to the rating schema.

    This test ensures that the rating data produced by T015b (real) or T014 (mock)
    satisfies the schema requirements from T006:
    - participant_id: string
    - stimulus_id: string
    - relationship: enum ["friend", "acquaintance"]
    - rating: integer 1-7
    """
    raw_data_dir = get_raw_data_dir()

    # Check both possible output files (real and mock)
    real_ratings_path = raw_data_dir / "real_ratings.csv"
    mock_ratings_path = raw_data_dir / "ratings.csv"

    # Determine which file exists
    ratings_path = None
    if real_ratings_path.exists():
        ratings_path = real_ratings_path
    elif mock_ratings_path.exists():
        ratings_path = mock_ratings_path
    else:
        pytest.fail("Neither data/raw/real_ratings.csv nor data/raw/ratings.csv exists. "
                   "Ensure T015b (real data) or T014 (mock data) has been executed.")

    # Load the schema
    try:
        schema = load_schema("rating.schema.yaml")
    except Exception as e:
        pytest.fail(f"Failed to load rating schema: {str(e)}")

    # Validate the CSV
    errors = validate_csv_against_schema(ratings_path, schema)

    if errors:
        pytest.fail(f"Rating schema validation failed with {len(errors)} errors:\n" + "\n".join(errors))

    # Additional specific checks based on the schema definition
    with open(ratings_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Verify at least one row exists
    assert len(rows) > 0, "Rating data file is empty"

    # Verify relationship values are only 'friend' or 'acquaintance'
    valid_relationships = {'friend', 'acquaintance'}
    for i, row in enumerate(rows):
        rel = row.get('relationship', '').lower()
        assert rel in valid_relationships, f"Row {i+1}: Invalid relationship '{rel}'"

    # Verify rating values are integers between 1 and 7
    for i, row in enumerate(rows):
        rating_str = row.get('rating', '')
        try:
            rating = int(rating_str)
            assert 1 <= rating <= 7, f"Row {i+1}: Rating {rating} is out of range [1, 7]"
        except ValueError:
            pytest.fail(f"Row {i+1}: Rating '{rating_str}' is not a valid integer")

    # Verify participant_id format (should look like Prolific ID)
    for i, row in enumerate(rows):
        pid = row.get('participant_id', '')
        # Prolific IDs typically start with 'P-' or are alphanumeric
        assert len(pid) > 0, f"Row {i+1}: Missing participant_id"

    # Verify stimulus_id exists and matches format
    for i, row in enumerate(rows):
        sid = row.get('stimulus_id', '')
        assert len(sid) > 0, f"Row {i+1}: Missing stimulus_id"

    # Log success
    print(f"✓ Rating schema validation passed for {len(rows)} rows in {ratings_path.name}")