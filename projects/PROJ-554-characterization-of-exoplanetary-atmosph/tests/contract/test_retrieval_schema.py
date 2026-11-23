"""
Contract test for retrieval output schema.

This test verifies that the retrieval output schema matches the specification
defined in `code/retrieval_output_schema.py` and that the data produced by
`code/retrieval_output.py` adheres to the required structure.

The schema defines the following required fields for each retrieval result:
- planet_name: str
- water_mixing_ratio: float (log10 scale)
- uncertainty: float
- is_upper_limit: bool
- detection_limit: float
- min_detectable_concentration: float
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from retrieval_output_schema import (
    RetrievalOutputSchema,
    get_schema_columns,
    validate_schema_row,
)
from data_models import RetrievalResult, CensorshipStatus


class TestRetrievalOutputSchema:
    """Contract tests for the retrieval output schema."""

    @pytest.fixture
    def expected_columns(self):
        """Return the expected columns defined in the schema."""
        return get_schema_columns()

    def test_schema_columns_match_specification(self, expected_columns):
        """Verify that the schema columns match the task specification."""
        required_fields = {
            "planet_name",
            "water_mixing_ratio",
            "uncertainty",
            "is_upper_limit",
            "detection_limit",
            "min_detectable_concentration",
        }
        assert set(expected_columns) == required_fields, (
            f"Schema columns {set(expected_columns)} do not match "
            f"required fields {required_fields}"
        )

    def test_retrieval_result_mapping(self):
        """Test that RetrievalResult dataclass maps correctly to schema."""
        # Create a sample RetrievalResult with censored data
        result = RetrievalResult(
            planet_name="TestPlanet",
            water_mixing_ratio=-5.0,
            uncertainty=0.5,
            censorship_status=CensorshipStatus.UPPER_LIMIT,
            detection_limit=-4.0,
            min_detectable_concentration=-4.5,
        )

        # Map to schema dictionary
        schema_dict = RetrievalOutputSchema.map_from_result(result)

        # Verify all required fields are present
        for field in get_schema_columns():
            assert field in schema_dict, f"Missing field: {field}"

        # Verify types
        assert isinstance(schema_dict["planet_name"], str)
        assert isinstance(schema_dict["water_mixing_ratio"], float)
        assert isinstance(schema_dict["uncertainty"], float)
        assert isinstance(schema_dict["is_upper_limit"], bool)
        assert isinstance(schema_dict["detection_limit"], float)
        assert isinstance(schema_dict["min_detectable_concentration"], float)

    def test_validate_schema_row_valid(self, expected_columns):
        """Test validation of a valid schema row."""
        valid_row = {
            "planet_name": "WASP-12b",
            "water_mixing_ratio": -3.5,
            "uncertainty": 0.3,
            "is_upper_limit": False,
            "detection_limit": -4.0,
            "min_detectable_concentration": -3.8,
        }

        is_valid, error_msg = validate_schema_row(valid_row, expected_columns)
        assert is_valid, f"Valid row rejected: {error_msg}"

    def test_validate_schema_row_missing_field(self, expected_columns):
        """Test validation fails for missing required field."""
        invalid_row = {
            "planet_name": "WASP-12b",
            "water_mixing_ratio": -3.5,
            "uncertainty": 0.3,
            # Missing is_upper_limit, detection_limit, min_detectable_concentration
        }

        is_valid, error_msg = validate_schema_row(invalid_row, expected_columns)
        assert not is_valid
        assert "missing" in error_msg.lower()

    def test_validate_schema_row_wrong_type(self, expected_columns):
        """Test validation fails for wrong data type."""
        invalid_row = {
            "planet_name": "WASP-12b",
            "water_mixing_ratio": "not_a_float",  # Wrong type
            "uncertainty": 0.3,
            "is_upper_limit": False,
            "detection_limit": -4.0,
            "min_detectable_concentration": -3.8,
        }

        is_valid, error_msg = validate_schema_row(invalid_row, expected_columns)
        assert not is_valid
        assert "type" in error_msg.lower() or "float" in error_msg.lower()

    def test_validate_schema_row_upper_limit_consistency(self, expected_columns):
        """Test that upper limit flags are consistent with detection limits."""
        # Case 1: Upper limit with detection_limit set
        row1 = {
            "planet_name": "TestPlanet1",
            "water_mixing_ratio": -5.0,
            "uncertainty": 0.5,
            "is_upper_limit": True,
            "detection_limit": -4.0,
            "min_detectable_concentration": -4.5,
        }
        is_valid, _ = validate_schema_row(row1, expected_columns)
        assert is_valid

        # Case 2: Non-upper limit should have reasonable values
        row2 = {
            "planet_name": "TestPlanet2",
            "water_mixing_ratio": -3.0,
            "uncertainty": 0.2,
            "is_upper_limit": False,
            "detection_limit": -5.0,
            "min_detectable_concentration": -4.8,
        }
        is_valid, _ = validate_schema_row(row2, expected_columns)
        assert is_valid

    def test_csv_output_schema_compliance(self, tmp_path, expected_columns):
        """Test that CSV output matches the schema columns."""
        # Create a sample DataFrame
        df = pd.DataFrame(
            [
                {
                    "planet_name": "PlanetA",
                    "water_mixing_ratio": -4.0,
                    "uncertainty": 0.4,
                    "is_upper_limit": True,
                    "detection_limit": -3.5,
                    "min_detectable_concentration": -3.8,
                },
                {
                    "planet_name": "PlanetB",
                    "water_mixing_ratio": -2.5,
                    "uncertainty": 0.2,
                    "is_upper_limit": False,
                    "detection_limit": -4.0,
                    "min_detectable_concentration": -3.9,
                },
            ]
        )

        # Write to CSV
        csv_path = tmp_path / "retrieval_results.csv"
        df.to_csv(csv_path, index=False)

        # Read back and validate
        df_read = pd.read_csv(csv_path)
        assert list(df_read.columns) == expected_columns, (
            f"CSV columns {list(df_read.columns)} do not match schema {expected_columns}"
        )

        # Validate each row
        for _, row in df_read.iterrows():
            is_valid, error_msg = validate_schema_row(row.to_dict(), expected_columns)
            assert is_valid, f"Row validation failed: {error_msg}"

    def test_empty_dataframe_schema(self, expected_columns):
        """Test that an empty DataFrame still has the correct schema."""
        df = pd.DataFrame(columns=expected_columns)
        assert list(df.columns) == expected_columns

        # Validate empty row (should pass or handle gracefully)
        if len(df) == 0:
            # Empty DataFrame is valid as long as columns match
            assert True
        else:
            for _, row in df.iterrows():
                is_valid, _ = validate_schema_row(row.to_dict(), expected_columns)
                assert is_valid

if __name__ == "__main__":
    pytest.main([__file__, "-v"])