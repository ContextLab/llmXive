"""
Contract test for SquarefreeSequence schema.

Validates that a generated SquarefreeSequence object conforms to
contracts/Squarefree_sequence.schema.yaml.
"""
import json
import os
import sys
from pathlib import Path

import yaml
import jsonschema

# Add project root to path to allow imports from code/ if needed,
# though this test primarily relies on schema validation.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_sample_sequence(n: int = 100) -> dict:
    """
    Generate a minimal valid SquarefreeSequence sample for testing.
    This mimics the structure expected by the schema without running
    the full sieve (since T012a is not yet implemented).
    """
    # Hardcoded small list of squarefree numbers for validation testing
    # 1, 2, 3, 5, 6, 7, 10...
    sample_numbers = [1, 2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30]
    
    return {
        "N": n,
        "count": len(sample_numbers),
        "squarefree_numbers": sample_numbers,
        "generation_timestamp": "2023-10-27T10:00:00Z",
        "source": "unit_test_mock"
    }

def test_squarefree_sequence_schema():
    """
    Validates JSON against contracts/SquarefreeSequence.schema.yaml.
    
    This is a contract test ensuring the data model matches the schema.
    """
    schema_path = project_root / "contracts" / "SquarefreeSequence.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    schema = load_schema(str(schema_path))
    sample_data = generate_sample_sequence(n=20)

    try:
        jsonschema.validate(instance=sample_data, schema=schema)
        print("Schema validation successful: Sample data conforms to SquarefreeSequence.schema.yaml")
    except jsonschema.exceptions.ValidationError as e:
        print(f"Schema validation failed: {e.message}")
        print(f"Path: {list(e.path)}")
        raise AssertionError(f"SquarefreeSequence data does not match schema: {e.message}") from e

if __name__ == "__main__":
    test_squarefree_sequence_schema()
