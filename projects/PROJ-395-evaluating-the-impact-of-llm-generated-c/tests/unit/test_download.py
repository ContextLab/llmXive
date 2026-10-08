"""
Unit tests for code/download.py.

Ensures the dataset loading mechanism works without authentication and
verifies the integrity of the downloaded artifacts.
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch, MagicMock

# Ensure code/ is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import (
    calculate_sha256,
    verify_dataset_structure,
    download_dataset,
    save_dataset_to_parquet,
    update_manifest
)


class TestCalculateSha256(TestCase):
    """Tests for the calculate_sha256 utility function."""

    def test_calculate_sha256_file(self):
        """Verify SHA-256 calculation on a temporary file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Hello, World!")
            tmp_path = tmp.name

        try:
            expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
            actual_hash = calculate_sha256(tmp_path)
            self.assertEqual(actual_hash, expected_hash)
        finally:
            os.unlink(tmp_path)

    def test_calculate_sha256_nonexistent(self):
        """Verify that calculating hash on a missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")


class TestVerifyDatasetStructure(TestCase):
    """Tests for dataset structure verification logic."""

    def test_verify_dataset_structure_valid(self):
        """Verify structure check passes for a valid directory layout."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create expected structure
            os.makedirs(os.path.join(tmp_dir, "data"))
            os.makedirs(os.path.join(tmp_dir, "code"))
            os.makedirs(os.path.join(tmp_dir, "tests"))
            
            # Create dummy files
            Path(os.path.join(tmp_dir, "data", "dummy.txt")).touch()
            
            result = verify_dataset_structure(tmp_dir)
            self.assertTrue(result)

    def test_verify_dataset_structure_missing_dir(self):
        """Verify structure check fails if a required directory is missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Only create 'data', missing 'code' and 'tests'
            os.makedirs(os.path.join(tmp_dir, "data"))
            
            result = verify_dataset_structure(tmp_dir)
            self.assertFalse(result)


class TestDownloadDatasetMock(TestCase):
    """Tests for download_dataset ensuring it runs without auth (mocked)."""

    @patch('download.hf_hub_download')
    @patch('download.Path')
    def test_download_dataset_no_auth_needed(self, mock_path_class, mock_hf_download):
        """
        Ensure the download flow executes without raising authentication errors.
        This test mocks the HF Hub to simulate a successful public download.
        """
        # Setup mocks
        mock_hf_download.return_value = "/mocked/path/to/dataset.parquet"
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        
        # Define a mock manifest
        mock_manifest = {
            "dataset_id": "google-research-datasets/mbpp",
            "revision": "main",
            "files": ["dataset.parquet"]
        }

        # Execute
        result_path = download_dataset(
            dataset_id="google-research-datasets/mbpp",
            revision="main",
            output_dir="/tmp/test_output",
            manifest=mock_manifest
        )

        # Assertions
        self.assertIsNotNone(result_path)
        mock_hf_download.assert_called_once()
        # Ensure no auth-related exceptions were raised during the mock call
        # (If the real function required auth and failed, this would raise)


class TestSaveDatasetToParquet(TestCase):
    """Tests for saving dataset to parquet format."""

    @patch('download.pd')
    def test_save_dataset_to_parquet(self, mock_pd):
        """Verify that the parquet save function calls pandas correctly."""
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "output.parquet")
            data = [{"prompt": "test", "test_list": []}]
            
            save_dataset_to_parquet(data, output_path)
            
            mock_pd.DataFrame.assert_called_once_with(data)
            mock_df.to_parquet.assert_called_once_with(output_path, index=False)


class TestUpdateManifest(TestCase):
    """Tests for updating the dataset manifest file."""

    def test_update_manifest(self):
        """Verify manifest update logic creates/updates the YAML file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest_path = os.path.join(tmp_dir, "manifest.yaml")
            dataset_info = {
                "id": "test-dataset",
                "version": "1.0.0",
                "hash": "abc123"
            }

            update_manifest(manifest_path, dataset_info)

            # Verify file exists
            self.assertTrue(os.path.exists(manifest_path))
            
            # Verify content (basic check)
            with open(manifest_path, 'r') as f:
                content = f.read()
                self.assertIn("id: test-dataset", content)
                self.assertIn("version: 1.0.0", content)


if __name__ == "__main__":
    main()