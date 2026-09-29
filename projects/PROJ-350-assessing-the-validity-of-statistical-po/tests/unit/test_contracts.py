"""
Unit tests for contract validation against JSON Schema.
Specifically tests T011: Verify output schema of study_records_raw.json.
"""
import json
import os
import pytest
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError, SchemaError

# Path constants relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "contracts" / "study_record.schema.yaml"
DATA_PATH = PROJECT_ROOT / "data" / "derived" / "study_records_raw.json"


def load_schema(schema_path: Path) -> dict:
    """Load YAML schema from file."""
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data(data_path: Path) -> list:
    """Load JSON data from file."""
    if not data_path.exists():
        pytest.fail(f"Data file not found: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestStudyRecordContract:
    """Contract tests for study_records_raw.json against study_record.schema.yaml."""

    def test_schema_file_exists(self):
        """Verify the schema file exists on disk."""
        assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

    def test_data_file_exists(self):
        """Verify the data file exists on disk."""
        assert DATA_PATH.exists(), f"Data file missing: {DATA_PATH}"

    def test_schema_is_valid_yaml(self):
        """Verify the schema file is valid YAML."""
        try:
            load_schema(SCHEMA_PATH)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in schema: {e}")

    def test_data_is_valid_json(self):
        """Verify the data file is valid JSON."""
        try:
            load_data(DATA_PATH)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in data file: {e}")

    def test_data_validates_against_schema(self):
        """
        Contract test: Verify data/derived/study_records_raw.json
        validates against specs/contracts/study_record.schema.yaml.
        """
        schema = load_schema(SCHEMA_PATH)
        data = load_data(DATA_PATH)

        # Validate that schema is a dict
        assert isinstance(schema, dict), "Schema must be a dictionary"

        # Perform validation
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(
                f"Data validation failed: {e.message} "
                f"(Path: {list(e.path)})"
            )
        except SchemaError as e:
            pytest.fail(f"Schema definition error: {e.message}")

    def test_data_structure_matches_requirements(self):
        """
        Additional check: Ensure the data is a list of records
        with the required fields as per the spec.
        """
        data = load_data(DATA_PATH)

        assert isinstance(data, list), "Root element must be a list"
        assert len(data) > 0, "Data list must not be empty"

        required_fields = [
            "study_id",
            "title",
            "planned_power",
            "target_n",
            "effect_size_assumption",
            "field",
            "missing_planned_data",
            "source_citation",
        ]

        for i, record in enumerate(data):
            assert isinstance(record, dict), f"Record {i} must be a dictionary"
            missing = [f for f in required_fields if f not in record]
            if missing:
                pytest.fail(
                    f"Record {i} is missing required fields: {missing}"
                )
