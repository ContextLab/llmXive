"""
Unit tests for the validation logic in code/validation/run_validation.py.

These tests verify:
1. That the rater count validation logic correctly identifies insufficient raters.
2. That the column validation logic correctly identifies missing columns.
3. That the main validation function handles file not found errors.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the functions to test
from code.validation.run_validation import validate_rater_count, validate_columns, run_validation

class TestRaterCountValidation:
    """Tests for the validate_rater_count function."""

    def test_passes_with_enough_raters(self):
        """Test that validation passes when >= 3 distinct raters are present."""
        df = pd.DataFrame({
            'rater_id': ['r1', 'r2', 'r3', 'r1', 'r2'],
            'comment_id': [1, 2, 3, 4, 5],
            'prosocial_action': [1, 0, 1, 0, 1],
            'neg_sentiment': [0.1, 0.5, 0.2, 0.8, 0.1]
        })
        assert validate_rater_count(df) is True

    def test_fails_with_insufficient_raters(self):
        """Test that validation fails when < 3 distinct raters are present."""
        df = pd.DataFrame({
            'rater_id': ['r1', 'r1', 'r2', 'r1', 'r2'],
            'comment_id': [1, 2, 3, 4, 5],
            'prosocial_action': [1, 0, 1, 0, 1],
            'neg_sentiment': [0.1, 0.5, 0.2, 0.8, 0.1]
        })
        assert validate_rater_count(df) is False

    def test_fails_with_single_rater(self):
        """Test that validation fails when only 1 rater is present."""
        df = pd.DataFrame({
            'rater_id': ['r1', 'r1', 'r1', 'r1', 'r1'],
            'comment_id': [1, 2, 3, 4, 5],
            'prosocial_action': [1, 0, 1, 0, 1],
            'neg_sentiment': [0.1, 0.5, 0.2, 0.8, 0.1]
        })
        assert validate_rater_count(df) is False

class TestColumnValidation:
    """Tests for the validate_columns function."""

    def test_passes_with_all_columns(self):
        """Test that validation passes when all required columns are present."""
        df = pd.DataFrame({
            'comment_id': [1, 2, 3],
            'rater_id': ['r1', 'r2', 'r3'],
            'prosocial_action': [1, 0, 1],
            'neg_sentiment': [0.1, 0.5, 0.2]
        })
        assert validate_columns(df) is True

    def test_fails_with_missing_column(self):
        """Test that validation fails when a required column is missing."""
        df = pd.DataFrame({
            'comment_id': [1, 2, 3],
            'rater_id': ['r1', 'r2', 'r3'],
            'prosocial_action': [1, 0, 1]
            # Missing 'neg_sentiment'
        })
        assert validate_columns(df) is False

    def test_fails_with_multiple_missing_columns(self):
        """Test that validation fails when multiple required columns are missing."""
        df = pd.DataFrame({
            'comment_id': [1, 2, 3],
            'rater_id': ['r1', 'r2', 'r3']
            # Missing 'prosocial_action' and 'neg_sentiment'
        })
        assert validate_columns(df) is False

class TestRunValidation:
    """Tests for the run_validation function."""

    def test_fails_on_file_not_found(self):
        """Test that run_validation returns False when the file does not exist."""
        fake_path = Path('/tmp/this_file_does_not_exist_12345.csv')
        assert run_validation(fake_path) is False

    def test_passes_on_valid_file(self):
        """Test that run_validation returns True for a valid gold standard file."""
        # Create a temporary valid CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("comment_id,rater_id,prosocial_action,neg_sentiment\n")
            f.write("1,r1,1,0.1\n")
            f.write("2,r2,0,0.5\n")
            f.write("3,r3,1,0.2\n")
            temp_path = f.name
        
        try:
            result = run_validation(Path(temp_path))
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_fails_on_invalid_rater_count(self):
        """Test that run_validation returns False if rater count is insufficient."""
        # Create a temporary invalid CSV (only 2 raters)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("comment_id,rater_id,prosocial_action,neg_sentiment\n")
            f.write("1,r1,1,0.1\n")
            f.write("2,r1,0,0.5\n")
            f.write("3,r2,1,0.2\n")
            temp_path = f.name
        
        try:
            result = run_validation(Path(temp_path))
            assert result is False
        finally:
            os.unlink(temp_path)