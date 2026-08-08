"""
Unit tests for the validate_dataset_schema module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Import the module under test
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.validate_dataset_schema import (
    DataInvalidError,
    validate_dataset_schema,
    validate_columns,
    validate_roi_definitions,
    get_required_columns,
    get_required_roi_definitions,
    write_validation_result
)


class TestValidateColumns:
    """Tests for the validate_columns function."""

    def test_all_columns_present(self):
        """Test when all required columns are present."""
        df = pd.DataFrame({
            'headline_text': ['test'],
            'belief_rating': [1],
            'cognitive_reflection_score': [1],
            'fixation_duration': [1]
        })
        required = get_required_columns()
        missing = validate_columns(df, required)
        assert missing == []

    def test_some_columns_missing(self):
        """Test when some required columns are missing."""
        df = pd.DataFrame({
            'headline_text': ['test'],
            'belief_rating': [1]
        })
        required = get_required_columns()
        missing = validate_columns(df, required)
        assert 'cognitive_reflection_score' in missing
        assert 'fixation_duration' in missing

    def test_no_columns_present(self):
        """Test when no required columns are present."""
        df = pd.DataFrame({
            'other_column': ['test']
        })
        required = get_required_columns()
        missing = validate_columns(df, required)
        assert len(missing) == 4


class TestValidateRoiDefinitions:
    """Tests for the validate_roi_definitions function."""

    def test_roi_type_column_with_all_rois(self):
        """Test when roi_type column contains all required ROIs."""
        df = pd.DataFrame({
            'roi_type': ['source_attribution', 'headline_body', 'other']
        })
        required = get_required_roi_definitions()
        missing = validate_roi_definitions(df, required)
        assert missing == []

    def test_roi_type_column_missing_some_rois(self):
        """Test when roi_type column is missing some required ROIs."""
        df = pd.DataFrame({
            'roi_type': ['source_attribution', 'other']
        })
        required = get_required_roi_definitions()
        missing = validate_roi_definitions(df, required)
        assert 'headline_body' in missing

    def test_roi_config_column_with_all_rois(self):
        """Test when roi_config column contains all required ROIs."""
        df = pd.DataFrame({
            'roi_config': [json.dumps({'rois': {
                'source_attribution': {'x': 0, 'y': 0},
                'headline_body': {'x': 10, 'y': 10}
            }})]
        })
        required = get_required_roi_definitions()
        missing = validate_roi_definitions(df, required)
        assert missing == []

    def test_roi_config_column_missing_some_rois(self):
        """Test when roi_config column is missing some required ROIs."""
        df = pd.DataFrame({
            'roi_config': [json.dumps({'rois': {
                'source_attribution': {'x': 0, 'y': 0}
            }})]
        })
        required = get_required_roi_definitions()
        missing = validate_roi_definitions(df, required)
        assert 'headline_body' in missing

    def test_no_roi_columns(self):
        """Test when no ROI configuration columns exist."""
        df = pd.DataFrame({
            'other_column': ['test']
        })
        required = get_required_roi_definitions()
        missing = validate_roi_definitions(df, required)
        assert len(missing) == 2


class TestValidateDatasetSchema:
    """Tests for the validate_dataset_schema function."""

    def test_valid_schema(self, tmp_path):
        """Test validation with a valid schema."""
        # Create a temporary parquet file with valid schema
        df = pd.DataFrame({
            'headline_text': ['test'],
            'belief_rating': [1],
            'cognitive_reflection_score': [1],
            'fixation_duration': [1],
            'roi_type': ['source_attribution', 'headline_body']
        })
        input_path = tmp_path / 'test.parquet'
        df.to_parquet(input_path)

        result = validate_dataset_schema(input_path)
        assert result['status'] == 'valid'
        assert result['missing_columns'] == []
        assert result['missing_rois'] == []

    def test_invalid_schema_missing_columns(self, tmp_path):
        """Test validation with missing columns."""
        df = pd.DataFrame({
            'headline_text': ['test'],
            'belief_rating': [1]
        })
        input_path = tmp_path / 'test.parquet'
        df.to_parquet(input_path)

        with pytest.raises(DataInvalidError) as exc_info:
            validate_dataset_schema(input_path)

        assert 'Missing columns' in str(exc_info.value)

    def test_invalid_schema_missing_rois(self, tmp_path):
        """Test validation with missing ROIs."""
        df = pd.DataFrame({
            'headline_text': ['test'],
            'belief_rating': [1],
            'cognitive_reflection_score': [1],
            'fixation_duration': [1],
            'roi_type': ['other']
        })
        input_path = tmp_path / 'test.parquet'
        df.to_parquet(input_path)

        with pytest.raises(DataInvalidError) as exc_info:
            validate_dataset_schema(input_path)

        assert 'Missing ROIs' in str(exc_info.value)

    def test_file_not_found(self, tmp_path):
        """Test validation when input file does not exist."""
        input_path = tmp_path / 'nonexistent.parquet'

        with pytest.raises(FileNotFoundError):
            validate_dataset_schema(input_path)


class TestWriteValidationResult:
    """Tests for the write_validation_result function."""

    def test_write_result(self, tmp_path):
        """Test writing a validation result to a file."""
        result = {
            'status': 'valid',
            'missing_columns': [],
            'missing_rois': [],
            'message': 'Validation passed'
        }
        output_path = tmp_path / 'result.json'

        write_validation_result(result, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            written_result = json.load(f)

        assert written_result == result