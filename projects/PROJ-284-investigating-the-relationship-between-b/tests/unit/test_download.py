"""Unit tests for data download functionality.

This module contains contract tests for the HCP data fetcher.
It mocks the HCP API to verify correct behavior without network access.
"""
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
from pathlib import Path

# Import the function we are testing from the actual implementation
from code.data.download import fetch_adhd_dataset
from code.logging_config import get_logger


logger = get_logger(__name__)


def test_fetch_returns_nifti_on_success():
    """Contract test: Mocks HCP API, verifies NIfTI return.

    This test ensures that when the HCP API (or in this case, the ADHD dataset
    fetcher from nilearn) returns successfully, the function correctly
    identifies and returns paths to NIfTI files.

    It validates:
    1. The function returns a dictionary with expected keys.
    2. The 'func' or 'scans' key contains a list of file paths.
    3. The file paths end with .nii or .nii.gz.
    4. The function handles the real data structure from nilearn's fetch_adhd.
    """
    # Mock the nilearn.datasets.fetch_adhd function to return a controlled structure
    # that mimics the real return value but without downloading.
    mock_phenotypic_data = [
        {
            "Subject": "1",
            "Rest1": "path/to/sub-1_func.nii.gz",
            "age": 10,
            "sex": "M"
        },
        {
            "Subject": "2",
            "Rest1": "path/to/sub-2_func.nii.gz",
            "age": 12,
            "sex": "F"
        }
    ]

    # Create a mock bunch object that mimics nilearn's return structure
    mock_bunch = MagicMock()
    mock_bunch.phenotypic = mock_phenotypic_data
    # The real fetch_adhd returns a list of paths in 'func' if available,
    # or we derive them from phenotypic if the mock is minimal.
    # In the real implementation, fetch_adhd returns a dict with 'func' keys.
    # We simulate the successful fetch result structure.
    mock_bunch.func = ["path/to/sub-1_func.nii.gz", "path/to/sub-2_func.nii.gz"]
    mock_bunch.data_dir = "/mock/data/dir"

    with patch('code.data.download.datasets.fetch_adhd', return_value=mock_bunch):
        # Call the function under test
        result = fetch_adhd_dataset(subjects=["1", "2"])

        # Assertions
        assert result is not None, "Result should not be None on success"
        assert "phenotypic" in result, "Result must contain 'phenotypic' key"
        assert "func" in result, "Result must contain 'func' key (NIfTI paths)"

        # Verify the NIfTI paths are present and valid
        func_paths = result["func"]
        assert isinstance(func_paths, list), "func paths should be a list"
        assert len(func_paths) == 2, "Should have 2 NIfTI paths for 2 subjects"

        for path in func_paths:
            assert path.endswith(".nii") or path.endswith(".nii.gz"), \
                f"Path {path} must be a valid NIfTI file"
            assert os.path.isabs(path) or path.startswith("path/to/"), \
                f"Path {path} should be a valid path string"

        # Verify phenotypic data is preserved
        phenotypic = result["phenotypic"]
        assert len(phenotypic) == 2, "Should have 2 phenotypic records"
        assert phenotypic[0]["Subject"] == "1"
        assert phenotypic[1]["Subject"] == "2"

        logger.log("test_fetch_returns_nifti_on_success", status="passed")

def test_fetch_handles_missing_subjects():
    """Contract test: Verify behavior when requested subjects are not found.

    This test ensures the function handles cases where the requested subject IDs
    do not exist in the available dataset, without crashing.
    """
    mock_phenotypic_data = [
        {"Subject": "1", "Rest1": "path/to/sub-1_func.nii.gz", "age": 10, "sex": "M"}
    ]
    mock_bunch = MagicMock()
    mock_bunch.phenotypic = mock_phenotypic_data
    mock_bunch.func = ["path/to/sub-1_func.nii.gz"]

    with patch('code.data.download.datasets.fetch_adhd', return_value=mock_bunch):
        # Request a subject that doesn't exist
        result = fetch_adhd_dataset(subjects=["999"])

        # Should return empty lists or None for missing data, not crash
        assert result is not None
        assert len(result.get("func", [])) == 0, "Should return empty list for missing subjects"
        assert len(result.get("phenotypic", [])) == 0, "Should return empty list for missing subjects"

        logger.log("test_fetch_handles_missing_subjects", status="passed")

def test_fetch_preserves_data_integrity():
    """Contract test: Verify that data types and structures are preserved.

    Ensures that the function does not inadvertently corrupt or alter the
    structure of the data returned by the underlying fetcher.
    """
    mock_phenotypic_data = [
        {
            "Subject": "1",
            "Rest1": "path/to/sub-1_func.nii.gz",
            "age": 10.5,
            "sex": "M",
            "extra_field": "value"
        }
    ]
    mock_bunch = MagicMock()
    mock_bunch.phenotypic = mock_phenotypic_data
    mock_bunch.func = ["path/to/sub-1_func.nii.gz"]

    with patch('code.data.download.datasets.fetch_adhd', return_value=mock_bunch):
        result = fetch_adhd_dataset(subjects=["1"])

        # Check that all original fields are preserved
        phenotypic = result["phenotypic"][0]
        assert phenotypic["Subject"] == "1"
        assert phenotypic["age"] == 10.5
        assert phenotypic["sex"] == "M"
        assert phenotypic["extra_field"] == "value"

        logger.log("test_fetch_preserves_data_integrity", status="passed")