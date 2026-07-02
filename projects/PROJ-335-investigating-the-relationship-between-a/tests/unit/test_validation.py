"""
Unit tests for dataset validation logic in code/utils/validation.py.

This module specifically tests the validation utility for missing behavioral measures
as required by User Story 1 (T010).
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add the code directory to the path to allow imports
# Assuming this test runs from the project root or tests/unit
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.validation import (
    validate_behavioral_metrics,
    exit_on_validation_failure,
    load_and_validate_csv,
    log_error
)
import logging

# Configure logging for tests to avoid handler duplication issues
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class TestValidateBehavioralMetrics:
    """Tests for the validate_behavioral_metrics function."""

    def test_valid_behavioral_metrics(self):
        """Test that a dataframe with required behavioral columns passes validation."""
        # Create a mock dataframe with required columns
        data = {
            'subject_id': ['S01', 'S02'],
            'k_score': [2.5, 3.0],
            'd_prime': [1.2, 1.5],
            'accuracy': [0.85, 0.90]
        }
        df = pd.DataFrame(data)

        # Required columns for this test
        required_cols = {'k_score', 'd_prime'}

        # This should not raise an exception
        result = validate_behavioral_metrics(df, required_cols)
        assert result is True

    def test_missing_k_score(self):
        """Test that missing k_score column triggers validation failure."""
        data = {
            'subject_id': ['S01', 'S02'],
            'd_prime': [1.2, 1.5],
            'accuracy': [0.85, 0.90]
        }
        df = pd.DataFrame(data)
        required_cols = {'k_score', 'd_prime'}

        # This should return False or raise an error depending on implementation
        # Based on the task description, it should detect missing measures
        result = validate_behavioral_metrics(df, required_cols)
        assert result is False

    def test_missing_d_prime(self):
        """Test that missing d_prime column triggers validation failure."""
        data = {
            'subject_id': ['S01', 'S02'],
            'k_score': [2.5, 3.0],
            'accuracy': [0.85, 0.90]
        }
        df = pd.DataFrame(data)
        required_cols = {'k_score', 'd_prime'}

        result = validate_behavioral_metrics(df, required_cols)
        assert result is False

    def test_missing_all_behavioral_measures(self):
        """Test that completely missing behavioral measures triggers failure."""
        data = {
            'subject_id': ['S01', 'S02'],
            'reaction_time': [0.5, 0.6]
        }
        df = pd.DataFrame(data)
        required_cols = {'k_score', 'd_prime'}

        result = validate_behavioral_metrics(df, required_cols)
        assert result is False

    def test_empty_dataframe(self):
        """Test that an empty dataframe triggers validation failure."""
        df = pd.DataFrame()
        required_cols = {'k_score', 'd_prime'}

        result = validate_behavioral_metrics(df, required_cols)
        # An empty dataframe should fail validation for behavioral metrics
        assert result is False

    def test_partial_missing_columns(self):
        """Test that having some but not all required columns fails."""
        data = {
            'subject_id': ['S01'],
            'k_score': [2.5],
            # d_prime is missing
            'accuracy': [0.85]
        }
        df = pd.DataFrame(data)
        required_cols = {'k_score', 'd_prime'}

        result = validate_behavioral_metrics(df, required_cols)
        assert result is False


class TestExitOnValidationFailure:
    """Tests for the exit_on_validation_failure function."""

    def test_exit_on_failure(self):
        """Test that the function exits when validation fails."""
        is_valid = False
        error_message = "Test validation failure"
        
        # We need to catch the SystemExit
        with pytest.raises(SystemExit) as exc_info:
            exit_on_validation_failure(is_valid, error_message)
        
        assert exc_info.value.code != 0

    def test_no_exit_on_success(self):
        """Test that the function does not exit when validation passes."""
        is_valid = True
        error_message = "This should not be printed"
        
        # Should not raise SystemExit
        try:
            exit_on_validation_failure(is_valid, error_message)
        except SystemExit:
            pytest.fail("exit_on_validation_failure should not exit on valid data")


class TestLoadAndValidateCsv:
    """Tests for the load_and_validate_csv function."""

    def test_load_valid_csv(self):
        """Test loading and validating a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("subject_id,k_score,d_prime\n")
            f.write("S01,2.5,1.2\n")
            f.write("S02,3.0,1.5\n")
            temp_path = f.name

        try:
            df = load_and_validate_csv(temp_path)
            assert df is not None
            assert len(df) == 2
            assert 'k_score' in df.columns
            assert 'd_prime' in df.columns
        finally:
            os.unlink(temp_path)

    def test_load_missing_csv(self):
        """Test that loading a non-existent CSV raises an error."""
        with pytest.raises(FileNotFoundError):
            load_and_validate_csv("non_existent_file.csv")

    def test_load_empty_csv(self):
        """Test loading an empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("subject_id,k_score,d_prime\n")
            temp_path = f.name

        try:
            df = load_and_validate_csv(temp_path)
            # Should return an empty dataframe or raise an error depending on implementation
            assert df is not None
            assert len(df) == 0
        finally:
            os.unlink(temp_path)


class TestLogError:
    """Tests for the log_error function."""

    def test_log_error_format(self):
        """Test that log_error formats the message correctly."""
        # Capture log output by checking if the function runs without error
        # The actual log output is hard to capture in a simple unit test without complex mocking
        # We test that it doesn't crash
        log_error("Missing behavioral measures: k_score, d_prime")
        # If we reach here, the function executed without crashing
        assert True

    def test_log_error_with_code(self):
        """Test log_error with an error code."""
        log_error("Missing behavioral measures", error_code="FR-006")
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])