"""
Unit tests for the Validation Gate (T036).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.dataset.validation_gate import load_json, save_json, validate_distribution, main

class TestValidationGate:
    """Tests for the validation gate logic."""

    def test_load_json_valid(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = {"key": "value"}
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        result = load_json(file_path)
        assert result == test_data

    def test_load_json_missing_file(self, tmp_path):
        """Test loading a missing JSON file returns None."""
        file_path = tmp_path / "missing.json"
        result = load_json(file_path)
        assert result is None

    def test_validate_distribution_pass(self):
        """Test validation passes with valid data."""
        data = {
            "is_valid": True,
            "power_estimate": 0.9,
            "notes": "All checks passed."
        }
        is_valid, message = validate_distribution(data)
        assert is_valid is True
        assert "passed" in message.lower()

    def test_validate_distribution_fail_invalid(self):
        """Test validation fails when is_valid is False."""
        data = {
            "is_valid": False,
            "power_estimate": 0.9,
            "notes": "Distribution mismatch."
        }
        is_valid, message = validate_distribution(data)
        assert is_valid is False
        assert "is_valid is False" in message

    def test_validate_distribution_fail_low_power(self):
        """Test validation fails when power is critically low."""
        data = {
            "is_valid": True,
            "power_estimate": 0.05,
            "notes": "Low power."
        }
        is_valid, message = validate_distribution(data)
        assert is_valid is False
        assert "critically low" in message.lower()

    def test_validate_distribution_fail_critical_notes(self):
        """Test validation fails if notes contain critical keywords."""
        data = {
            "is_valid": True,
            "power_estimate": 0.9,
            "notes": "Error in scaling logic."
        }
        is_valid, message = validate_distribution(data)
        assert is_valid is False
        assert "notes" in message.lower()

    def test_validate_distribution_warning_power(self):
        """Test validation passes with warning if power is between 0.1 and 0.8."""
        data = {
            "is_valid": True,
            "power_estimate": 0.5,
            "notes": "Moderate power."
        }
        is_valid, message = validate_distribution(data)
        assert is_valid is True
        assert "Warning" in message

    @patch('code.dataset.validation_gate.load_json')
    @patch('code.dataset.validation_gate.save_json')
    @patch('code.dataset.validation_gate.sys.exit')
    def test_main_missing_input(self, mock_exit, mock_save, mock_load):
        """Test main exits with error when input file is missing."""
        mock_load.return_value = None
        
        # Run main
        try:
            main()
        except SystemExit:
            pass
        
        mock_load.assert_called_once()
        mock_save.assert_called_once()
        mock_exit.assert_called_with(1)

    @patch('code.dataset.validation_gate.load_json')
    @patch('code.dataset.validation_gate.save_json')
    @patch('code.dataset.validation_gate.sys.exit')
    def test_main_pass(self, mock_exit, mock_save, mock_load):
        """Test main exits with 0 when validation passes."""
        mock_load.return_value = {
            "is_valid": True,
            "power_estimate": 0.9,
            "notes": "OK"
        }
        
        try:
            main()
        except SystemExit:
            pass
        
        mock_exit.assert_called_with(0)

    @patch('code.dataset.validation_gate.load_json')
    @patch('code.dataset.validation_gate.save_json')
    @patch('code.dataset.validation_gate.sys.exit')
    def test_main_fail(self, mock_exit, mock_save, mock_load):
        """Test main exits with 1 when validation fails."""
        mock_load.return_value = {
            "is_valid": False,
            "power_estimate": 0.9,
            "notes": "Failed"
        }
        
        try:
            main()
        except SystemExit:
            pass
        
        mock_exit.assert_called_with(1)