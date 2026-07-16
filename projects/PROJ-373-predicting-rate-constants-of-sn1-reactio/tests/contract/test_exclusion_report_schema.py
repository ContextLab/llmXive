import os
import yaml
import pytest
import pandas as pd
from pathlib import Path
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_DIR = PROJECT_ROOT / "specs" / "001-predict-sn1-rate-constants" / "contracts"

def load_schema(schema_name: str) -> dict:
    """Load a JSON/YAML schema from the contracts directory."""
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif schema_path.suffix == '.json':
            import json
            return json.load(f)
    raise ValueError(f"Unsupported schema format: {schema_path.suffix}")

def get_exclusion_report_path():
    """Returns the path to the exclusion report."""
    return PROJECT_ROOT / "data" / "processed" / "exclusion_report.csv"

class TestExclusionReportSchema:
    """Contract tests for the exclusion report schema."""

    @pytest.fixture
    def exclusion_schema(self):
        return load_schema("exclusion_report.schema.yaml")

    def test_schema_required_fields(self, exclusion_schema):
        """Verify required fields are defined."""
        required = exclusion_schema.get("required", [])
        assert "row_index" in required
        assert "reason" in required
        assert "original_smiles" in required

    def test_reason_enum_values(self, exclusion_schema):
        """Verify reason field has correct enum values."""
        props = exclusion_schema.get("properties", {})
        assert "reason" in props
        assert "enum" in props["reason"]
        expected = ["parsing_error", "missing_rate", "invalid_substrate"]
        assert set(props["reason"]["enum"]) == set(expected)

    def test_validate_actual_report(self, exclusion_schema):
        """Validate the actual exclusion report against the schema."""
        data_path = get_exclusion_report_path()
        if not data_path.exists():
            pytest.skip("Exclusion report file not found. Skipping data validation.")
        
        df = pd.read_csv(data_path)
        
        if df.empty:
            pytest.skip("Exclusion report is empty. Skipping row validation.")

        for idx, row in df.iterrows():
            record = row.to_dict()
            # Ensure row_index is int for validation if schema expects integer
            if isinstance(record.get('row_index'), float) and pd.isna(record['row_index']):
                continue 
                
            try:
                validate(instance=record, schema=exclusion_schema)
            except ValidationError as e:
                pytest.fail(f"Row {idx} in exclusion report failed schema validation: {e.message}")
