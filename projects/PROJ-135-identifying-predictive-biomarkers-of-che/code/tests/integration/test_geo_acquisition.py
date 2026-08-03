"""
Integration tests for GEO data acquisition (T013).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data_acquisition import (
    check_response_labels,
    compute_file_checksum,
    write_checksum_to_state,
    download_geo_data
)
from src.config import get_project_root

class TestGEOAcquisition:
    """Tests for GEO data acquisition logic."""

    def test_check_response_labels_valid(self):
        """Test that valid metadata with response labels is detected."""
        valid_metadata = {
            "title": "Colorectal Cancer Response to Chemotherapy",
            "description": "Patients treated with 5-FU, response measured by RECIST criteria",
            "characteristics": ["Response: CR", "Response: PR"]
        }
        assert check_response_labels(valid_metadata) is True

    def test_check_response_labels_invalid(self):
        """Test that metadata without response labels is rejected."""
        invalid_metadata = {
            "title": "Gene Expression Profiling",
            "description": "General expression study without clinical response data",
            "organism": "Homo sapiens"
        }
        assert check_response_labels(invalid_metadata) is False

    def test_check_response_labels_empty(self):
        """Test that empty metadata is rejected."""
        assert check_response_labels({}) is False
        assert check_response_labels(None) is False

    def test_compute_file_checksum(self):
        """Test checksum computation on a temporary file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data for checksum")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = compute_file_checksum(tmp_path)
            assert isinstance(checksum, str)
            assert len(checksum) == 64 # SHA256 hex length
        finally:
            tmp_path.unlink()

    def test_write_checksum_to_state(self, tmp_path):
        """Test writing checksum to state file."""
        # Mock the project root to use tmp_path
        import src.config
        original_get_root = src.config.get_project_root
        src.config.get_project_root = lambda: tmp_path
        
        try:
            # Ensure state directory exists
            state_dir = tmp_path / "state" / "projects"
            state_dir.mkdir(parents=True, exist_ok=True)
            
            state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
            
            write_checksum_to_state("abc123", "data/raw/geo/test.txt", "geo_real")
            
            assert state_file.exists()
            
            import yaml
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f)
            
            assert "artifact_hashes" in state_data
            assert "geo_real:data/raw/geo/test.txt" in state_data["artifact_hashes"]
            assert state_data["artifact_hashes"]["geo_real:data/raw/geo/test.txt"]["checksum"] == "abc123"
        finally:
            src.config.get_project_root = original_get_root

    def test_download_geo_data_structure(self):
        """
        Test that download_geo_data returns the correct structure.
        Note: This test mocks the actual network call to avoid real downloads in CI.
        We are testing the logic flow and return values.
        """
        # Since we cannot easily mock GEOparse.get_GEO in a pure unit test without complex patching,
        # and the task requires real data fetching, we will test the logic by checking
        # that the function exists and returns a tuple.
        # In a real integration environment, this would fetch real data.
        # For the purpose of this task implementation, we assert the function signature and return type.
        import unittest.mock as mock
        
        # Mock the GEOparse module to simulate a successful download
        with mock.patch('src.data_acquisition.GEOQUERY_AVAILABLE', True):
            with mock.patch('GEOparse.get_GEO') as mock_get_geo:
                # Create a mock GSE object
                mock_gse = mock.MagicMock()
                mock_gse.metadata = {
                    "title": "Test",
                    "description": "Response data present: RECIST"
                }
                mock_get_geo.return_value = mock_gse
                
                # Mock the save_to_file method to create a dummy file
                def mock_save(path):
                    Path(path).write_text("dummy data")
                mock_gse.save_to_file = mock_save
                
                # Mock the checksum function to return a fixed value
                with mock.patch('src.data_acquisition.compute_file_checksum', return_value="fixed_checksum"):
                    total, valid = download_geo_data(["GSE12345"])
                    
                    assert isinstance(total, int)
                    assert isinstance(valid, int)
                    assert total == 1
                    # Since metadata contains "RECIST", valid should be 1
                    assert valid == 1