import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import yaml

from src.validation.validate_contracts import (
    ValidationResult,
    validate_dataframe,
    validate_game_records,
    assert_valid,
    assert_game_records_valid
)
from src.config import get_contract_path


class TestValidationModule:
    @pytest.fixture
    def mock_schema_dir(self, tmp_path):
        """Create a temporary directory with mock schema files."""
        # Create specs/contracts structure in temp dir
        contracts_dir = tmp_path / "specs" / "contracts"
        contracts_dir.mkdir(parents=True)

        # Create game_record schema
        schema_data = {
            "columns": [
                "game_id", "white_rating", "black_rating", "eco_code",
                "avg_move_time_white", "avg_move_time_black",
                "material_imbalance_move5", "outcome",
                "elo_expected_prob", "outcome_deviation"
            ],
            "types": {
                "game_id": str,
                "white_rating": (int, float),
                "black_rating": (int, float),
                "eco_code": str,
                "avg_move_time_white": (int, float),
                "avg_move_time_black": (int, float),
                "material_imbalance_move5": (int, float),
                "outcome": str,
                "elo_expected_prob": float,
                "outcome_deviation": float
            }
        }

        with open(contracts_dir / "game_record.schema.yaml", 'w') as f:
            yaml.dump(schema_data, f)

        return contracts_dir

    def test_validate_dataframe_basic(self):
        """Test basic DataFrame validation."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0]
        })

        result = validate_dataframe(
            df,
            schema_name="test_schema",
            required_columns=["id", "value"],
            column_types={"id": int, "value": float}
        )

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_dataframe_missing_columns(self):
        """Test validation fails with missing columns."""
        df = pd.DataFrame({"id": [1, 2]})

        result = validate_dataframe(
            df,
            schema_name="test_schema",
            required_columns=["id", "missing_col"],
            column_types={}
        )

        assert not result.is_valid
        assert "Missing required columns" in str(result.errors)

    def test_validate_dataframe_null_values(self):
        """Test validation fails with null values in required columns."""
        df = pd.DataFrame({
            "id": [1, None, 3],
            "value": [10.0, 20.0, 30.0]
        })

        result = validate_dataframe(
            df,
            schema_name="test_schema",
            required_columns=["id", "value"],
            column_types={"id": int}
        )

        assert not result.is_valid
        assert any("null" in err for err in result.errors)

    def test_assert_valid_passes(self):
        """Test assert_valid does not raise on valid result."""
        result = ValidationResult(is_valid=True, schema_name="test")
        # Should not raise
        assert_valid(result)

    def test_assert_valid_raises(self):
        """Test assert_valid raises AssertionError on invalid result."""
        result = ValidationResult(is_valid=False, errors=["Error 1"], schema_name="test")
        with pytest.raises(AssertionError):
            assert_valid(result)

    def test_validate_game_records_valid(self, mock_schema_dir):
        """Test validation of a valid game records DataFrame."""
        df = pd.DataFrame({
            "game_id": ["g1", "g2"],
            "white_rating": [1500, 1600],
            "black_rating": [1400, 1500],
            "eco_code": ["B00", "C50"],
            "avg_move_time_white": [10.5, 12.0],
            "avg_move_time_black": [11.0, 13.0],
            "material_imbalance_move5": [0, 1],
            "outcome": ["1-0", "0-1"],
            "elo_expected_prob": [0.6, 0.4],
            "outcome_deviation": [0.4, -0.4]
        })

        # Temporarily override get_contract_path behavior if needed,
        # but since we created the file in the temp path, we rely on the
        # fallback logic in validate_game_records if the real path isn't found,
        # OR we ensure the test environment has the file.
        # For this unit test, we will rely on the fallback logic inside the function
        # if the file isn't at the actual project path, OR we mock the path.
        # Given the constraint to not mock heavily, we assume the fallback works
        # or the file exists in the real project structure during integration.
        # Here we test the logic assuming the schema is found or fallback is used.

        result = validate_game_records(df)
        assert result.is_valid, f"Validation failed: {result.errors}"

    def test_validate_game_records_invalid(self, mock_schema_dir):
        """Test validation fails on invalid game records."""
        df = pd.DataFrame({
            "game_id": ["g1", "g2"],
            "white_rating": [1500, 1600],
            # Missing other required columns
        })

        result = validate_game_records(df)
        assert not result.is_valid
        assert "Missing required columns" in str(result.errors)

    def test_assert_game_records_valid(self, mock_schema_dir):
        """Test assert_game_records_valid raises on invalid data."""
        df = pd.DataFrame({"game_id": ["g1"]}) # Missing required columns
        with pytest.raises(AssertionError):
            assert_game_records_valid(df)
