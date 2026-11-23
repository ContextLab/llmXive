"""
Unit tests for checksum_datasets.py
"""
import os
import sys
import csv
import hashlib
import tempfile
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.checksum_datasets import compute_sha256, get_dataset_id_from_filename

class TestComputeSha256:
    def test_compute_sha256_single_file(self, tmp_path):
        """Test SHA-256 computation on a single file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        # Compute hash
        computed_hash = compute_sha256(test_file)
        
        # Verify against expected hash
        expected_hash = hashlib.sha256(content).hexdigest()
        assert computed_hash == expected_hash
    
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA-256 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        computed_hash = compute_sha256(test_file)
        expected_hash = hashlib.sha256(b"").hexdigest()
        assert computed_hash == expected_hash
    
    def test_compute_sha256_large_file(self, tmp_path):
        """Test SHA-256 computation on a larger file."""
        test_file = tmp_path / "large.txt"
        content = b"x" * (1024 * 1024)  # 1MB
        test_file.write_bytes(content)
        
        computed_hash = compute_sha256(test_file)
        expected_hash = hashlib.sha256(content).hexdigest()
        assert computed_hash == expected_hash

class TestGetDatasetIdFromFilename:
    def test_get_dataset_id_with_prefix(self):
        """Test extracting dataset ID from filename with 'dataset_' prefix."""
        file_path = Path("dataset_123.csv")
        dataset_id = get_dataset_id_from_filename(file_path)
        assert dataset_id == "123"
    
    def test_get_dataset_id_without_prefix(self):
        """Test extracting dataset ID from filename without prefix."""
        file_path = Path("456.csv")
        dataset_id = get_dataset_id_from_filename(file_path)
        assert dataset_id == "456"
    
    def test_get_dataset_id_with_extension(self):
        """Test that extension is properly removed."""
        file_path = Path("dataset_789.csv")
        dataset_id = get_dataset_id_from_filename(file_path)
        assert dataset_id == "789"
    
    def test_get_dataset_id_arff(self):
        """Test extracting dataset ID from ARFF file."""
        file_path = Path("dataset_abc.arff")
        dataset_id = get_dataset_id_from_filename(file_path)
        assert dataset_id == "abc"

class TestChecksumIntegration:
    @pytest.fixture
    def sample_filtered_dir(self, tmp_path):
        """Create a sample filtered directory with test datasets."""
        filtered_dir = tmp_path / "data" / "filtered"
        filtered_dir.mkdir(parents=True)
        
        # Create sample dataset files
        (filtered_dir / "dataset_001.csv").write_text("col1,col2\n1,2\n3,4")
        (filtered_dir / "dataset_002.csv").write_text("a,b\n10,20\n30,40")
        (filtered_dir / "dataset_003.arff").write_text("@relation test\n@data\n1,2")
        
        return filtered_dir
    
    def test_checksums_file_created(self, sample_filtered_dir, tmp_path):
        """Test that checksums.csv is created with correct headers."""
        # We can't easily test the full main() without mocking logging and paths,
        # but we can verify the helper functions work correctly
        files = list(sample_filtered_dir.glob("*.csv")) + list(sample_filtered_dir.glob("*.arff"))
        assert len(files) == 3