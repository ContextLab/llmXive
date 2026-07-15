import os
import sys
import tempfile
import csv
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open
import io

# Add project root to path if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.ingest import (
    fetch_dst_indices, 
    write_dst_data, 
    update_manifest_entry, 
    load_manifest,
    save_manifest,
    MANIFEST_PATH,
    DATA_RAW_DIR
)

# Mock data sample for Dst
MOCK_DST_CONTENT = """# Dst Index Data
# Year Month Day Hour Min Dst
2023 1 1 0 0 -10.5
2023 1 1 1 0 -12.3
2023 1 1 2 0 -15.0
# Comment line to ignore
2023 1 1 3 0 -20.1
"""

def test_fetch_dst_indices_parses_correctly():
    """Test that fetch_dst_indices correctly parses the raw text format."""
    with patch('code.ingest.connect_to_swpc') as mock_connect:
        # Setup mock FTP
        mock_ftp = MagicMock()
        mock_ftp.size.return_value = 1024
        mock_ftp.retrbinary = MagicMock(side_effect=lambda cmd, callback: callback(MOCK_DST_CONTENT.encode()))
        mock_ftp.quit = MagicMock()
        mock_connect.return_value = mock_ftp

        data = fetch_dst_indices()
        
        assert len(data) == 4
        assert data[0]['year'] == 2023
        assert data[0]['month'] == 1
        assert data[0]['day'] == 1
        assert data[0]['hour'] == 0
        assert data[0]['dst'] == -10.5
        assert data[3]['dst'] == -20.1

def test_write_dst_data_creates_csv():
    """Test that write_dst_data creates a valid CSV file."""
    test_data = [
        {'year': 2023, 'month': 1, 'day': 1, 'hour': 0, 'minute': 0, 'dst': -10.5},
        {'year': 2023, 'month': 1, 'day': 1, 'hour': 1, 'minute': 0, 'dst': -12.3},
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_dst.csv"
        write_dst_data(test_data, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['dst'] == '-10.5'
            assert rows[1]['dst'] == '-12.3'

def test_update_manifest_entry():
    """Test that update_manifest_entry correctly updates the manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override MANIFEST_PATH for this test
        test_manifest_path = Path(tmpdir) / "manifest.yaml"
        
        # Patch the global variable in the module
        import code.ingest as ingest_module
        original_path = ingest_module.MANIFEST_PATH
        ingest_module.MANIFEST_PATH = test_manifest_path
        
        try:
            # Initialize empty manifest
            ingest_module.save_manifest({"sources": {}})
            
            update_manifest_entry("TEST_SRC", "Success", {"key": "value"})
            
            manifest = ingest_module.load_manifest()
            assert "TEST_SRC" in manifest["sources"]
            assert manifest["sources"]["TEST_SRC"]["status"] == "Success"
            assert manifest["sources"]["TEST_SRC"]["details"]["key"] == "value"
        finally:
            # Restore original path
            ingest_module.MANIFEST_PATH = original_path