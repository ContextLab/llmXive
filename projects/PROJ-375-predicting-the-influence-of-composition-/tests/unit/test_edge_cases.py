"""
Unit tests for edge cases in data ingestion and feature extraction.
Tests empty API responses, malformed formulas, and malformed JSON handling.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from features.descriptors import parse_formula
from ingestion.fetch_data import fetch_materials_project_data, fetch_aflow_data


class TestEmptyFormula:
    """Tests for handling empty or invalid composition formulas."""

    def test_empty_formula(self):
        """Verify that an empty string formula raises a ValueError."""
        with pytest.raises(ValueError, match="Empty formula"):
            parse_formula("")

    def test_whitespace_only_formula(self):
        """Verify that a whitespace-only formula raises a ValueError."""
        with pytest.raises(ValueError, match="Empty formula"):
            parse_formula("   ")

    def test_null_formula(self):
        """Verify that a None formula raises a TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            parse_formula(None)

    def test_invalid_characters_formula(self):
        """Verify that a formula with invalid characters raises a ValueError."""
        # Formulas should only contain element symbols and numbers
        with pytest.raises(ValueError, match="Invalid character"):
            parse_formula("Zr@50Cu40")

    def test_negative_coefficient_formula(self):
        """Verify that a formula with negative coefficients raises a ValueError."""
        with pytest.raises(ValueError, match="Negative coefficient"):
            parse_formula("Zr-50Cu40Al10")


class TestMalformedJson:
    """Tests for handling malformed JSON responses from APIs."""

    @patch('ingestion.fetch_data.requests.get')
    def test_malformed_json_response(self, mock_get):
        """Verify that malformed JSON from API raises a clear error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "{ invalid json }"  # Malformed JSON
        mock_response.json.side_effect = json.JSONDecodeError("Expecting property", "doc", 0)
        mock_get.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            fetch_materials_project_data()

    @patch('ingestion.fetch_data.requests.get')
    def test_empty_json_array_response(self, mock_get):
        """Verify that an empty JSON array is handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        # Should return an empty DataFrame, not raise
        result = fetch_materials_project_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('ingestion.fetch_data.requests.get')
    def test_null_json_response(self, mock_get):
        """Verify that a null JSON response is handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

        # Should return an empty DataFrame, not raise
        result = fetch_materials_project_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('ingestion.fetch_data.requests.get')
    def test_missing_required_fields_json(self, mock_get):
        """Verify that JSON missing required fields raises a clear error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # JSON structure missing 'composition' field
        mock_response.json.return_value = [
            {"properties": {"thermal_expansion": 1.0}}
        ]
        mock_get.return_value = mock_response

        # Should raise KeyError or ValueError when accessing missing fields
        with pytest.raises((KeyError, ValueError, TypeError)):
            fetch_materials_project_data()

    @patch('ingestion.fetch_data.requests.get')
    def test_malformed_nested_json(self, mock_get):
        """Verify that deeply nested malformed JSON is handled."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Nested structure with missing keys
        mock_response.json.return_value = {
            "data": [
                {"composition": "Zr50Cu40Al10"},
                {"properties": {}}  # Missing thermal_expansion
            ]
        }
        mock_get.return_value = mock_response

        # Should handle missing nested fields gracefully or raise clear error
        with pytest.raises((KeyError, TypeError, ValueError)):
            fetch_materials_project_data()


class TestApiErrorResponses:
    """Tests for handling various API error responses."""

    @patch('ingestion.fetch_data.requests.get')
    def test_403_unauthorized(self, mock_get):
        """Verify that 403 errors are handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        # Should log warning and return empty DataFrame
        result = fetch_materials_project_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('ingestion.fetch_data.requests.get')
    def test_404_not_found(self, mock_get):
        """Verify that 404 errors are handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = fetch_materials_project_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('ingestion.fetch_data.requests.get')
    def test_500_server_error(self, mock_get):
        """Verify that 500 errors are handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = fetch_materials_project_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('ingestion.fetch_data.requests.get')
    def test_network_timeout(self, mock_get):
        """Verify that network timeouts are handled gracefully."""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = fetch_materials_project_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('ingestion.fetch_data.requests.get')
    def test_connection_error(self, mock_get):
        """Verify that connection errors are handled gracefully."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = fetch_materials_project_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0