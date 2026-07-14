"""Unit tests for the data download module.

This module contains contract tests for the HCP/ADHD data fetching logic.
It mocks external API calls to verify that the system correctly handles
success and failure scenarios without requiring network access during
unit testing.
"""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import nibabel as nib
import numpy as np

# Import the module under test
# We import the function directly to test it in isolation
from code.data.download import fetch_adhd_dataset, check_ica_fix_availability


class TestDownloadContract(unittest.TestCase):
    """Contract tests for the download module.

    These tests verify that the download logic adheres to the specified
    interface and behavior, ensuring that the pipeline can fetch data
    correctly when real credentials and network are available.
    """

    @patch('code.data.download.datasets')
    @patch('code.data.download.os.path.exists')
    def test_fetch_returns_nifti_on_success(self, mock_exists, mock_datasets):
        """Contract test: fetch_returns_nifti_on_success.

        Verifies that when the HCP/ADHD API returns a successful response,
        the fetch function returns a list of NIfTI file paths.

        This test mocks the nilearn datasets module to simulate a successful
        download without actually contacting the network.

        Expected behavior:
        1. The function calls the underlying dataset fetcher.
        2. The function returns a list of file paths (strings or Path objects).
        3. Each returned path points to a valid NIfTI file (verified by existence check).
        """
        # Setup: Mock the datasets.fetch_adhd to return a mock bunch
        mock_bunch = MagicMock()
        mock_bunch.func = [
            "/mock/path/sub-01_task-rest_bold.nii.gz",
            "/mock/path/sub-02_task-rest_bold.nii.gz"
        ]
        mock_bunch.phenotypic = MagicMock()
        mock_bunch.phenotypic.columns = ["Subject", "Age"]
        mock_bunch.phenotypic.to_csv = MagicMock()

        mock_datasets.fetch_adhd.return_value = mock_bunch
        mock_exists.return_value = True  # Pretend files exist on disk

        # Also mock the actual file check if needed, but here we rely on the mock path
        # The function should return the list of files from mock_bunch.func

        # Execute: Call the function under test
        # Note: fetch_adhd_dataset wraps datasets.fetch_adhd
        result = fetch_adhd_dataset(subject_ids=["100307", "100909"], data_dir="/tmp/test_data")

        # Assert: Verify the result is a list of paths
        self.assertIsInstance(result, list, "fetch_adhd_dataset should return a list of file paths")
        self.assertEqual(len(result), 2, "Should return 2 file paths for 2 subjects")

        # Verify that the paths are strings or Path objects
        for path in result:
            self.assertIsInstance(path, (str, Path), "Each result item must be a path string or Path object")

        # Verify that the underlying fetcher was called
        mock_datasets.fetch_adhd.assert_called_once()

    @patch('code.data.download.datasets')
    def test_fetch_handles_empty_dataset(self, mock_datasets):
        """Contract test: Verify behavior when dataset is empty.

        Ensures the function handles the case where no files are returned
        without crashing.
        """
        mock_bunch = MagicMock()
        mock_bunch.func = []
        mock_bunch.phenotypic = MagicMock()
        mock_bunch.phenotypic.columns = []
        mock_datasets.fetch_adhd.return_value = mock_bunch

        result = fetch_adhd_dataset(subject_ids=[], data_dir="/tmp/test_data")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    @patch('code.data.download.os')
    def test_check_ica_fix_availability_logic(self, mock_os):
        """Contract test: Verify ICA-FIX availability check logic.

        Simulates the filesystem check for ICA-FIX processed data availability.
        """
        # Scenario 1: ICA-FIX directory exists
        mock_os.path.join.return_value = "/mock/ica_fix_dir"
        mock_os.path.exists.return_value = True
        
        # We need to mock the specific path check inside the function
        # Since we can't easily mock the internal logic without refactoring,
        # we verify the contract by ensuring the function returns a boolean
        
        # Re-mock to simulate the internal check
        with patch.object(mock_os.path, 'exists', return_value=True):
            # The function should return True if the path exists
            # Note: This test is a bit abstract because the actual implementation
            # might have specific logic. We are verifying the contract that
            # it returns a boolean based on existence.
            pass 
        
        # Let's test the actual function behavior with a known path
        # We will mock the specific path check
        with patch('code.data.download.os.path.exists', return_value=True):
            result = check_ica_fix_availability()
            self.assertIsInstance(result, bool)
            self.assertTrue(result)

        with patch('code.data.download.os.path.exists', return_value=False):
            result = check_ica_fix_availability()
            self.assertIsInstance(result, bool)
            self.assertFalse(result)

    @patch('code.data.download.datasets')
    def test_fetch_with_specific_subjects(self, mock_datasets):
        """Contract test: Verify fetching with specific subject IDs.

        Ensures that the function correctly filters or requests specific subjects.
        """
        mock_bunch = MagicMock()
        # Simulate data for specific subjects
        mock_bunch.func = [
            "/data/sub-100307_task-rest_bold.nii.gz",
            "/data/sub-100909_task-rest_bold.nii.gz"
        ]
        mock_bunch.phenotypic = MagicMock()
        mock_bunch.phenotypic.columns = ["Subject"]
        mock_bunch.phenotypic.to_csv = MagicMock()
        
        mock_datasets.fetch_adhd.return_value = mock_bunch

        # Call with specific subjects
        subjects = ["100307", "100909"]
        result = fetch_adhd_dataset(subject_ids=subjects, data_dir="/tmp/data")

        self.assertEqual(len(result), 2)
        # Verify the filenames contain the subject IDs
        for path in result:
            self.assertTrue(any(sub_id in str(path) for sub_id in subjects))

if __name__ == '__main__':
    unittest.main()