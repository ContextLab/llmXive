"""
Contract test for repository filtering logic.

This test verifies that the filter_repos function correctly raises a ValueError
when encountering repositories with invalid license types, as per the PESTO
filter requirements.
"""
import pytest
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.acquisition import filter_repos

def test_filter_repos_raises_value_error_for_invalid_license():
    """
    Assert that filter_repos() raises ValueError for invalid license types.
    
    This is a contract test ensuring the interface behaves as expected:
    - Valid licenses should pass through.
    - Invalid or missing licenses should raise ValueError.
    """
    # Test case 1: Repository with an invalid license (e.g., "Proprietary" or "UNLICENSED")
    repos_with_invalid_license = [
        {
            "full_name": "test-org/invalid-repo",
            "language": "Python",
            "license": {
                "spdx_id": "Proprietary",
                "name": "Proprietary License"
            }
        },
        {
            "full_name": "test-org/valid-repo",
            "language": "Python",
            "license": {
                "spdx_id": "MIT",
                "name": "MIT License"
            }
        }
    ]

    # The function should raise ValueError when it encounters "Proprietary"
    # Since the implementation processes sequentially, it will raise on the first invalid one.
    with pytest.raises(ValueError) as exc_info:
        filter_repos(repos_with_invalid_license)

    assert "Proprietary" in str(exc_info.value)
    assert "invalid license type" in str(exc_info.value).lower()

def test_filter_repos_raises_value_error_for_missing_license():
    """
    Assert that filter_repos() raises ValueError for missing license info.
    """
    repos_with_missing_license = [
        {
            "full_name": "test-org/no-license-repo",
            "language": "Python",
            "license": None
        }
    ]

    with pytest.raises(ValueError) as exc_info:
        filter_repos(repos_with_missing_license)

    assert "None" in str(exc_info.value)
    assert "invalid license type" in str(exc_info.value).lower()

def test_filter_repos_passes_valid_licenses():
    """
    Assert that filter_repos() returns repositories with valid licenses.
    """
    repos_with_valid_licenses = [
        {
            "full_name": "test-org/mit-repo",
            "language": "Python",
            "license": {"spdx_id": "MIT", "name": "MIT License"}
        },
        {
            "full_name": "test-org/apache-repo",
            "language": "Java",
            "license": {"spdx_id": "Apache-2.0", "name": "Apache License 2.0"}
        }
    ]

    result = filter_repos(repos_with_valid_licenses)
    
    assert len(result) == 2
    assert result[0]["full_name"] == "test-org/mit-repo"
    assert result[1]["full_name"] == "test-org/apache-repo"