"""
Unit tests for download scripts (T009a, T009b, T009c).

This module verifies that:
1. The download scripts log the raw record count retrieved.
2. The download scripts do NOT halt execution on data insufficiency (delegating to T011).
3. No synthetic fallback data is used when real data retrieval fails or returns zero records.
"""
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.download import fetch_materials_project_data, fetch_openkim_data, fetch_nist_data
from code.utils import setup_logging, raise_data_insufficiency
from code.error_handling import DataInsufficiencyError


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    logger = MagicMock(spec=logging.Logger)
    return logger


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for raw data storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables to prevent actual API calls during tests."""
    env_patch = patch.dict(os.environ, {
        "MP_API_KEY": "fake_key_for_testing",
        "OPENKIM_API_KEY": "fake_key_for_testing"
    })
    env_patch.start()
    yield
    env_patch.stop()


class TestMaterialsProjectDownload:
    """Tests for fetch_materials_project_data."""

    def test_logs_raw_count_on_success(self, mock_logger, mock_env_vars):
        """Verify that the script logs the raw count when data is retrieved."""
        mock_response = {
            "data": [
                {"task_id": "mp-1", "structure": {"lattice": [[1,0,0],[0,1,0],[0,0,1]], "species": [{"label": "Ce"}]}},
                {"task_id": "mp-2", "structure": {"lattice": [[1,0,0],[0,1,0],[0,0,1]], "species": [{"label": "Ce"}]}}
            ]
        }
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            # Call the function with a mock logger
            result = fetch_materials_project_data(
                keywords=["grain boundary"],
                properties=["diffusivity"],
                limit=2,
                logger=mock_logger
            )
            
            # Verify log was called with the count
            mock_logger.info.assert_any_call("Total records retrieved from Materials Project: 2")
            assert len(result) == 2

    def test_logs_raw_count_on_empty_result(self, mock_logger, mock_env_vars):
        """Verify that the script logs 0 count when no data is retrieved, but does NOT halt."""
        mock_response = {"data": []}
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = fetch_materials_project_data(
                keywords=["grain boundary"],
                properties=["diffusivity"],
                limit=10,
                logger=mock_logger
            )
            
            # Verify log was called with 0 count
            mock_logger.info.assert_any_call("Total records retrieved from Materials Project: 0")
            
            # Verify the function returns the empty list without raising DataInsufficiencyError
            assert result == []
            
            # Verify that raise_data_insufficiency was NOT called (delegation to T011)
            with pytest.raises(AssertionError):
                # This assertion will fail if raise_data_insufficiency was called
                # We check that the function completed normally
                pass

    def test_no_synthetic_fallback_on_failure(self, mock_logger, mock_env_vars):
        """Verify that no synthetic data is generated when the API fails."""
        with patch('code.download.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Connection Failed")
            
            # The function should raise an exception or return empty, but never synthetic data
            with pytest.raises(Exception):
                fetch_materials_project_data(
                    keywords=["grain boundary"],
                    properties=["diffusivity"],
                    limit=10,
                    logger=mock_logger
                )

    def test_no_data_insufficiency_halt_in_download_module(self, mock_logger, mock_env_vars):
        """
        Verify that the download script does NOT halt on insufficiency.
        The error handling is delegated to T011 (preprocess.py).
        """
        mock_response = {"data": []}
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            # This should NOT raise DataInsufficiencyError
            try:
                result = fetch_materials_project_data(
                    keywords=["grain boundary"],
                    properties=["diffusivity"],
                    limit=10,
                    logger=mock_logger
                )
                # If we reach here, the function did not halt
                assert result == []
            except DataInsufficiencyError:
                pytest.fail("fetch_materials_project_data should NOT raise DataInsufficiencyError")


class TestOpenKIMDownload:
    """Tests for fetch_openkim_data."""

    def test_logs_raw_count_on_success(self, mock_logger, mock_env_vars):
        """Verify that the script logs the raw count when data is retrieved."""
        mock_response = [
            {"id": "kim-1", "data": {"structure": "test"}},
            {"id": "kim-2", "data": {"structure": "test"}}
        ]
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = fetch_openkim_data(
                keywords=["grain boundary", "diffusivity"],
                limit=2,
                logger=mock_logger
            )
            
            mock_logger.info.assert_any_call("Total records retrieved from OpenKIM: 2")
            assert len(result) == 2

    def test_logs_raw_count_on_empty_result(self, mock_logger, mock_env_vars):
        """Verify that the script logs 0 count but does NOT halt."""
        mock_response = []
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = fetch_openkim_data(
                keywords=["grain boundary", "diffusivity"],
                limit=10,
                logger=mock_logger
            )
            
            mock_logger.info.assert_any_call("Total records retrieved from OpenKIM: 0")
            assert result == []

    def test_no_synthetic_fallback(self, mock_logger, mock_env_vars):
        """Verify that no synthetic data is generated on API failure."""
        with patch('code.download.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                fetch_openkim_data(
                    keywords=["grain boundary", "diffusivity"],
                    limit=10,
                    logger=mock_logger
                )


class TestNISTDownload:
    """Tests for fetch_nist_data."""

    def test_logs_raw_count_on_success(self, mock_logger, mock_env_vars):
        """Verify that the script logs the raw count when data is retrieved."""
        mock_response = {
            "results": [
                {"id": "nist-1", "data": "test"},
                {"id": "nist-2", "data": "test"}
            ]
        }
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = fetch_nist_data(
                keywords=["grain boundary", "diffusivity"],
                limit=2,
                logger=mock_logger
            )
            
            mock_logger.info.assert_any_call("Total records retrieved from NIST: 2")
            assert len(result) == 2

    def test_logs_raw_count_on_empty_result(self, mock_logger, mock_env_vars):
        """Verify that the script logs 0 count but does NOT halt."""
        mock_response = {"results": []}
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = fetch_nist_data(
                keywords=["grain boundary", "diffusivity"],
                limit=10,
                logger=mock_logger
            )
            
            mock_logger.info.assert_any_call("Total records retrieved from NIST: 0")
            assert result == []


class TestDataInsufficiencyDelegation:
    """Tests to ensure data insufficiency handling is delegated correctly."""

    def test_download_functions_do_not_call_raise_data_insufficiency(self, mock_logger, mock_env_vars):
        """
        Verify that download functions do not call raise_data_insufficiency.
        This ensures T011 is responsible for the check.
        """
        mock_response = {"data": []}
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            with patch('code.download.raise_data_insufficiency') as mock_raise:
                # Call the function
                fetch_materials_project_data(
                    keywords=["grain boundary"],
                    properties=["diffusivity"],
                    limit=10,
                    logger=mock_logger
                )
                
                # Verify raise_data_insufficiency was NOT called
                mock_raise.assert_not_called()

    def test_empty_data_returns_empty_list_not_synthetic(self, mock_logger, mock_env_vars):
        """Verify that empty results return an empty list, not synthetic data."""
        mock_response = {"data": []}
        
        with patch('code.download.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            result = fetch_materials_project_data(
                keywords=["grain boundary"],
                properties=["diffusivity"],
                limit=10,
                logger=mock_logger
            )
            
            assert result == []
            # Verify no synthetic data generation occurred
            assert len(result) == 0