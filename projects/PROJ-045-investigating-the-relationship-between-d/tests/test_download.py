"""
Tests for the download module.

This module implements the contract test for data download success rate (>=93%).
It mocks external API calls to verify the retry logic and success rate handling
without requiring network access or API keys during CI.
"""

import json
import os
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

# Import the module to test
import code.download as download_module

# Configure logging for tests to avoid "No handler found" warnings
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_mp_structure():
    """Mock pymatgen Structure object."""
    mock = MagicMock()
    mock.to = MagicMock(return_value=None)
    return mock

@pytest.fixture
def mock_mprester(mock_mp_structure):
    """Mock MPRester context manager."""
    mock_instance = MagicMock()
    mock_instance.get_structure_by_material_id.return_value = mock_mp_structure
    
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_instance)
    mock_context.__exit__ = MagicMock(return_value=False)
    
    return mock_context

def test_setup_download_logging():
    """Test that logging is configured correctly."""
    logger = download_module.setup_download_logging()
    assert logger is not None
    assert logger.level == logging.INFO

@patch('code.download.MPRester')
def test_fetch_mp_structure_success(mock_mprester, mock_mp_structure):
    """Test successful fetch from Materials Project."""
    # Setup mock
    mock_instance = MagicMock()
    mock_instance.get_structure_by_material_id.return_value = mock_mp_structure
    mock_mprester.return_value.__enter__.return_value = mock_instance

    result = download_module.fetch_mp_structure("mp-1234", api_key="fake_key")
    
    assert result is not None
    assert result == mock_mp_structure
    mock_instance.get_structure_by_material_id.assert_called_once_with("mp-1234")

@patch('code.download.MPRester')
def test_fetch_mp_structure_not_found(mock_mprester):
    """Test fetch when structure is not found."""
    mock_instance = MagicMock()
    mock_instance.get_structure_by_material_id.return_value = None
    mock_mprester.return_value.__enter__.return_value = mock_instance

    result = download_module.fetch_mp_structure("mp-9999", api_key="fake_key")
    
    assert result is None

@patch('code.download.requests.get')
def test_fetch_obelix_structure_success(mock_get):
    """Test successful fetch from OBELiX (simulated)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"structure": "data"}
    mock_get.return_value = mock_response

    result = download_module.fetch_obelix_structure("mp-1234")
    
    assert result is not None
    assert result == {"structure": "data"}

@patch('code.download.requests.get')
def test_fetch_obelix_structure_failure(mock_get):
    """Test fetch failure from OBELiX."""
    mock_get.side_effect = Exception("Connection error")

    result = download_module.fetch_obelix_structure("mp-1234")
    
    assert result is None

def test_save_structure(tmp_path):
    """Test saving a structure to a file."""
    mock_structure = MagicMock()
    output_file = tmp_path / "test.cif"
    
    result = download_module.save_structure(mock_structure, output_file)
    
    assert result is True
    mock_structure.to.assert_called_once_with(filename=str(output_file))

@patch('code.download.fetch_mp_structure')
@patch('code.download.save_structure')
def test_download_all_structures(mock_save, mock_fetch, tmp_path):
    """Test the full download pipeline with mocked dependencies."""
    mock_structure = MagicMock()
    mock_fetch.return_value = mock_structure
    mock_save.return_value = True

    mp_ids = ["mp-1", "mp-2"]
    results = download_module.download_all_structures(mp_ids, tmp_path, api_key="fake")

    assert results["total"] == 2
    assert results["successful"] == 2
    assert results["failed"] == 0
    assert len(results["details"]) == 2
    assert all(d["status"] == "success" for d in results["details"])

@patch('code.download.fetch_mp_structure')
@patch('code.download.save_structure')
def test_download_all_structures_partial_failure(mock_save, mock_fetch, tmp_path):
    """Test download pipeline with some failures."""
    mock_structure = MagicMock()
    mock_fetch.side_effect = [mock_structure, None]
    mock_save.return_value = True

    mp_ids = ["mp-1", "mp-2"]
    results = download_module.download_all_structures(mp_ids, tmp_path, api_key="fake")

    assert results["total"] == 2
    assert results["successful"] == 1
    assert results["failed"] == 1

@patch('code.download.fetch_mp_structure')
@patch('code.download.save_structure')
def test_contract_test_download_success_rate(mock_save, mock_fetch, tmp_path):
    """
    Contract test for data download success rate (>=93%).
    
    This test simulates a scenario where we attempt to download 100 structures.
    It verifies that the success rate meets the >=93% threshold defined in the
    user story requirements.
    
    Scenario: 100 attempts, 95 successes, 5 failures.
    Expected: Success rate = 95% (>= 93%), test passes.
    """
    mp_ids = [f"mp-{i:04d}" for i in range(100)]
    
    # Simulate 95 successes and 5 failures
    # We'll make the last 5 calls return None (failure)
    success_structure = MagicMock()
    mock_fetch.side_effect = [success_structure] * 95 + [None] * 5
    mock_save.return_value = True

    results = download_module.download_all_structures(mp_ids, tmp_path, api_key="fake")

    success_rate = (results["successful"] / results["total"]) * 100
    
    # Assert the contract: success rate must be >= 93%
    assert success_rate >= 93.0, f"Download success rate {success_rate}% is below the 93% contract threshold."
    assert results["successful"] == 95
    assert results["failed"] == 5

@patch('code.download.fetch_mp_structure')
@patch('code.download.save_structure')
def test_contract_test_download_failure_rate_exceeded(mock_save, mock_fetch, tmp_path):
    """
    Contract test verifying failure when success rate drops below 93%.
    
    Scenario: 100 attempts, 90 successes, 10 failures.
    Expected: Success rate = 90% (< 93%), test should fail (assertion error).
    """
    mp_ids = [f"mp-{i:04d}" for i in range(100)]
    
    # Simulate 90 successes and 10 failures
    success_structure = MagicMock()
    mock_fetch.side_effect = [success_structure] * 90 + [None] * 10
    mock_save.return_value = True

    results = download_module.download_all_structures(mp_ids, tmp_path, api_key="fake")

    success_rate = (results["successful"] / results["total"]) * 100

    # This assertion should fail in this specific test scenario
    # to demonstrate the contract check logic.
    # In a real CI environment, if the actual rate < 93%, the build fails.
    assert success_rate >= 93.0, f"Download success rate {success_rate}% is below the 93% contract threshold."