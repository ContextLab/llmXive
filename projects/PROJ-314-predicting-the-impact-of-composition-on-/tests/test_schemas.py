import pytest
from pathlib import Path
import sys
import os

# Add code to path if running directly
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from contracts.validate_schemas import validate_ceramic_entry_schema, validate_model_result_schema

def test_ceramic_entry_schema_exists_and_valid():
    """Test that ceramic_entry.schema.yaml exists and has required fields."""
    schema_path = Path(__file__).parent.parent / "code" / "contracts" / "ceramic_entry.schema.yaml"
    assert schema_path.exists(), "ceramic_entry.schema.yaml not found"
    result = validate_ceramic_entry_schema(schema_path)
    assert result is True

def test_model_result_schema_exists_and_valid():
    """Test that model_result.schema.yaml exists and has required fields."""
    schema_path = Path(__file__).parent.parent / "code" / "contracts" / "model_result.schema.yaml"
    assert schema_path.exists(), "model_result.schema.yaml not found"
    result = validate_model_result_schema(schema_path)
    assert result is True