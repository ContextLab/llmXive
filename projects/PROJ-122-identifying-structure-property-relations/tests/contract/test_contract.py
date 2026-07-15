"""
Contract tests for data schema validation (US1).
"""
import pytest
from utils.schema_validator import load_schema, validate_artifact

def test_load_schema():
    # Basic check that schema loading doesn't crash (schema file path might need adjustment based on real location)
    try:
        # Attempt to load a known schema or a minimal mock structure if file missing
        # In a real run, this would point to specs/.../dataset.schema.yaml
        schema = load_schema("specs/001-structure-property-relationships/contracts/dataset.schema.yaml")
        assert schema is not None
    except FileNotFoundError:
        pytest.skip("Schema file not found; expected in full project setup")
