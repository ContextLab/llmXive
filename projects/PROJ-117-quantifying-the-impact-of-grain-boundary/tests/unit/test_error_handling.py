"""
Unit tests for error handling infrastructure.

Tests the DataInsufficiencyError exception and related utility functions
for proper behavior when data requirements are not met.
"""

import logging
import sys
import pytest
from unittest.mock import patch, MagicMock

from code.error_handling import (
    DataInsufficiencyError,
    check_data_sufficiency,
    exit_on_insufficiency
)


class TestDataInsufficiencyError:
    """Tests for the DataInsufficiencyError exception class."""
    
    def test_basic_error_initialization(self):
        """Test basic error creation with counts only."""
        error = DataInsufficiencyError(
            retrieved_count=100,
            required_count=500
        )
        assert error.retrieved_count == 100
        assert error.required_count == 500
        assert error.missing_features == []
        assert "Data Insufficiency" in str(error)
        assert "100" in str(error)
        assert "500" in str(error)
    
    def test_error_with_missing_features(self):
        """Test error creation with missing features list."""
        missing = ['boundary plane normal', 'Σ value']
        error = DataInsufficiencyError(
            retrieved_count=250,
            required_count=500,
            missing_features=missing
        )
        assert error.missing_features == missing
        assert "boundary plane normal" in str(error)
        assert "Σ value" in str(error)
    
    def test_custom_message(self):
        """Test that custom messages override default formatting."""
        custom_msg = "Custom error message for testing"
        error = DataInsufficiencyError(
            retrieved_count=10,
            required_count=100,
            message=custom_msg
        )
        assert str(error) == custom_msg
    
    def test_error_is_exception(self):
        """Test that DataInsufficiencyError is a subclass of Exception."""
        assert issubclass(DataInsufficiencyError, Exception)
    
    def test_error_can_be_raised(self):
        """Test that the error can be raised and caught."""
        with pytest.raises(DataInsufficiencyError) as exc_info:
            raise DataInsufficiencyError(
                retrieved_count=50,
                required_count=200
            )
        assert exc_info.value.retrieved_count == 50
        assert exc_info.value.required_count == 200


class TestCheckDataSufficiency:
    """Tests for the check_data_sufficiency function."""
    
    def test_sufficient_data(self):
        """Test when data count meets requirement."""
        assert check_data_sufficiency(500, 500) is True
        assert check_data_sufficiency(1000, 500) is True
    
    def test_insufficient_data(self):
        """Test when data count is below requirement."""
        assert check_data_sufficiency(499, 500) is False
        assert check_data_sufficiency(100, 500) is False
    
    def test_exact_match(self):
        """Test when data count exactly matches requirement."""
        assert check_data_sufficiency(500, 500) is True
    
    def test_missing_features_parameter(self):
        """Test that missing_features parameter doesn't affect boolean result."""
        missing = ['feature1', 'feature2']
        assert check_data_sufficiency(500, 500, missing) is True
        assert check_data_sufficiency(499, 500, missing) is False


class TestExitOnInsufficiency:
    """Tests for the exit_on_insufficiency function."""
    
    def test_exits_with_code_one(self):
        """Test that the function exits with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            exit_on_insufficiency(100, 500)
        assert exc_info.value.code == 1
    
    def test_logs_error_message(self, caplog):
        """Test that the function logs the error message."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit):
                exit_on_insufficiency(100, 500)
        
        assert "Data Insufficiency" in caplog.text
        assert "100" in caplog.text
        assert "500" in caplog.text
    
    def test_logs_missing_features(self, caplog):
        """Test that missing features are logged when provided."""
        missing = ['boundary plane normal', 'Σ value']
        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit):
                exit_on_insufficiency(250, 500, missing)
        
        assert "boundary plane normal" in caplog.text
        assert "Σ value" in caplog.text
    
    def test_uses_custom_logger(self):
        """Test that a custom logger can be provided."""
        mock_logger = MagicMock()
        mock_logger.error = MagicMock()
        
        with pytest.raises(SystemExit):
            exit_on_insufficiency(100, 500, logger_instance=mock_logger)
        
        mock_logger.error.assert_called_once()
        assert "Data Insufficiency" in mock_logger.error.call_args[0][0]
    
    def test_integration_with_check_data_sufficiency(self):
        """Test integration: exit only called when check fails."""
        # Sufficient data - should not exit
        assert check_data_sufficiency(600, 500)
        
        # Insufficient data - would exit if called
        with pytest.raises(SystemExit):
            if not check_data_sufficiency(400, 500):
                exit_on_insufficiency(400, 500)