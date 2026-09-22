"""
Unit tests for the validator module.

These tests verify that the schema validation logic correctly identifies
valid and invalid data according to the defined schemas.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.validator import (
    load_schema,
    validate_dataframe_against_schema,
    validate_input_schema,
    validate_output_schema,
    validate_parsed_data
)
from contracts.dataset.schema import DATASET_SCHEMA_PATH
from contracts.output.schema import OUTPUT_SCHEMA_PATH

class TestValidator:
    """Test suite for validator functions."""
    
    @pytest.fixture
    def valid_dataset_df(self):
        """Create a valid DataFrame matching the dataset schema."""
        return pd.DataFrame({
            'discharge_id': [123456, 123457],
            'island_width': [0.05, 0.08],
            'tau_e': [0.12, 0.15],
            'confinement_mode': ['H-mode', 'L-mode'],
            'h98y2': [0.95, 0.78],
            'q_min': [1.2, 1.5],
            'q_max': [3.8, 4.2],
            'resonant_surface_density': [2.5, 3.1],
            'te_profile': [[1.0, 2.0, 3.0], [1.5, 2.5, 3.5]],
            'ne_profile': [[0.5, 1.0, 1.5], [0.6, 1.1, 1.6]]
        })
    
    @pytest.fixture
    def valid_output_df(self):
        """Create a valid DataFrame matching the output schema."""
        return pd.DataFrame({
            'r': [-0.65],
            'p_value': [0.03],
            'ci_lower': [-0.85],
            'ci_upper': [-0.45],
            'power': [0.75],
            'hypothesis_status': ['Supported'],
            'warning_flags': [[]],
            'collinearity_flag': [False]
        })
    
    def test_load_schema_success(self):
        """Test successful loading of a schema file."""
        schema = load_schema(Path("contracts/dataset.schema.yaml"))
        assert 'properties' in schema
        assert 'required' in schema
        assert 'discharge_id' in schema['properties']
    
    def test_load_schema_not_found(self):
        """Test loading a non-existent schema file raises error."""
        with pytest.raises(FileNotFoundError):
            load_schema(Path("contracts/non_existent.yaml"))
    
    def test_validate_dataframe_missing_required_columns(self, valid_dataset_df):
        """Test validation fails when required columns are missing."""
        # Remove a required column
        df_invalid = valid_dataset_df.drop(columns=['discharge_id'])
        
        # Load schema
        from data.validator import load_schema, CONTRACTS_DIR
        schema = load_schema(CONTRACTS_DIR / "dataset.schema.yaml")
        
        is_valid, errors = validate_dataframe_against_schema(
            df_invalid, schema, "dataset.schema.yaml"
        )
        
        assert is_valid is False
        assert any("Missing required columns" in error for error in errors)
    
    def test_validate_dataframe_invalid_enum_value(self, valid_dataset_df):
        """Test validation fails when enum value is invalid."""
        df_invalid = valid_dataset_df.copy()
        df_invalid.loc[0, 'confinement_mode'] = 'Invalid-Mode'
        
        from data.validator import load_schema, CONTRACTS_DIR
        schema = load_schema(CONTRACTS_DIR / "dataset.schema.yaml")
        
        is_valid, errors = validate_dataframe_against_schema(
            df_invalid, schema, "dataset.schema.yaml"
        )
        
        assert is_valid is False
        assert any("invalid values" in error for error in errors)
    
    def test_validate_dataframe_negative_minimum_violation(self, valid_dataset_df):
        """Test validation fails when minimum value constraint is violated."""
        df_invalid = valid_dataset_df.copy()
        df_invalid.loc[0, 'island_width'] = -0.05
        
        from data.validator import load_schema, CONTRACTS_DIR
        schema = load_schema(CONTRACTS_DIR / "dataset.schema.yaml")
        
        is_valid, errors = validate_dataframe_against_schema(
            df_invalid, schema, "dataset.schema.yaml"
        )
        
        assert is_valid is False
        assert any("below minimum" in error for error in errors)
    
    def test_validate_input_schema_success(self, valid_dataset_df):
        """Test successful validation of input dataset."""
        is_valid, errors = validate_input_schema(valid_dataset_df)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_input_schema_failure(self):
        """Test validation fails with invalid input."""
        df_invalid = pd.DataFrame({
            'discharge_id': [123456],
            'island_width': [-0.05],  # Negative value violates minimum
            'tau_e': [0.12],
            'confinement_mode': ['H-mode'],
            'h98y2': [0.95],
            'q_min': [1.2],
            'q_max': [3.8],
            'resonant_surface_density': [2.5],
            'te_profile': [[1.0, 2.0]],
            'ne_profile': [[0.5, 1.0]]
        })
        
        is_valid, errors = validate_input_schema(df_invalid)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_output_schema_success(self, valid_output_df):
        """Test successful validation of output dataset."""
        is_valid, errors = validate_output_schema(valid_output_df)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_parsed_data_success(self, valid_dataset_df):
        """Test validate_parsed_data returns success for valid data."""
        is_valid, errors = validate_parsed_data(valid_dataset_df)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_parsed_data_failure(self):
        """Test validate_parsed_data raises error for invalid data."""
        df_invalid = pd.DataFrame({
            'discharge_id': [123456],
            'island_width': [-0.05],  # Invalid
            'tau_e': [0.12],
            'confinement_mode': ['H-mode'],
            'h98y2': [0.95],
            'q_min': [1.2],
            'q_max': [3.8],
            'resonant_surface_density': [2.5],
            'te_profile': [[1.0, 2.0]],
            'ne_profile': [[0.5, 1.0]]
        })
        
        with pytest.raises(ValueError, match="Schema validation failed"):
            validate_parsed_data(df_invalid)
    
    def test_array_column_validation(self, valid_dataset_df):
        """Test that array columns are validated correctly."""
        df_invalid = valid_dataset_df.copy()
        df_invalid.loc[0, 'te_profile'] = "not an array"
        
        from data.validator import load_schema, CONTRACTS_DIR
        schema = load_schema(CONTRACTS_DIR / "dataset.schema.yaml")
        
        is_valid, errors = validate_dataframe_against_schema(
            df_invalid, schema, "dataset.schema.yaml"
        )
        
        assert is_valid is False
        assert any("should contain array values" in error for error in errors)