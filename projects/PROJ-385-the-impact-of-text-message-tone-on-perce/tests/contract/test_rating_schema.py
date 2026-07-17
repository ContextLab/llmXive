"""
Contract test for the rating schema.

Validates that artifacts produced by T006 (schema definition) are correctly
implemented by T014 (simulate_ratings.py) and T006 (schema definition).

This test ensures:
1. The rating schema file exists and is valid JSON/YAML.
2. The generated ratings data (data/raw/ratings.csv) conforms to the schema.
3. All required fields are present and have correct types.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

# Import schema validation utilities if available
try:
    from validate_schemas import load_schema, validate_json_against_schema
except ImportError:
    # Fallback if validate_schemas is not yet available or different structure
    def load_schema(schema_path: Path) -> Dict[str, Any]:
        """Load a JSON schema from file."""
        with open(schema_path, 'r') as f:
            return json.load(f)

    def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Simple validation of JSON data against a JSON schema.
        Checks for required fields and basic type constraints.
        """
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check types for known fields
        for field, spec in properties.items():
            if field in data:
                expected_type = spec.get('type')
                value = data[field]
                
                if expected_type == 'string' and not isinstance(value, str):
                    raise TypeError(f"Field {field} should be string, got {type(value)}")
                elif expected_type == 'integer' and not isinstance(value, int):
                    raise TypeError(f"Field {field} should be integer, got {type(value)}")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    raise TypeError(f"Field {field} should be number, got {type(value)}")
        
        return True

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def get_schema_path() -> Path:
    """Get the path to the rating schema file."""
    return get_project_root() / "specs" / "001-text-tone-emotional-support" / "contracts" / "rating.schema.yaml"

def get_ratings_path() -> Path:
    """Get the path to the generated ratings CSV file."""
    return get_project_root() / "data" / "raw" / "ratings.csv"

def load_csv_as_records(csv_path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file and return a list of dictionaries (records)."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    return df.to_dict(orient='records')

def test_rating_schema_exists():
    """Test that the rating schema file exists."""
    schema_path = get_schema_path()
    assert schema_path.exists(), f"Rating schema file not found at {schema_path}"
    print(f"✓ Rating schema file found at {schema_path}")

def test_rating_schema_is_valid_json():
    """Test that the rating schema is valid JSON (or YAML that can be parsed as JSON-like)."""
    schema_path = get_schema_path()
    try:
        # Try loading as JSON first
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        print("✓ Rating schema is valid JSON")
        return schema
    except json.JSONDecodeError:
        # If it's YAML, we need to handle it differently
        # For now, assume it's JSON as per T006 specification
        # If it's YAML, we'd need PyYAML installed
        try:
            import yaml
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            print("✓ Rating schema is valid YAML")
            return schema
        except ImportError:
            raise AssertionError("Schema is not valid JSON and PyYAML is not available to parse YAML")

def test_ratings_file_exists():
    """Test that the ratings CSV file exists."""
    ratings_path = get_ratings_path()
    assert ratings_path.exists(), f"Ratings file not found at {ratings_path}"
    print(f"✓ Ratings file found at {ratings_path}")

def test_ratings_conform_to_schema():
    """Test that the ratings data conforms to the schema."""
    schema_path = get_schema_path()
    ratings_path = get_ratings_path()
    
    # Load schema
    try:
        with open(schema_path, 'r') as f:
            import json
            schema = json.load(f)
    except json.JSONDecodeError:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    
    # Load ratings data
    records = load_csv_as_records(ratings_path)
    assert len(records) > 0, "Ratings file is empty"
    
    # Validate each record
    errors = []
    for i, record in enumerate(records):
        try:
            validate_json_against_schema(record, schema)
        except (ValueError, TypeError) as e:
            errors.append(f"Record {i}: {str(e)}")
    
    if errors:
        raise AssertionError(f"Schema validation failed for {len(errors)} records:\n" + "\n".join(errors[:5]))
    
    print(f"✓ All {len(records)} rating records conform to the schema")

def test_required_fields_present():
    """Test that all required fields defined in the schema are present in the data."""
    schema_path = get_schema_path()
    ratings_path = get_ratings_path()
    
    # Load schema
    try:
        with open(schema_path, 'r') as f:
            import json
            schema = json.load(f)
    except json.JSONDecodeError:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    
    required_fields = schema.get('required', [])
    assert len(required_fields) > 0, "No required fields defined in schema"
    
    # Load data
    records = load_csv_as_records(ratings_path)
    
    # Check first record for all required fields
    first_record = records[0]
    missing_fields = [field for field in required_fields if field not in first_record]
    
    assert len(missing_fields) == 0, f"Missing required fields: {missing_fields}"
    print(f"✓ All required fields ({', '.join(required_fields)}) are present in the data")

def run_all_tests():
    """Run all contract tests."""
    print("Running rating schema contract tests...")
    
    test_rating_schema_exists()
    test_rating_schema_is_valid_json()
    test_ratings_file_exists()
    test_required_fields_present()
    test_ratings_conform_to_schema()
    
    print("\n✓ All contract tests passed!")

if __name__ == "__main__":
    run_all_tests()