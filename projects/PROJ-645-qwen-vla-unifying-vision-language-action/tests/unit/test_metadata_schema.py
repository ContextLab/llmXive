"""
Unit tests for metadata schema and management.

Tests verify:
- Schema structure is valid
- Metadata can be loaded and saved
- Checksum computation works
- Dataset updates work correctly
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.metadata_manager import MetadataManager


class TestMetadataSchema:
    """Test cases for metadata schema structure."""
    
    @pytest.fixture
    def temp_metadata_file(self, tmp_path):
        """Create a temporary metadata file for testing."""
        metadata_content = {
            "metadata_version": "1.0.0",
            "dataset_name": "test_dataset",
            "version": "0.0.1",
            "created_at": "2024-01-01T00:00:00Z",
            "datasets": [
                {
                    "name": "test_dataset_1",
                    "path": "data/test1.parquet",
                    "format": "parquet",
                    "version": "pending",
                    "checksum": "pending",
                    "row_count": 0,
                    "description": "Test dataset 1",
                    "source_url": "https://example.com",
                    "filters_applied": ["filter1"],
                    "status": "pending_download"
                }
            ]
        }
        
        metadata_file = tmp_path / "metadata.yaml"
        with open(metadata_file, 'w') as f:
            yaml.dump(metadata_content, f)
        
        return metadata_file
    
    def test_schema_structure(self, temp_metadata_file):
        """Test that the metadata schema has required fields."""
        manager = MetadataManager(temp_metadata_file)
        
        assert 'metadata_version' in manager.metadata
        assert 'dataset_name' in manager.metadata
        assert 'version' in manager.metadata
        assert 'created_at' in manager.metadata
        assert 'datasets' in manager.metadata
        assert isinstance(manager.metadata['datasets'], list)
    
    def test_dataset_entry_structure(self, temp_metadata_file):
        """Test that dataset entries have required fields."""
        manager = MetadataManager(temp_metadata_file)
        dataset = manager.get_dataset('test_dataset_1')
        
        assert dataset is not None
        assert 'name' in dataset
        assert 'path' in dataset
        assert 'format' in dataset
        assert 'version' in dataset
        assert 'checksum' in dataset
        assert 'row_count' in dataset
        assert 'description' in dataset
        assert 'source_url' in dataset
        assert 'filters_applied' in dataset
        assert 'status' in dataset
    
    def test_get_dataset_by_name(self, temp_metadata_file):
        """Test retrieving a dataset by name."""
        manager = MetadataManager(temp_metadata_file)
        
        dataset = manager.get_dataset('test_dataset_1')
        assert dataset is not None
        assert dataset['name'] == 'test_dataset_1'
        
        # Test non-existent dataset
        non_existent = manager.get_dataset('non_existent')
        assert non_existent is None
    
    def test_update_dataset(self, temp_metadata_file):
        """Test updating a dataset entry."""
        manager = MetadataManager(temp_metadata_file)
        
        # Update dataset
        result = manager.update_dataset(
            name='test_dataset_1',
            checksum='abc123',
            row_count=1000,
            version='1.0.0',
            status='verified'
        )
        
        assert result is True
        
        # Verify update
        updated = manager.get_dataset('test_dataset_1')
        assert updated['checksum'] == 'abc123'
        assert updated['row_count'] == 1000
        assert updated['version'] == '1.0.0'
        assert updated['status'] == 'verified'
    
    def test_update_non_existent_dataset(self, temp_metadata_file):
        """Test updating a non-existent dataset returns False."""
        manager = MetadataManager(temp_metadata_file)
        
        result = manager.update_dataset(
            name='non_existent',
            checksum='abc123'
        )
        
        assert result is False
    
    def test_get_all_datasets(self, temp_metadata_file):
        """Test getting all datasets."""
        manager = MetadataManager(temp_metadata_file)
        datasets = manager.get_all_datasets()
        
        assert isinstance(datasets, list)
        assert len(datasets) == 1
        assert datasets[0]['name'] == 'test_dataset_1'
    
    def test_get_pending_datasets(self, temp_metadata_file):
        """Test getting pending datasets."""
        manager = MetadataManager(temp_metadata_file)
        pending = manager.get_pending_datasets()
        
        assert isinstance(pending, list)
        assert len(pending) == 1
        assert pending[0]['status'] == 'pending_download'
    
    def test_get_verified_datasets(self, temp_metadata_file):
        """Test getting verified datasets."""
        manager = MetadataManager(temp_metadata_file)
        verified = manager.get_verified_datasets()
        
        assert isinstance(verified, list)
        assert len(verified) == 0  # Initially none are verified
    
    def test_generate_report(self, temp_metadata_file):
        """Test report generation."""
        manager = MetadataManager(temp_metadata_file)
        report = manager.generate_report()
        
        assert isinstance(report, str)
        assert 'Dataset Metadata Report' in report
        assert 'test_dataset_1' in report
        assert 'pending_download' in report
    
    def test_save_metadata(self, temp_metadata_file):
        """Test that metadata is saved correctly."""
        manager = MetadataManager(temp_metadata_file)
        
        # Update and save
        manager.update_dataset(
            name='test_dataset_1',
            status='verified'
        )
        
        # Reload and verify
        with open(temp_metadata_file, 'r') as f:
            reloaded = yaml.safe_load(f)
        
        assert reloaded['datasets'][0]['status'] == 'verified'

class TestChecksumComputation:
    """Test checksum computation functionality."""
    
    def test_compute_file_checksum(self, tmp_path):
        """Test SHA256 checksum computation."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        manager = MetadataManager()  # Path doesn't matter for this method
        
        checksum = manager.compute_file_checksum(test_file)
        
        # Verify it's a valid hex string
        assert len(checksum) == 64  # SHA256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_checksum_deterministic(self, tmp_path):
        """Test that checksum is deterministic."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        manager = MetadataManager()
        
        checksum1 = manager.compute_file_checksum(test_file)
        checksum2 = manager.compute_file_checksum(test_file)
        
        assert checksum1 == checksum2
    
    def test_checksum_changes_with_content(self, tmp_path):
        """Test that checksum changes when content changes."""
        test_file = tmp_path / "test.txt"
        
        test_file.write_bytes(b"Content 1")
        checksum1 = MetadataManager().compute_file_checksum(test_file)
        
        test_file.write_bytes(b"Content 2")
        checksum2 = MetadataManager().compute_file_checksum(test_file)
        
        assert checksum1 != checksum2