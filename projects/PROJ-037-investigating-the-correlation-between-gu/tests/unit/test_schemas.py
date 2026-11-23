import pytest
from code.schemas import get_schema, get_required_columns, get_optional_columns

class TestGetSchema:
    def test_schema_structure(self):
        """Test that the schema contains expected keys and structure."""
        schema = get_schema()
        assert 'columns' in schema
        assert isinstance(schema['columns'], dict)
        
        # Check for key columns
        expected_columns = ['participant_id', 'shannon', 'simpson', 'age', 'bmi', 
                          'sleep_duration', 'sleep_quality', 'chronotype', 'antibiotic_use']
        for col in expected_columns:
            assert col in schema['columns'], f"Missing column {col} in schema"

    def test_column_types(self):
        """Test that column types are correctly specified."""
        schema = get_schema()
        assert schema['columns']['participant_id']['type'] == 'str'
        assert schema['columns']['shannon']['type'] == 'float'
        assert schema['columns']['age']['type'] == 'int'
        assert schema['columns']['bmi']['type'] == 'float'
        assert schema['columns']['sleep_duration']['type'] == 'float'
        assert schema['columns']['sleep_quality']['type'] == 'float'
        assert schema['columns']['chronotype']['type'] == 'str'
        assert schema['columns']['antibiotic_use']['type'] == 'str'

class TestGetRequiredColumns:
    def test_required_columns_list(self):
        """Test that required columns are returned correctly."""
        required = get_required_columns()
        assert isinstance(required, list)
        assert 'participant_id' in required
        assert 'shannon' in required
        assert 'sleep_duration' in required
        assert 'antibiotic_use' in required

    def test_required_columns_not_empty(self):
        """Test that required columns list is not empty."""
        required = get_required_columns()
        assert len(required) > 0

class TestGetOptionalColumns:
    def test_optional_columns_list(self):
        """Test that optional columns are returned correctly."""
        optional = get_optional_columns()
        assert isinstance(optional, list)
        # Optional columns should exist but may vary based on implementation
        # Just verify it returns a list
        
    def test_optional_vs_required(self):
        """Test that optional columns don't overlap with required columns."""
        required = set(get_required_columns())
        optional = set(get_optional_columns())
        overlap = required.intersection(optional)
        assert len(overlap) == 0, f"Overlap found: {overlap}"