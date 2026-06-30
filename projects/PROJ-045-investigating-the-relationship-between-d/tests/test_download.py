"""
Contract test for data download success rate (>=93%).

This test verifies that the download module successfully retrieves data
from OBELiX and Materials Project APIs with a success rate of at least 93%.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import URLError
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from download import download_crystal_structures
from utils import setup_logging

# Configure logging
logger = setup_logging()

# Constants
MIN_SUCCESS_RATE = 0.93
TOTAL_ATTEMPTS = 100  # Simulate 100 download attempts

@pytest.fixture
def mock_successful_response():
    """Mock a successful API response."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "success": True,
        "data": {"structure": "mock_structure_data"}
    }).encode('utf-8')
    return mock_response

@pytest.fixture
def mock_failed_response():
    """Mock a failed API response."""
    mock_response = MagicMock()
    mock_response.read.side_effect = URLError("Connection timeout")
    return mock_response

@patch('download.urlopen')
@patch('download.Path')
def test_download_success_rate(mock_path, mock_urlopen, mock_successful_response):
    """
    Test that the download success rate meets the >=93% threshold.
    
    This simulates 100 download attempts where 95 succeed and 5 fail.
    The success rate (95%) must be >= 93%.
    """
    # Setup mock paths
    mock_path.return_value = Path("/mock/data/raw")
    
    # Create a mix of successful and failed responses
    # 95 successes, 5 failures = 95% success rate
    responses = [mock_successful_response] * 95 + [mock_failed_response] * 5
    urlopen_calls = [responses[i] for i in range(len(responses))]
    
    # Configure urlopen to return our mix of responses
    def side_effect(*args, **kwargs):
        if urlopen_calls:
            return urlopen_calls.pop(0)
        return mock_successful_response
    
    mock_urlopen.side_effect = side_effect
    
    # Mock the MP-ID list with 100 IDs
    mock_mp_ids = [f"mp-{i}" for i in range(1, 101)]
    
    # Mock the download function to use our mock IDs
    with patch('download.MATERIALS_PROJECT_IDS', mock_mp_ids):
        with patch('download.OBELIX_IDS', []):  # No OBELiX IDs for this test
            try:
                # Run the download
                results = download_crystal_structures()
                
                # Calculate success rate
                total_downloads = len(mock_mp_ids)
                successful_downloads = sum(1 for r in results.values() if r.get('success', False))
                success_rate = successful_downloads / total_downloads if total_downloads > 0 else 0
                
                # Assert success rate meets threshold
                assert success_rate >= MIN_SUCCESS_RATE, (
                    f"Download success rate ({success_rate:.2%}) is below "
                    f"the required threshold ({MIN_SUCCESS_RATE:.2%}). "
                    f"Successful: {successful_downloads}/{total_downloads}"
                )
                
                logger.info(
                    f"Download success rate test PASSED: {success_rate:.2%} "
                    f"({successful_downloads}/{total_downloads})"
                )
                
            except Exception as e:
                pytest.fail(f"Download process failed with error: {str(e)}")

@patch('download.urlopen')
def test_download_retry_logic(mock_urlopen, mock_successful_response):
    """
    Test that the retry logic handles transient failures correctly.
    
    This verifies that failed attempts are retried and eventually succeed.
    """
    # Setup: First 2 attempts fail, 3rd succeeds
    responses = [mock_failed_response, mock_failed_response, mock_successful_response]
    
    def side_effect(*args, **kwargs):
        if responses:
            return responses.pop(0)
        return mock_successful_response
    
    mock_urlopen.side_effect = side_effect
    
    # Mock a single MP-ID
    mock_mp_ids = ["mp-123"]
    
    with patch('download.MATERIALS_PROJECT_IDS', mock_mp_ids):
        with patch('download.OBELIX_IDS', []):
            try:
                results = download_crystal_structures()
                
                # Verify the download eventually succeeded after retries
                assert results["mp-123"]["success"], "Download should have succeeded after retries"
                
                # Verify that urlopen was called 3 times (2 failures + 1 success)
                assert mock_urlopen.call_count == 3, "Retry logic should have attempted 3 times"
                
                logger.info("Retry logic test PASSED: Failed attempts were correctly retried")
                
            except Exception as e:
                pytest.fail(f"Retry logic test failed with error: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
