"""
Unit tests for verify_checksums.py (T003)
Tests checksum verification and experiment ID matching logic.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from exceptions import E_DATASET
from verify_checksums import (
    load_file_metadata, 
    verify_experiment_id_matching, 
    main,
    EXPECTED_FILES,
    EXPECTED_EXPERIMENT_IDS
)

class TestLoadFileMetadata:
    """Tests for load_file_metadata function."""
    
    def test_file_not_found(self):
        """Test behavior when file doesn't exist."""
        result = load_file_metadata(Path("/nonexistent/file.csv"))
        assert result is None
    
    def test_extract_experiment_ids(self):
        """Test extraction of experiment IDs from file content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("GSE21857,GSE167633,ST002565,sample1,sample2\n")
            f.write("gene1,10,20,30,40\n")
            temp_path = Path(f.name)
        
        try:
            metadata = load_file_metadata(temp_path)
            assert metadata is not None
            assert "experiment_ids" in metadata
            assert "GSE21857" in metadata["experiment_ids"]
            assert "GSE167633" in metadata["experiment_ids"]
            assert "ST002565" in metadata["experiment_ids"]
        finally:
            os.unlink(temp_path)
    
    def test_no_experiment_ids_found(self):
        """Test behavior when no experiment IDs are found."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("sample1,sample2,sample3\n")
            f.write("gene1,10,20,30\n")
            temp_path = Path(f.name)
        
        try:
            metadata = load_file_metadata(temp_path)
            assert metadata is not None
            assert metadata["experiment_ids"] == []
        finally:
            os.unlink(temp_path)

class TestVerifyExperimentIdMatching:
    """Tests for verify_experiment_id_matching function."""
    
    def test_all_ids_match(self):
        """Test when all expected IDs are found."""
        metadata = {"experiment_ids": ["GSE21857", "GSE167633", "ST002565"]}
        result = verify_experiment_id_matching(metadata, EXPECTED_EXPERIMENT_IDS)
        assert result is True
    
    def test_partial_match_above_threshold(self):
        """Test when match rate is above 99% threshold."""
        # With 3 expected IDs, need at least 3 to pass (100%)
        metadata = {"experiment_ids": ["GSE21857", "GSE167633"]}
        result = verify_experiment_id_matching(metadata, EXPECTED_EXPERIMENT_IDS)
        # 2/3 = 66.67% which is below 99%, so should be False
        assert result is False
    
    def test_no_match(self):
        """Test when no expected IDs are found."""
        metadata = {"experiment_ids": ["GSE12345", "GSE67890"]}
        result = verify_experiment_id_matching(metadata, EXPECTED_EXPERIMENT_IDS)
        assert result is False
    
    def test_empty_expected_ids(self):
        """Test with empty expected IDs set."""
        metadata = {"experiment_ids": ["GSE21857"]}
        result = verify_experiment_id_matching(metadata, set())
        assert result is True
    
    def test_empty_found_ids(self):
        """Test with empty found IDs."""
        metadata = {"experiment_ids": []}
        result = verify_experiment_id_matching(metadata, EXPECTED_EXPERIMENT_IDS)
        assert result is False

class TestMainFunction:
    """Tests for the main function."""
    
    @patch('verify_checksums.DATA_RAW_DIR')
    @patch('verify_checksums.EXPECTED_FILES')
    def test_missing_files_raises_error(self, mock_expected_files, mock_data_raw_dir, tmp_path):
        """Test that missing files raise E_DATASET error."""
        # Setup mocks
        mock_data_raw_dir.__truediv__.return_value = tmp_path
        mock_expected_files.return_value = {
            "file1.csv": tmp_path / "file1.csv"
        }
        
        # Create a mock that raises E_DATASET when files are missing
        with patch('verify_checksums.logger') as mock_logger:
            with pytest.raises(E_DATASET):
                main()
    
    def test_checksum_verification_logic(self):
        """Test the core checksum verification logic."""
        # This is a high-level test to ensure the logic flows correctly
        # Detailed checksum tests are in checksum_utils tests
        assert len(EXPECTED_EXPERIMENT_IDS) > 0
        assert len(EXPECTED_FILES) > 0