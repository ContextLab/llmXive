"""
Contract tests for validate_contracts module.
"""
import pytest
import pandas as pd
from src.validation.validate_contracts import (
    validate_contract,
    validate_game_record,
    validate_model_output,
    ContractValidationError
)
from src.config import get_contract_path


@pytest.fixture
def valid_game_record_df():
    """Create a valid game_record DataFrame for testing."""
    return pd.DataFrame({
        'game_id': ['g1', 'g2', 'g3'],
        'white_rating': [1500, 1600, 1700],
        'black_rating': [1450, 1550, 1650],
        'eco_code': ['B01', 'C45', 'E20'],
        'avg_move_time_white': [10.5, 12.3, 8.9],
        'avg_move_time_black': [11.2, 10.1, 9.5],
        'material_imbalance_move5': [0.0, 1.0, -0.5],
        'outcome': ['1-0', '0-1', '1/2-1/2'],
        'elo_expected_prob': [0.56, 0.44, 0.58],
        'outcome_deviation': [0.44, -0.44, -0.08]
    })


@pytest.fixture
def invalid_game_record_missing_col():
    """Create a game_record DataFrame missing a required column."""
    return pd.DataFrame({
        'game_id': ['g1', 'g2'],
        'white_rating': [1500, 1600],
        # Missing: black_rating, eco_code, etc.
    })


@pytest.fixture
def invalid_game_record_null_values():
    """Create a game_record DataFrame with null values in not-nullable columns."""
    return pd.DataFrame({
        'game_id': ['g1', None, 'g3'],
        'white_rating': [1500, 1600, 1700],
        'black_rating': [1450, 1550, 1650],
        'eco_code': ['B01', 'C45', 'E20'],
        'avg_move_time_white': [10.5, 12.3, 8.9],
        'avg_move_time_black': [11.2, 10.1, 9.5],
        'material_imbalance_move5': [0.0, 1.0, -0.5],
        'outcome': ['1-0', '0-1', '1/2-1/2'],
        'elo_expected_prob': [0.56, 0.44, 0.58],
        'outcome_deviation': [0.44, -0.44, -0.08]
    })


@pytest.fixture
def valid_model_output_df():
    """Create a valid model_output DataFrame for testing."""
    return pd.DataFrame({
        'model_type': ['GaussianGLM', 'Ridge'],
        'coefficients': ['{a: 0.5, b: -0.3}', '{a: 0.45, b: -0.35}'],
        'p_values': ['{a: 0.01, b: 0.05}', '{a: 0.02, b: 0.04}'],
        'r_squared': [0.75, 0.72],
        'aic': [150.5, 152.3],
        'cross_validation_scores': ['[0.71, 0.73, 0.74, 0.72, 0.70]', '[0.70, 0.72, 0.73, 0.71, 0.69]']
    })


class TestValidateContracts:
    def test_valid_game_record_passes(self, valid_game_record_df):
        """Test that a valid game_record DataFrame passes validation."""
        result = validate_game_record(valid_game_record_df)
        assert result is True

    def test_invalid_game_record_missing_column(self, invalid_game_record_missing_col):
        """Test that a DataFrame missing required columns raises an error."""
        with pytest.raises(ContractValidationError) as exc_info:
            validate_game_record(invalid_game_record_missing_col)
        assert "Missing required columns" in str(exc_info.value)

    def test_invalid_game_record_null_values(self, invalid_game_record_null_values):
        """Test that a DataFrame with null values in not-nullable columns raises an error."""
        with pytest.raises(ContractValidationError) as exc_info:
            validate_game_record(invalid_game_record_null_values)
        assert "Null values in not-nullable columns" in str(exc_info.value)

    def test_valid_model_output_passes(self, valid_model_output_df):
        """Test that a valid model_output DataFrame passes validation."""
        result = validate_model_output(valid_model_output_df)
        assert result is True

    def test_validate_contract_with_explicit_path(self, valid_game_record_df):
        """Test validate_contract with an explicit schema path."""
        schema_path = get_contract_path('game_record')
        result = validate_contract(valid_game_record_df, schema_path=schema_path)
        assert result is True

    def test_validate_contract_missing_schema_name(self, valid_game_record_df):
        """Test validate_contract raises error when neither name nor path provided."""
        with pytest.raises(ValueError) as exc_info:
            validate_contract(valid_game_record_df)
        assert "Either schema_name or schema_path must be provided" in str(exc_info.value)

    def test_validate_contract_nonexistent_schema(self, valid_game_record_df):
        """Test validate_contract raises error for nonexistent schema."""
        with pytest.raises(ContractValidationError) as exc_info:
            validate_contract(valid_game_record_df, schema_name='nonexistent_schema')
        assert "Schema not found" in str(exc_info.value)
