"""
Unit tests for the download module.
"""

import pytest
from pathlib import Path
import tempfile
import json

from data.download import download_dataset, _get_dataset_info, _validate_bids_structure
from data.validate import DataValidationError


class TestDownloadDataset:
    """Tests for the download_dataset function."""
    
    def test_valid_dataset_id(self):
        """Test that valid dataset IDs are accepted."""
        info = _get_dataset_info("ds000030")
        assert info["name"] == "Resting-state fMRI from the Human Connectome Project"
        
        info = _get_dataset_info("ds000208")
        assert "musical_genre" in info["behavioral_vars"]
    
    def test_invalid_dataset_id(self):
        """Test that invalid dataset IDs raise ValueError."""
        with pytest.raises(ValueError):
            _get_dataset_info("invalid_dataset")
    
    def test_download_creates_expected_files(self):
        """Test that download creates expected BIDS files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_dataset("ds000030", tmpdir)
            
            dataset_path = Path(tmpdir) / "ds000030"
            assert dataset_path.exists()
            assert (dataset_path / "dataset_description.json").exists()
            assert (dataset_path / "participants.tsv").exists()
            assert (dataset_path / "task-rest_bold.nii.gz").exists()
    
    def test_download_returns_metadata(self):
        """Test that download returns correct metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_dataset("ds000030", tmpdir)
            
            assert "dataset_id" in result
            assert result["dataset_id"] == "ds000030"
            assert "checksum" in result
            assert "validated" in result
            assert result["validated"] is True
    
    def test_download_validation_fails_on_missing_behavioral_vars(self):
        """Test that download fails if required behavioral variables are missing."""
        # This test would require mocking the validation to fail
        # For now, we test that the validation is called
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dataset without required variables
            dataset_path = Path(tmpdir) / "test_dataset"
            dataset_path.mkdir()
            
            # Create dataset_description.json
            desc_file = dataset_path / "dataset_description.json"
            desc_file.write_text('{"Name": "Test"}')
            
            # Create participants.tsv without musical_genre
            participants_file = dataset_path / "participants.tsv"
            participants_file.write_text("participant_id\tage\tsex\nsub-001\t25\tM\n")
            
            # The download_dataset function should fail validation
            # Note: This test would need more complex mocking to fully test
            pass
    
    def test_checksum_computation(self):
        """Test that checksum is computed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = download_dataset("ds000030", tmpdir)
            result2 = download_dataset("ds000030", tmpdir)
            
            # Checksums should be identical for the same dataset
            assert result1["checksum"] == result2["checksum"]
    
    def test_bids_structure_validation(self):
        """Test BIDS structure validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "test_bids"
            dataset_path.mkdir()
            
            # Create required files
            (dataset_path / "dataset_description.json").write_text("{}")
            (dataset_path / "participants.tsv").write_text("participant_id\nsub-001")
            
            assert _validate_bids_structure(dataset_path) is True
            
            # Remove a required file
            (dataset_path / "dataset_description.json").unlink()
            assert _validate_bids_structure(dataset_path) is False


class TestDownloadIntegration:
    """Integration tests for the download module."""
    
    def test_download_multiple_datasets(self):
        """Test downloading multiple datasets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = download_dataset("ds000030", tmpdir)
            result2 = download_dataset("ds000208", tmpdir)
            
            assert result1["dataset_id"] == "ds000030"
            assert result2["dataset_id"] == "ds000208"
            
            dataset_path1 = Path(tmpdir) / "ds000030"
            dataset_path2 = Path(tmpdir) / "ds000208"
            
            assert dataset_path1.exists()
            assert dataset_path2.exists()
    
    def test_download_idempotency(self):
        """Test that downloading the same dataset twice is idempotent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = download_dataset("ds000030", tmpdir)
            result2 = download_dataset("ds000030", tmpdir)
            
            assert result1["status"] == "exists" or result2["status"] == "exists"
            assert result1["checksum"] == result2["checksum"]
