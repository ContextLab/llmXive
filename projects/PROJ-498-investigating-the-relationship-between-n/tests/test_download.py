import os
import sys
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path if necessary
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.download import (
    compute_sha256,
    generate_data_gap_report,
    query_openneuro_api,
    select_dataset,
    download_dataset
)

class TestDownloadChecksum:
    def test_compute_sha256(self, tmp_path):
        """Test SHA-256 computation on a known file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(str(test_file))
        
        assert actual_hash == expected_hash

class TestDataGapReport:
    def test_generate_data_gap_report(self, tmp_path):
        """Test generation of data gap report JSON."""
        # Mock the logger and ensure_directories
        with patch('code.download.get_logger'), \
             patch('code.download.ensure_directories'):
            
            report_path = tmp_path / "data" / "data_gap_report.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Patch the global path in the module to use tmp_path
            with patch('code.download.Path', return_value=report_path):
                generate_data_gap_report("Test reason", fallback_id="ds000000")
            
            # Verify file exists and content
            assert report_path.exists()
            with open(report_path) as f:
                data = json.load(f)
            
            assert data['reason'] == "Test reason"
            assert data['fallback_id'] == "ds000000"
            assert data['dataset_id'] is None
            assert 'timestamp' in data

class TestSelectDataset:
    def test_select_preferred(self):
        """Test selection of preferred dataset."""
        datasets = [
            {"id": "ds001", "name": "Dataset 1"},
            {"id": "ds002", "name": "Dataset 2"}
        ]
        
        selected = select_dataset(datasets, preferred_id="ds002")
        assert selected['id'] == "ds002"
    
    def test_select_first(self):
        """Test selection of first dataset when no preference."""
        datasets = [
            {"id": "ds001", "name": "Dataset 1"},
            {"id": "ds002", "name": "Dataset 2"}
        ]
        
        selected = select_dataset(datasets)
        assert selected['id'] == "ds001"
    
    def test_empty_list(self):
        """Test selection with empty list."""
        selected = select_dataset([])
        assert selected is None

class TestQueryOpenNeuro:
    @patch('code.download.urllib.request.urlopen')
    def test_query_success(self, mock_urlopen):
        """Test successful API query."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "datasets": {
                    "edges": [
                        {"node": {"id": "ds001", "name": "Test"}}
                    ]
                }
            }
        }).encode('utf-8')
        mock_urlopen.return_value = mock_response
        
        datasets = query_openneuro_api("task-switching")
        assert len(datasets) == 1
        assert datasets[0]['id'] == "ds001"

    @patch('code.download.urllib.request.urlopen')
    def test_query_failure(self, mock_urlopen):
        """Test API query failure."""
        mock_urlopen.side_effect = Exception("Network error")
        
        datasets = query_openneuro_api("task-switching")
        assert datasets == []