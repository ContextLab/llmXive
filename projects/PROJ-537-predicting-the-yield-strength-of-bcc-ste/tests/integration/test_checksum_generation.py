import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import CONFIG
from utils.checksums import generate_checksum, generate_all_checksums
from ingestion.generate_checksums import main


class TestChecksumGeneration:
    """Integration tests for checksum generation functionality"""

    @pytest.fixture
    def temp_test_files(self, tmp_path):
        """Create temporary test files with known content"""
        # Create raw data directory structure
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        # Create intermediate data directory structure
        intermediate_dir = tmp_path / "data" / "intermediate"
        intermediate_dir.mkdir(parents=True)
        
        # Create a test file in raw
        test_file_raw = raw_dir / "test_data.csv"
        test_file_raw.write_text("col1,col2\n1,2\n3,4\n")
        
        # Create a test file in intermediate
        test_file_inter = intermediate_dir / "merged.csv"
        test_file_inter.write_text("feature,target\n0.5,100\n0.8,150\n")
        
        return {
            "raw_dir": raw_dir,
            "intermediate_dir": intermediate_dir,
            "raw_file": test_file_raw,
            "inter_file": test_file_inter
        }

    def test_generate_single_checksum(self, temp_test_files):
        """Test that a single file checksum is generated correctly"""
        file_path = temp_test_files["raw_file"]
        
        # Calculate expected checksum manually
        expected_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        
        # Use our function
        actual_hash = generate_checksum(file_path)
        
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA-256 hex length

    def test_generate_all_checksums(self, temp_test_files):
        """Test that checksums are generated for multiple files"""
        directories = [temp_test_files["raw_dir"], temp_test_files["intermediate_dir"]]
        
        checksums = generate_all_checksums(directories)
        
        # Should have exactly 2 files
        assert len(checksums) == 2
        
        # Verify both files are in the results
        raw_file_name = temp_test_files["raw_file"].name
        inter_file_name = temp_test_files["inter_file"].name
          
        assert any(raw_file_name in str(path) for path in checksums.keys())
        assert any(inter_file_name in str(path) for path in checksums.keys())

    def test_checksums_file_creation(self, temp_test_files, tmp_path):
        """Test that the main function creates the checksums.txt file"""
        # Temporarily override CONFIG paths for testing
        original_data_dir = CONFIG.DATA_DIR
        original_provenance_dir = CONFIG.DATA_PROVENANCE_DIR
        
        test_data_dir = tmp_path / "data"
        test_provenance_dir = tmp_path / "provenance"
        
        # Mock the config
        import config
        config.CONFIG.DATA_DIR = test_data_dir
        config.CONFIG.DATA_RAW_DIR = temp_test_files["raw_dir"]
        config.CONFIG.DATA_INTERMEDIATE_DIR = temp_test_files["intermediate_dir"]
        config.CONFIG.DATA_PROVENANCE_DIR = test_provenance_dir
        config.CONFIG.PROVENANCE_TIMESTAMP = "test_timestamp"
        config.CONFIG.PROJECT_ID = "test_project"
        
        try:
            # Run the main function
            main()
            
            # Verify output file exists
            checksums_file = test_provenance_dir / "checksums.txt"
            assert checksums_file.exists()
            
            # Verify file contains expected content
            content = checksums_file.read_text()
            assert "test_project" in content
            assert "test_timestamp" in content
            assert len(content) > 100  # Should have substantial content
            
            # Verify it contains checksums for our test files
            assert "test_data.csv" in content
            assert "merged.csv" in content
            
        finally:
            # Restore original config
            config.CONFIG.DATA_DIR = original_data_dir
            config.CONFIG.DATA_PROVENANCE_DIR = original_provenance_dir
            config.CONFIG.DATA_RAW_DIR = CONFIG.DATA_RAW_DIR
            config.CONFIG.DATA_INTERMEDIATE_DIR = CONFIG.DATA_INTERMEDIATE_DIR
            config.CONFIG.DATA_PROCESSED_DIR = CONFIG.DATA_PROCESSED_DIR

    def test_checksums_deterministic(self, temp_test_files):
        """Test that running checksum generation twice produces identical results"""
        directories = [temp_test_files["raw_dir"], temp_test_files["intermediate_dir"]]
        
        checksums1 = generate_all_checksums(directories)
        checksums2 = generate_all_checksums(directories)
        
        assert checksums1 == checksums2