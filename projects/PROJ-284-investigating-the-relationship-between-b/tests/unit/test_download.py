"""
Unit tests for the data download module.
Focuses on contract testing with mocked external dependencies.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
from pathlib import Path

# Add project root to path for imports if running directly
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import fetch_adhd_dataset, check_ica_fix_availability
from nilearn._utils.data_gen import generate_fake_fmri
from nibabel import Nifti1Image
import numpy as np


class TestDownloadContract(unittest.TestCase):
    """Contract tests for the download module."""

    @patch('code.data.download.datasets')
    @patch('code.data.download.os.path.join')
    @patch('code.data.download.os.getenv')
    def test_fetch_returns_nifti_on_success(
        self, mock_getenv, mock_join, mock_datasets
    ):
        """
        Contract test: mocks HCP/ADHD API (via nilearn.datasets),
        verifies that the function returns a list of NIfTI file paths
        on success.

        This validates the interface contract:
        1. fetch_adhd_dataset calls the underlying data fetcher.
        2. It returns a list of strings (paths to .nii.gz files).
        3. The files do not need to physically exist on disk for this
           unit test, but the function must return valid path strings
           that point to .nii.gz extensions.
        """
        # Setup mocks
        mock_getenv.return_value = "/mock/home"
        mock_join.return_value = "/mock/nilearn_data"

        # Create a mock bunch object mimicking nilearn.datasets.fetch_adhd
        mock_bunch = MagicMock()
        # Simulate real nilearn output: list of paths to .nii.gz files
        mock_paths = [
            "/mock/nilearn_data/sub-01_rest.nii.gz",
            "/mock/nilearn_data/sub-02_rest.nii.gz",
            "/mock/nilearn_data/sub-03_rest.nii.gz"
        ]
        mock_bunch.func_img = mock_paths
        mock_bunch.phenotypic = MagicMock()
        mock_bunch.phenotypic.columns = []
        mock_bunch.phenotypic.to_csv = MagicMock(return_value="")

        mock_datasets.fetch_adhd.return_value = mock_bunch

        # Execute
        result = fetch_adhd_dataset(subjects=[1, 2, 3])

        # Assert
        self.assertIsInstance(result, list, "Return value must be a list of paths")
        self.assertEqual(len(result), 3, "Should return 3 paths for 3 subjects")

        for path in result:
            self.assertIsInstance(path, str, "Each item must be a string path")
            self.assertTrue(
                path.endswith(".nii.gz"),
                f"Path {path} must end with .nii.gz extension"
            )

        # Verify the mock was called correctly
        mock_datasets.fetch_adhd.assert_called_once()

    @patch('code.data.download.requests')
    def test_check_ica_fix_availability_returns_bool(self, mock_requests):
        """
        Contract test: verifies check_ica_fix_availability returns a boolean
        based on the API response status code.
        """
        # Case 1: Available (200 OK)
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_requests.get.return_value = mock_response_ok

        result = check_ica_fix_availability()
        self.assertTrue(result, "Should return True when API returns 200")

        # Case 2: Unavailable (404)
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 404
        mock_requests.get.return_value = mock_response_fail

        result = check_ica_fix_availability()
        self.assertFalse(result, "Should return False when API returns 404")

    @patch('code.data.download.datasets')
    def test_fetch_handles_empty_subject_list(self, mock_datasets):
        """
        Contract test: verifies behavior when an empty subject list is provided.
        """
        mock_bunch = MagicMock()
        mock_bunch.func_img = []
        mock_bunch.phenotypic = MagicMock()
        mock_bunch.phenotypic.columns = []
        mock_datasets.fetch_adhd.return_value = mock_bunch

        result = fetch_adhd_dataset(subjects=[])

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    @patch('code.data.download.datasets')
    def test_fetch_filters_subjects_correctly(self, mock_datasets):
        """
        Contract test: verifies that only requested subjects are returned.
        """
        # Mock a dataset with 5 subjects
        all_paths = [f"/data/sub-{i:03d}_rest.nii.gz" for i in range(1, 6)]
        mock_bunch = MagicMock()
        mock_bunch.func_img = all_paths
        mock_bunch.phenotypic = MagicMock()
        mock_bunch.phenotypic.columns = []
        mock_datasets.fetch_adhd.return_value = mock_bunch

        # Request specific subset
        requested = [1, 3, 5]
        result = fetch_adhd_dataset(subjects=requested)

        # Should return exactly the requested indices
        expected_paths = [f"/data/sub-{i:03d}_rest.nii.gz" for i in requested]
        self.assertEqual(result, expected_paths)

if __name__ == "__main__":
    unittest.main()