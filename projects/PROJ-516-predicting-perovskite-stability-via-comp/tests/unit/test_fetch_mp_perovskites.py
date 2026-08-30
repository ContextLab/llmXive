"""
Unit tests for Materials Project data fetching (Task T012b).
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from fetch_mp_perovskites import (
    fetch_mp_material_data,
    validate_data_checksum,
    PEROVSKITE_SPACE_GROUPS
)


class TestFetchMpPerovskites:
    """Tests for Materials Project data fetching functionality."""

    @patch('fetch_mp_perovskites.get_api_key')
    @patch('fetch_mp_perovskites.create_retry_session')
    def test_fetch_with_valid_api_key(self, mock_session, mock_get_key):
        """Test fetching data with a valid API key."""
        # Setup mocks
        mock_get_key.return_value = "test_api_key_123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "materials_id": "mp-12345",
                    "formula_pretty": "CsPbI3",
                    "nsites": 5,
                    "symmetry": {"space_group_number": 221},
                    "task_ids": ["mp-12345-task1"]
                }
            ]
        }
        mock_session.return_value.get.return_value = mock_response

        # Execute
        result = fetch_mp_material_data()

        # Assert
        assert len(result) == 1
        assert result[0]["formula"] == "CsPbI3"
        assert result[0]["space_group"] == 221
        assert result[0]["source"] == "Materials Project"
        mock_get_key.assert_called_once_with("MATERIALS_PROJECT_API_KEY")

    @patch('fetch_mp_perovskites.get_api_key')
    def test_fetch_raises_on_missing_api_key(self, mock_get_key):
        """Test that fetching raises an error when API key is missing."""
        mock_get_key.return_value = None

        with pytest.raises(RuntimeError, match="Materials Project API key not found"):
            fetch_mp_material_data()

    @patch('fetch_mp_perovskites.get_api_key')
    @patch('fetch_mp_perovskites.create_retry_session')
    def test_filter_non_perovskite_space_groups(self, mock_session, mock_get_key):
        """Test that non-perovskite space groups are filtered out."""
        mock_get_key.return_value = "test_key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "materials_id": "mp-1",
                    "formula_pretty": "CsPbI3",
                    "nsites": 5,
                    "symmetry": {"space_group_number": 221},  # Perovskite
                    "task_ids": []
                },
                {
                    "materials_id": "mp-2",
                    "formula_pretty": "NonPerovskite",
                    "nsites": 10,
                    "symmetry": {"space_group_number": 123},  # Not perovskite
                    "task_ids": []
                }
            ]
        }
        mock_session.return_value.get.return_value = mock_response

        result = fetch_mp_material_data()

        assert len(result) == 1
        assert result[0]["materials_id"] == "mp-1"

    @patch('fetch_mp_perovskites.get_api_key')
    @patch('fetch_mp_perovskites.create_retry_session')
    def test_handles_api_error(self, mock_session, mock_get_key):
        """Test handling of API errors."""
        from fetch_mp_perovskites import FetchError

        mock_get_key.return_value = "test_key"
        mock_session.return_value.get.side_effect = Exception("API Error")

        with pytest.raises(FetchError, match="Materials Project API request failed"):
            fetch_mp_material_data()

    def test_perovskite_space_groups_defined(self):
        """Test that perovskite space groups are properly defined."""
        assert 221 in PEROVSKITE_SPACE_GROUPS  # Pm-3m
        assert 123 not in PEROVSKITE_SPACE_GROUPS  # Non-perovskite

    @patch('fetch_mp_perovskites.verify_single_artifact')
    def test_validate_checksum_success(self, mock_verify):
        """Test successful checksum validation."""
        mock_verify.return_value = "abc123checksum"

        test_data = [
            {"materials_id": "mp-1", "formula": "CsPbI3", "T_d": None}
        ]
        output_path = Path("data/raw/test_mp.csv")

        # Create a temporary file for the test
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(test_data)
        df.to_csv(output_path)

        result = validate_data_checksum(test_data, output_path)

        assert result is True
        assert output_path.exists()
        output_path.unlink()  # Cleanup

    def test_validate_checksum_empty_data(self):
        """Test checksum validation with empty data."""
        result = validate_data_checksum([], Path("data/raw/test_empty.csv"))
        assert result is False
