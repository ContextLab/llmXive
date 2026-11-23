import pytest
import yaml
import pandas as pd
from pathlib import Path
import sys

# Add code root to path if running directly
if "code" not in sys.path[0]:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from contracts.merged_perovskite_schema import SCHEMA_FIELDS

class TestSchemaValidation:
    """
    Contract test for merged_perovskite.schema.yaml.
    Verifies that the output CSV matches the defined schema.
    """

    @pytest.fixture
    def schema_path(self):
        return Path("contracts/merged_perovskite.schema.yaml")

    @pytest.fixture
    def output_path(self):
        return Path("data/cleaned/merged_perovskite.csv")

    def test_schema_file_exists(self, schema_path):
        """Ensure the schema file exists."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_contains_required_fields(self, schema_path):
        """Ensure the schema contains all required fields."""
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        fields = schema.get('fields', [])
        field_names = [f['name'] for f in fields]
        
        required = [
            'structure_id', 'thermal_conductivity', 'source_reference',
            'chemistry_class', 'temperature', 'tilting_angle',
            'bond_length_variance', 'tolerance_factor', 'unit_cell_volume'
        ]
        
        for req in required:
            assert req in field_names, f"Missing required field: {req}"

    def test_output_matches_schema(self, output_path, schema_path):
        """Ensure the generated output CSV matches the schema."""
        assert output_path.exists(), f"Output file not found at {output_path}"
        
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        df = pd.read_csv(output_path)
        columns = df.columns.tolist()
        
        for field in schema['fields']:
            name = field['name']
            assert name in columns, f"Column {name} missing from output CSV"

    def test_no_nulls_in_critical_columns(self, output_path):
        """Ensure critical columns have no null values."""
        assert output_path.exists()
        df = pd.read_csv(output_path)
        
        critical = ['structure_id', 'thermal_conductivity']
        for col in critical:
            assert col in df.columns, f"Critical column {col} missing"
            assert not df[col].isnull().any(), f"Null values found in {col}"