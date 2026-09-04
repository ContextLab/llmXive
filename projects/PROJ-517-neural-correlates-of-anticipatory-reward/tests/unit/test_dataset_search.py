"""
Unit tests for dataset_search.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock the urllib to avoid network calls in tests
from unittest.mock import patch, MagicMock
import urllib.request
import urllib.error

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from dataset_search import verify_url_reachability, search_openneuro, write_candidates

class TestVerifyUrlReachability:
    def test_verify_url_success(self):
        """Test successful URL verification."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            result = verify_url_reachability("http://example.com")
            assert result is True

    def test_verify_url_failure(self):
        """Test failed URL verification."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError("http://example.com", 404, "Not Found", None, None)
            
            result = verify_url_reachability("http://example.com")
            assert result is False

class TestSearchOpenNeuro:
    @patch('urllib.request.urlopen')
    def test_search_returns_candidates(self, mock_urlopen):
        """Test that search returns candidates when API returns valid data."""
        # Mock the GraphQL response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "datasets": {
                    "edges": [
                        {
                            "node": {
                                "id": "ds001172",
                                "label": "Test Dataset",
                                "summary": {
                                    "modality": ["eeg"],
                                    "taskLabels": ["reward"]
                                }
                            }
                        }
                    ]
                }
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Also mock verify_url_reachability to return True
        with patch('dataset_search.verify_url_reachability', return_value=True):
            candidates = search_openneuro()
            assert len(candidates) > 0
            assert candidates[0]["dataset_id"] == "ds001172"

    @patch('urllib.request.urlopen')
    def test_search_filters_non_neurophys(self, mock_urlopen):
        """Test that datasets without neurophys modality are filtered out."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "datasets": {
                    "edges": [
                        {
                            "node": {
                                "id": "ds000001",
                                "label": "FMRI Only",
                                "summary": {
                                    "modality": ["mri"],
                                    "taskLabels": ["reward"]
                                }
                            }
                        },
                        {
                            "node": {
                                "id": "ds001172",
                                "label": "EEG Reward",
                                "summary": {
                                    "modality": ["eeg"],
                                    "taskLabels": ["reward"]
                                }
                            }
                        }
                    ]
                }
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with patch('dataset_search.verify_url_reachability', return_value=True):
            candidates = search_openneuro()
            # Should only return the EEG one
            assert len(candidates) == 1
            assert candidates[0]["dataset_id"] == "ds001172"

class TestWriteCandidates:
    def test_write_candidates_creates_file(self):
        """Test that write_candidates creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            state_dir = tmpdir_path / "state"
            state_dir.mkdir()
            
            # Temporarily override the STATE_DIR
            import dataset_search
            original_state_dir = dataset_search.STATE_DIR
            dataset_search.STATE_DIR = state_dir
            dataset_search.OUTPUT_FILE = state_dir / "dataset_candidates.json"
            
            try:
                candidates = [{"dataset_id": "ds001172", "label": "Test", "url": "http://test.com"}]
                write_candidates(candidates, "test query")
                
                output_file = state_dir / "dataset_candidates.json"
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                assert data["search_query"] == "test query"
                assert len(data["candidates"]) == 1
            finally:
                dataset_search.STATE_DIR = original_state_dir
                dataset_search.OUTPUT_FILE = original_state_dir / "dataset_candidates.json"