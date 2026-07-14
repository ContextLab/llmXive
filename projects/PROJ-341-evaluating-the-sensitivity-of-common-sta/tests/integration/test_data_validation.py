"""
Integration tests for dataset download and checksum verification.

This module tests the functionality of downloading real-world datasets
from UCI via ucimlrepo and verifying their integrity using checksums.

Tests cover:
- Dataset download (Breast Cancer, Wine, Adult)
- Checksum computation
- Checksum verification against stored metadata
- Metadata updates
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Import the functions we are testing
from code.analysis.validator import (
    ensure_data_raw_dir,
    load_simulation_metadata,
    save_simulation_metadata,
    compute_file_checksum,
    verify_dataset_checksum,
    download_breast_cancer_dataset,
    download_wine_dataset,
    download_adult_dataset
)

# Constants for test dataset IDs (as specified in tasks.md)
BREAST_CANCER_ID = 197
WINE_ID = 198
ADULT_ID = 522


class TestDatasetDownloadAndChecksum:
    """Integration tests for dataset download and checksum verification."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Create a temporary directory for test data
        self.test_data_dir = tempfile.mkdtemp()
        self.original_data_dir = os.environ.get('DATA_DIR')
        os.environ['DATA_DIR'] = self.test_data_dir
        
        # Ensure data/raw directory exists
        os.makedirs(os.path.join(self.test_data_dir, 'raw'), exist_ok=True)
        
        yield
        
        # Clean up
        if self.original_data_dir:
            os.environ['DATA_DIR'] = self.original_data_dir
        else:
            os.environ.pop('DATA_DIR', None)
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def test_ensure_data_raw_dir_creates_directory(self):
        """Test that ensure_data_raw_dir creates the data/raw directory if it doesn't exist."""
        new_dir = os.path.join(self.test_data_dir, 'new_test_raw')
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        
        # This should create the directory
        ensure_data_raw_dir(new_dir)
        
        assert os.path.exists(new_dir), "data/raw directory should be created"
        assert os.path.isdir(new_dir), "data/raw should be a directory"

    def test_load_simulation_metadata_empty_file(self):
        """Test loading metadata when file doesn't exist."""
        metadata_path = os.path.join(self.test_data_dir, 'nonexistent_metadata.json')
        result = load_simulation_metadata(metadata_path)
        
        assert isinstance(result, dict), "Should return empty dict for missing file"
        assert 'datasets' not in result or result['datasets'] == {}, "Should have empty datasets"

    def test_save_and_load_simulation_metadata(self):
        """Test saving and loading simulation metadata."""
        metadata_path = os.path.join(self.test_data_dir, 'test_metadata.json')
        
        test_data = {
            'datasets': {
                'test_dataset': {
                    'checksum': 'abc123',
                    'downloaded_at': '2024-01-01T00:00:00',
                    'source': 'test_source'
                }
            }
        }
        
        save_simulation_metadata(test_data, metadata_path)
        assert os.path.exists(metadata_path), "Metadata file should be created"
        
        loaded = load_simulation_metadata(metadata_path)
        assert loaded == test_data, "Loaded metadata should match saved metadata"

    def test_compute_file_checksum(self):
        """Test checksum computation on a known file."""
        test_file = os.path.join(self.test_data_dir, 'test_checksum.txt')
        test_content = "This is a test file for checksum verification."
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        checksum = compute_file_checksum(test_file)
        
        assert checksum is not None, "Checksum should not be None"
        assert len(checksum) == 64, "SHA256 checksum should be 64 characters"
        assert all(c in '0123456789abcdef' for c in checksum), "Checksum should be hex"

    def test_verify_dataset_checksum_success(self):
        """Test checksum verification when checksum matches."""
        test_file = os.path.join(self.test_data_dir, 'verify_test.txt')
        test_content = "Content to verify"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        correct_checksum = compute_file_checksum(test_file)
        
        result = verify_dataset_checksum(test_file, correct_checksum)
        assert result is True, "Verification should succeed with correct checksum"

    def test_verify_dataset_checksum_failure(self):
        """Test checksum verification when checksum doesn't match."""
        test_file = os.path.join(self.test_data_dir, 'verify_fail.txt')
        test_content = "Content to verify"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        wrong_checksum = "a" * 64  # Wrong checksum
        
        result = verify_dataset_checksum(test_file, wrong_checksum)
        assert result is False, "Verification should fail with wrong checksum"

    @patch('code.analysis.validator.ucimlrepo')
    def test_download_breast_cancer_dataset(self, mock_ucimlrepo):
        """Test downloading Breast Cancer dataset."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.data.features = MagicMock()
        mock_dataset.data.features.to_csv = MagicMock()
        mock_dataset.data.targets = MagicMock()
        mock_dataset.data.targets.to_csv = MagicMock()
        
        mock_ucimlrepo.fetch_dataset.return_value = mock_dataset
        
        # Mock file operations
        with patch('code.analysis.validator.pd.DataFrame.to_csv') as mock_to_csv:
            with patch('code.analysis.validator.save_simulation_metadata') as mock_save_meta:
                result = download_breast_cancer_dataset(self.test_data_dir)
        
        assert result is not None, "Should return dataset path"
        assert os.path.exists(result), "Dataset file should exist"
        assert 'breast_cancer' in result.lower(), "Filename should contain 'breast_cancer'"
        
        # Verify ucimlrepo was called with correct ID
        mock_ucimlrepo.fetch_dataset.assert_called_once_with(BREAST_CANCER_ID)

    @patch('code.analysis.validator.ucimlrepo')
    def test_download_wine_dataset(self, mock_ucimlrepo):
        """Test downloading Wine dataset."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.data.features = MagicMock()
        mock_dataset.data.features.to_csv = MagicMock()
        mock_dataset.data.targets = MagicMock()
        mock_dataset.data.targets.to_csv = MagicMock()
        
        mock_ucimlrepo.fetch_dataset.return_value = mock_dataset
        
        with patch('code.analysis.validator.pd.DataFrame.to_csv') as mock_to_csv:
            with patch('code.analysis.validator.save_simulation_metadata') as mock_save_meta:
                result = download_wine_dataset(self.test_data_dir)
        
        assert result is not None, "Should return dataset path"
        assert os.path.exists(result), "Dataset file should exist"
        assert 'wine' in result.lower(), "Filename should contain 'wine'"
        
        # Verify ucimlrepo was called with correct ID
        mock_ucimlrepo.fetch_dataset.assert_called_once_with(WINE_ID)

    @patch('code.analysis.validator.ucimlrepo')
    def test_download_adult_dataset(self, mock_ucimlrepo):
        """Test downloading Adult dataset."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.data.features = MagicMock()
        mock_dataset.data.features.to_csv = MagicMock()
        mock_dataset.data.targets = MagicMock()
        mock_dataset.data.targets.to_csv = MagicMock()
        
        mock_ucimlrepo.fetch_dataset.return_value = mock_dataset
        
        with patch('code.analysis.validator.pd.DataFrame.to_csv') as mock_to_csv:
            with patch('code.analysis.validator.save_simulation_metadata') as mock_save_meta:
                result = download_adult_dataset(self.test_data_dir)
        
        assert result is not None, "Should return dataset path"
        assert os.path.exists(result), "Dataset file should exist"
        assert 'adult' in result.lower(), "Filename should contain 'adult'"
        
        # Verify ucimlrepo was called with correct ID
        mock_ucimlrepo.fetch_dataset.assert_called_once_with(ADULT_ID)

    def test_integration_full_workflow(self):
        """Test a full workflow: download, compute checksum, verify checksum."""
        # Create a mock dataset file
        mock_file = os.path.join(self.test_data_dir, 'raw', 'mock_dataset.csv')
        os.makedirs(os.path.dirname(mock_file), exist_ok=True)
        
        test_data = "col1,col2,col3\n1,2,3\n4,5,6\n7,8,9\n"
        with open(mock_file, 'w') as f:
            f.write(test_data)
        
        # Compute checksum
        checksum = compute_file_checksum(mock_file)
        assert checksum is not None, "Checksum should be computed"
        
        # Verify checksum
        is_valid = verify_dataset_checksum(mock_file, checksum)
        assert is_valid is True, "Checksum should verify successfully"
        
        # Update metadata
        metadata = load_simulation_metadata(os.path.join(self.test_data_dir, 'simulation_metadata.json'))
        metadata['datasets']['mock_dataset'] = {
            'checksum': checksum,
            'downloaded_at': '2024-01-01T00:00:00',
            'source': 'mock'
        }
        save_simulation_metadata(metadata, os.path.join(self.test_data_dir, 'simulation_metadata.json'))
        
        # Load and verify metadata was saved correctly
        loaded_metadata = load_simulation_metadata(os.path.join(self.test_data_dir, 'simulation_metadata.json'))
        assert 'mock_dataset' in loaded_metadata['datasets'], "Dataset should be in metadata"
        assert loaded_metadata['datasets']['mock_dataset']['checksum'] == checksum, "Checksum should match"