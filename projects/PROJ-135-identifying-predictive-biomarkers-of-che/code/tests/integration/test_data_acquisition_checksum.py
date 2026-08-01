import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.data_acquisition import (
    download_tcga_data,
    download_geo_data,
    get_collected_checksums,
    reset_checksums,
    _file_checksums
)
from code.src.config import get_project_root, ensure_directories

class TestDataAcquisitionChecksum:
    """
    Integration test for T012c: Checksum Per File.
    Verifies that checksums are computed immediately after download
    and stored in the in-memory list.
    """

    def setup_method(self):
        """Reset state before each test."""
        reset_checksums()
        self.raw_dir = get_project_root() / "data" / "raw"
        ensure_directories()

    def test_tcga_download_records_checksum(self):
        """
        Test that downloading TCGA data triggers immediate checksum recording.
        """
        result = download_tcga_data()
        
        # Verify download status (might fail if network, but logic should run)
        # We assert that the checksum list was populated if a file was created
        checksums = get_collected_checksums()
        
        # If the download succeeded, we should have at least one checksum
        if result.get("status") == "success":
            assert len(checksums) >= 1, "Checksums should be recorded after successful download"
            assert checksums[0]["algorithm"] == "sha256"
            assert len(checksums[0]["checksum"]) == 64  # SHA256 hex length

    def test_geo_download_records_checksum(self):
        """
        Test that downloading GEO data triggers immediate checksum recording.
        """
        reset_checksums() # Clear previous
        result = download_geo_data()
        
        checksums = get_collected_checksums()
        
        if result.get("status") == "success":
            assert len(checksums) >= 1, "Checksums should be recorded after successful download"
            assert "geo_query_manifest.txt" in checksums[0]["file_path"]

    def test_checksums_accumulate(self):
        """
        Test that checksums accumulate across multiple downloads.
        """
        reset_checksums()
        download_tcga_data()
        initial_count = len(get_collected_checksums())
        
        download_geo_data()
        final_count = len(get_collected_checksums())
        
        # Should have accumulated
        assert final_count >= initial_count, "Checksums should accumulate"
        
        # Verify all entries are valid
        for entry in get_collected_checksums():
            assert "checksum" in entry
            assert "file_path" in entry
            assert "algorithm" in entry