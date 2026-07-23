"""
Tests for the ResearchClawBench data loader.

These tests verify that the loader correctly fetches the dataset,
computes checksums, and handles errors appropriately.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sys
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import (
    compute_sha256_file,
    compute_sha256_string,
    fetch_researchclawbench_dataset,
    verify_and_write_checksum,
    load_researchclawbench
)
from src.config import Config

class TestChecksumFunctions:
    """Tests for checksum computation functions."""
    
    def test_compute_sha256_string(self):
        """Test that SHA256 computation works correctly."""
        test_string = "test data for checksum"
        result = compute_sha256_string(test_string)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex string length
        assert result.isalnum()
    
    def test_compute_sha256_string_consistency(self):
        """Test that same input produces same hash."""
        test_string = "consistent test"
        hash1 = compute_sha256_string(test_string)
        hash2 = compute_sha256_string(test_string)
        assert hash1 == hash2
    
    def test_compute_sha256_string_uniqueness(self):
        """Test that different inputs produce different hashes."""
        hash1 = compute_sha256_string("input 1")
        hash2 = compute_sha256_string("input 2")
        assert hash1 != hash2

class TestFetchDataset:
    """Tests for dataset fetching logic."""
    
    @patch('src.data.loader.load_dataset')
    def test_fetch_success(self, mock_load_dataset):
        """Test successful dataset fetch."""
        # Setup mock
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset
        
        # Call function
        result = fetch_researchclawbench_dataset()
        
        # Verify
        mock_load_dataset.assert_called_once()
        assert result == mock_dataset
    
    @patch('src.data.loader.load_dataset')
    def test_fetch_failure_invalid_id(self, mock_load_dataset):
        """Test that invalid dataset ID raises ValueError."""
        # Setup mock to raise exception
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        # Verify exception
        with pytest.raises(ValueError, match="Invalid dataset ID"):
            fetch_researchclawbench_dataset()

class TestVerifyAndWriteChecksum:
    """Tests for checksum verification and writing."""
    
    def test_verify_and_write_checksum_creates_file(self):
        """Test that checksum file is created in correct format."""
        # Create a mock dataset
        mock_dataset = MagicMock()
        mock_dataset.keys.return_value = ['train']
        mock_dataset.__getitem__.return_value = MagicMock()
        mock_dataset.__getitem__.return_value.to_list.return_value = [
            {'id': 1, 'data': 'test1'},
            {'id': 2, 'data': 'test2'}
        ]
        mock_dataset.__getitem__.return_value.column_names = ['id', 'data']
        mock_dataset.__getitem__.return_value.__len__.return_value = 2
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            # Call function
            verify_and_write_checksum(mock_dataset, output_dir)
            
            # Verify file exists
            checksum_file = output_dir / "checksum.txt"
            assert checksum_file.exists()
            
            # Verify format
            with open(checksum_file, 'r') as f:
                content = f.read()
            
            assert content.startswith("sha256: ")
            assert len(content.split(": ")[1]) == 64  # Hex string length
    
    def test_verify_and_write_checksum_mismatch_raises(self):
        """Test that checksum mismatch raises RuntimeError."""
        # Create a mock dataset
        mock_dataset = MagicMock()
        mock_dataset.keys.return_value = ['train']
        mock_dataset.__getitem__.return_value = MagicMock()
        mock_dataset.__getitem__.return_value.to_list.return_value = [
            {'id': 1, 'data': 'test1'}
        ]
        mock_dataset.__getitem__.return_value.column_names = ['id', 'data']
        mock_dataset.__getitem__.return_value.__len__.return_value = 1
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            # Mock config to have an expected checksum that won't match
            with patch('src.data.loader.config') as mock_config:
                mock_config.EXPECTED_DATASET_CHECKSUM = "0" * 64  # All zeros
                
                # Verify exception is raised
                with pytest.raises(RuntimeError, match="VERIFIED_ACCURACY_GATE_FAILED"):
                    verify_and_write_checksum(mock_dataset, output_dir)

class TestLoadResearchClawBench:
    """Tests for the main loader function."""
    
    @patch('src.data.loader.fetch_researchclawbench_dataset')
    @patch('src.data.loader.verify_and_write_checksum')
    def test_load_success(self, mock_verify, mock_fetch):
        """Test successful load process."""
        # Setup mocks
        mock_dataset = MagicMock()
        mock_fetch.return_value = mock_dataset
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Patch the output directory
            with patch('src.data.loader.PROJECT_ROOT', Path(tmp_dir)):
                # Call function
                result = load_researchclawbench()
                
                # Verify
                mock_fetch.assert_called_once()
                mock_verify.assert_called_once()
                assert result == mock_dataset
    
    @patch('src.data.loader.fetch_researchclawbench_dataset')
    def test_load_fetch_failure(self, mock_fetch):
        """Test that fetch failure propagates correctly."""
        # Setup mock to raise exception
        mock_fetch.side_effect = ValueError("Failed to fetch")
        
        # Verify exception propagates
        with pytest.raises(ValueError, match="Failed to fetch"):
            load_researchclawbench()
    
    @patch('src.data.loader.fetch_researchclawbench_dataset')
    @patch('src.data.loader.verify_and_write_checksum')
    def test_load_checksum_failure(self, mock_verify, mock_fetch):
        """Test that checksum failure propagates correctly."""
        # Setup mocks
        mock_dataset = MagicMock()
        mock_fetch.return_value = mock_dataset
        mock_verify.side_effect = RuntimeError("Checksum failed")
        
        # Verify exception propagates
        with pytest.raises(RuntimeError, match="Checksum failed"):
            load_researchclawbench()

class TestIntegration:
    """Integration tests that verify the full flow."""
    
    def test_full_flow_creates_checksum_file(self):
        """Test that the full flow creates the checksum file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create a minimal mock dataset
            mock_dataset = MagicMock()
            mock_dataset.keys.return_value = ['test']
            mock_data = MagicMock()
            mock_data.to_list.return_value = [{'id': 1, 'value': 'test'}]
            mock_data.column_names = ['id', 'value']
            mock_data.__len__.return_value = 1
            mock_dataset.__getitem__.return_value = mock_data
            
            with patch('src.data.loader.fetch_researchclawbench_dataset', return_value=mock_dataset):
                with patch('src.data.loader.PROJECT_ROOT', tmp_path):
                    load_researchclawbench()
            
            # Verify checksum file was created
            checksum_file = tmp_path / "data" / "raw" / "checksum.txt"
            assert checksum_file.exists()
            
            # Verify format
            with open(checksum_file, 'r') as f:
                content = f.read()
            
            assert content.startswith("sha256: ")
            assert len(content.split(": ")[1]) == 64
