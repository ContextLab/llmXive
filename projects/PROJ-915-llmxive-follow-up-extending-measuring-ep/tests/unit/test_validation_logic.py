"""
Unit tests for T015 validation logic.
Tests for flagging prompts with undefined imperative ratio.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from validation_logic import (
    flag_undefined_imperative_ratio,
    validate_features_for_imperative_ratio,
    run_t015_validation_pipeline
)

class TestFlagUndefinedImperativeRatio:
    """Tests for flag_undefined_imperative_ratio function."""

    def test_flag_undefined_ratio_with_zero_sentences(self):
        """Test that prompts with zero total sentences are flagged."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2', 'p3'],
            'imperative_count': [1, 0, 2],
            'total_sentences': [0, 5, 3]
        })

        result = flag_undefined_imperative_ratio(df)

        assert 'undefined_imperative_ratio' in result.columns
        assert result.loc[0, 'undefined_imperative_ratio'] is True  # p1 has 0 sentences
        assert result.loc[1, 'undefined_imperative_ratio'] is False  # p2 has 5 sentences
        assert result.loc[2, 'undefined_imperative_ratio'] is False  # p3 has 3 sentences

    def test_flag_undefined_ratio_with_all_zero_sentences(self):
        """Test that all prompts are flagged when all have zero sentences."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2'],
            'imperative_count': [0, 1],
            'total_sentences': [0, 0]
        })

        result = flag_undefined_imperative_ratio(df)

        assert result['undefined_imperative_ratio'].all()

    def test_flag_undefined_ratio_with_no_zero_sentences(self):
        """Test that no prompts are flagged when all have non-zero sentences."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2', 'p3'],
            'imperative_count': [1, 0, 2],
            'total_sentences': [5, 3, 10]
        })

        result = flag_undefined_imperative_ratio(df)

        assert not result['undefined_imperative_ratio'].any()

    def test_flag_undefined_ratio_with_empty_dataframe(self):
        """Test that empty dataframe is handled correctly."""
        df = pd.DataFrame(columns=['prompt_id', 'imperative_count', 'total_sentences'])

        result = flag_undefined_imperative_ratio(df)

        assert 'undefined_imperative_ratio' in result.columns
        assert len(result) == 0
        assert result['undefined_imperative_ratio'].sum() == 0

    def test_flag_undefined_ratio_missing_columns(self):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2'],
            'imperative_count': [1, 0]
            # Missing 'total_sentences'
        })

        with pytest.raises(ValueError) as exc_info:
            flag_undefined_imperative_ratio(df)

        assert 'total_sentences' in str(exc_info.value)

    def test_flag_undefined_ratio_with_float_sentences(self):
        """Test handling of float sentence counts (should work if they represent valid counts)."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2'],
            'imperative_count': [1, 0],
            'total_sentences': [0.0, 5.0]
        })

        result = flag_undefined_imperative_ratio(df)

        assert result.loc[0, 'undefined_imperative_ratio'] is True
        assert result.loc[1, 'undefined_imperative_ratio'] is False


class TestValidateFeaturesForImperativeRatio:
    """Tests for validate_features_for_imperative_ratio function."""

    def test_validate_no_issues(self):
        """Test validation with no issues."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2', 'p3'],
            'imperative_count': [1, 0, 2],
            'total_sentences': [5, 3, 10]
        })

        is_valid, issues = validate_features_for_imperative_ratio(df)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_with_zero_sentences(self):
        """Test validation with zero total sentences (warning, not failure)."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2'],
            'imperative_count': [1, 0],
            'total_sentences': [0, 5]
        })

        is_valid, issues = validate_features_for_imperative_ratio(df)

        assert is_valid is True  # Still valid, just flagged
        assert len(issues) == 1
        assert issues[0]['issue_type'] == 'undefined_imperative_ratio'
        assert issues[0]['severity'] == 'warning'
        assert issues[0]['count'] == 1

    def test_validate_with_negative_sentences(self):
        """Test validation with negative sentence counts (critical failure)."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2'],
            'imperative_count': [1, 0],
            'total_sentences': [-1, 5]
        })

        is_valid, issues = validate_features_for_imperative_ratio(df)

        assert is_valid is False
        assert len(issues) == 1
        assert issues[0]['issue_type'] == 'negative_sentence_count'
        assert issues[0]['severity'] == 'critical'

    def test_validate_with_missing_columns(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2'],
            'imperative_count': [1, 0]
            # Missing 'total_sentences'
        })

        is_valid, issues = validate_features_for_imperative_ratio(df)

        assert is_valid is False
        assert len(issues) == 1
        assert issues[0]['issue_type'] == 'missing_columns'
        assert issues[0]['severity'] == 'critical'

    def test_validate_with_empty_dataframe(self):
        """Test validation with empty dataframe."""
        df = pd.DataFrame(columns=['prompt_id', 'imperative_count', 'total_sentences'])

        is_valid, issues = validate_features_for_imperative_ratio(df)

        assert is_valid is False
        assert len(issues) == 1
        assert issues[0]['issue_type'] == 'empty_dataframe'

    def test_validate_with_non_integer_sentences(self):
        """Test validation with non-integer sentence counts (warning)."""
        df = pd.DataFrame({
            'prompt_id': ['p1', 'p2'],
            'imperative_count': [1, 0],
            'total_sentences': [5.5, 3]
        })

        is_valid, issues = validate_features_for_imperative_ratio(df)

        assert is_valid is True
        assert len(issues) == 1
        assert issues[0]['issue_type'] == 'non_integer_sentence_count'
        assert issues[0]['severity'] == 'warning'


class TestRunT015ValidationPipeline:
    """Tests for run_t015_validation_pipeline function."""

    def test_run_pipeline_with_mock_config(self, tmp_path):
        """Test running the full pipeline with a mock configuration."""
        # Create mock directories
        processed_dir = tmp_path / 'data' / 'processed'
        processed_dir.mkdir(parents=True)
        reports_dir = tmp_path / 'data' / 'results'
        reports_dir.mkdir(parents=True)

        # Create mock feature data
        features_file = processed_dir / 'features.csv'
        mock_data = pd.DataFrame({
            'prompt_id': ['p1', 'p2', 'p3', 'p4'],
            'imperative_count': [1, 0, 2, 0],
            'total_sentences': [0, 5, 0, 10],
            'other_feature': [10, 20, 30, 40]
        })
        mock_data.to_csv(features_file, index=False)

        # Mock config
        config = {
            'paths': {
                'processed_features': str(features_file),
                'validation_reports': str(reports_dir)
            }
        }

        # Run pipeline
        result = run_t015_validation_pipeline(config)

        assert result['success'] is True
        assert result['undefined_imperative_ratio_count'] == 2
        assert 'report_path' in result
        assert Path(result['report_path']).exists()

    def test_run_pipeline_with_missing_file(self, tmp_path):
        """Test running the pipeline with a missing feature file."""
        reports_dir = tmp_path / 'data' / 'results'
        reports_dir.mkdir(parents=True)

        config = {
            'paths': {
                'processed_features': str(tmp_path / 'nonexistent.csv'),
                'validation_reports': str(reports_dir)
            }
        }

        result = run_t015_validation_pipeline(config)

        assert result['success'] is False
        assert 'error' in result
        assert 'nonexistent.csv' in result['error']