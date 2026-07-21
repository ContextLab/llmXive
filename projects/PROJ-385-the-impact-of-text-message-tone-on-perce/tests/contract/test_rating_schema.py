"""
Contract test for rating data schema.

Validates that data/raw/ratings.csv (produced by T014) conforms to the
rating.schema.yaml definition (produced by T006).

This test MUST run after T014 completes.
"""
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

# Add parent directory to path to allow imports from config
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_raw_data_dir, get_contracts_dir
from validate_schemas import load_schema, validate_json_against_schema


def load_ratings_csv(path: Path) -> List[Dict[str, Any]]:
    """Load the ratings CSV file and return a list of row dictionaries."""
    if not path.exists():
        raise FileNotFoundError(f"Ratings file not found: {path}")
    
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to appropriate types for validation
            # We do this because JSON schema validation expects actual types
            processed_row = {}
            for key, value in row.items():
                if key in ["participant_id", "stimulus_id", "relationship_context"]:
                    processed_row[key] = str(value)
                elif key in ["rating_value", "response_time_ms", "attention_check_passed"]:
                    # rating_value is integer (Likert scale)
                    try:
                        processed_row[key] = int(value)
                    except ValueError:
                        processed_row[key] = value
                elif key == "response_time_ms":
                    # response_time_ms is integer
                    try:
                        processed_row[key] = int(value)
                    except ValueError:
                        processed_row[key] = value
                elif key == "attention_check_passed":
                    # boolean string -> bool
                    processed_row[key] = value.lower() in ["true", "1", "yes"]
                else:
                    processed_row[key] = value
            rows.append(processed_row)
    
    return rows


def get_required_fields(schema: Dict[str, Any]) -> Set[str]:
    """Extract required field names from a JSON schema."""
    return set(schema.get("required", []))


def validate_ratings_schema():
    """
    Validate ratings.csv against rating.schema.yaml.
    
    Returns:
        bool: True if validation passes, False otherwise.
    
    Raises:
        AssertionError: If validation fails.
    """
    # Paths
    raw_dir = get_raw_data_dir()
    contracts_dir = get_contracts_dir()
    ratings_path = raw_dir / "ratings.csv"
    schema_path = contracts_dir / "rating.schema.yaml"
    
    # Check files exist
    if not ratings_path.exists():
        raise FileNotFoundError(
            f"Ratings file not found: {ratings_path}. "
            "Ensure T014 (simulate_ratings) has completed successfully."
        )
    
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found: {schema_path}. "
            "Ensure T006 (schema definition) has completed successfully."
        )
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load ratings
    ratings = load_ratings_csv(ratings_path)
    
    if not ratings:
        raise ValueError("Ratings file is empty or has no data rows.")
    
    # Get required fields from schema
    required_fields = get_required_fields(schema)
    
    # Check that all rows have required fields
    errors = []
    for i, row in enumerate(ratings):
        missing = required_fields - set(row.keys())
        if missing:
            errors.append(f"Row {i+1}: Missing required fields: {missing}")
        
        # Check field types
        for field_name, field_schema in schema.get("properties", {}).items():
            if field_name in row:
                value = row[field_name]
                expected_type = field_schema.get("type")
                
                if expected_type == "integer" and not isinstance(value, int):
                    errors.append(
                        f"Row {i+1}: Field '{field_name}' should be integer, got {type(value).__name__}"
                    )
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(
                        f"Row {i+1}: Field '{field_name}' should be boolean, got {type(value).__name__}"
                    )
                elif expected_type == "string" and not isinstance(value, str):
                    errors.append(
                        f"Row {i+1}: Field '{field_name}' should be string, got {type(value).__name__}"
                    )
                
                # Check enum constraints
                if "enum" in field_schema:
                    if value not in field_schema["enum"]:
                        errors.append(
                            f"Row {i+1}: Field '{field_name}' value '{value}' not in allowed values: {field_schema['enum']}"
                        )
                
                # Check format constraints (e.g., P-IDs)
                if field_name == "participant_id":
                    # Prolific IDs should match pattern P-XXXXXXXX
                    import re
                    if not re.match(r"^P-[A-Z0-9]{8}$", str(value)):
                        errors.append(
                            f"Row {i+1}: participant_id '{value}' does not match expected format P-XXXXXXXX"
                        )
                
                # Check rating_value range (Likert 1-7)
                if field_name == "rating_value":
                    if not (1 <= value <= 7):
                        errors.append(
                            f"Row {i+1}: rating_value {value} is outside valid range [1, 7]"
                        )
    
    if errors:
        error_msg = "Schema validation failed:\n" + "\n".join(errors[:10])  # Limit to first 10 errors
        if len(errors) > 10:
            error_msg += f"\n... and {len(errors) - 10} more errors"
        raise AssertionError(error_msg)
    
    print(f"✓ Ratings schema validation passed: {len(ratings)} rows validated")
    return True


def main():
    """Entry point for contract test."""
    try:
        validate_ratings_schema()
        return 0
    except (FileNotFoundError, ValueError, AssertionError) as e:
        print(f"✗ Ratings schema validation failed: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())