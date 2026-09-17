import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

# Import the module functions
from scripts.verify_citation import fetch_citation_data, update_state_yaml, main

def test_fetch_citation_data_success():
    """Test that fetch_citation_data returns valid data for the concrete dataset."""
    # We mock the urllib request to avoid network dependency in tests
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b"<html><body>Mocked Content</body></html>"
    
    with patch('scripts.verify_citation.urllib.request.urlopen', return_value=mock_response):
        result = fetch_citation_data()
        
        assert result['status'] == 'verified'
        assert 'concrete' in result['url'].lower()
        assert 'timestamp' in result
        assert 'metadata' in result
        assert result['metadata']['id'] == 165

def test_fetch_citation_data_failure():
    """Test that fetch_citation_data raises an error on network failure."""
    with patch('scripts.verify_citation.urllib.request.urlopen', side_effect=Exception("Network Error")):
        with pytest.raises(Exception):
            fetch_citation_data()

def test_update_state_yaml(tmp_path):
    """Test that update_state_yaml correctly writes to the YAML file."""
    state_file = tmp_path / "state.yaml"
    citation_data = {
        "status": "verified",
        "url": "http://example.com",
        "timestamp": "2023-01-01T00:00:00Z"
    }
    
    # Test with PyYAML available (mocked import check)
    with patch('scripts.verify_citation.yaml') as mock_yaml:
        update_state_yaml(str(state_file), citation_data)
        mock_yaml.dump.assert_called_once()
        
    # Test without PyYAML (fallback)
    with patch('scripts.verify_citation.yaml', side_effect=ImportError()):
        update_state_yaml(str(state_file), citation_data)
        assert state_file.exists()
        content = state_file.read_text()
        assert "uci_citation_verified" in content
        assert "http://example.com" in content

def test_main_integration(tmp_path, caplog):
    """Integration test for the main function."""
    # This test is more of a structural check since it involves file I/O
    # We mock the fetch to ensure it runs without network
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b"<html></html>"
    
    with patch('scripts.verify_citation.fetch_citation_data') as mock_fetch:
        mock_fetch.return_value = {
            "status": "verified",
            "url": "http://test.com",
            "timestamp": "2023-01-01T00:00:00Z",
            "dataset_id": "test",
            "title": "Test",
            "source": "Test",
            "metadata": {}
        }
        with patch('scripts.verify_citation.update_state_yaml') as mock_update:
            # Create temp directories
            data_dir = tmp_path / "data" / "raw"
            state_dir = tmp_path / "state" / "projects"
            data_dir.mkdir(parents=True)
            state_dir.mkdir(parents=True)
            
            # Patch paths
            with patch('scripts.verify_citation.OUTPUT_JSON_PATH', str(data_dir / "test.json")):
                with patch('scripts.verify_citation.STATE_FILE_PATH', str(state_dir / "test.yaml")):
                    exit_code = main()
                    
                    assert exit_code == 0
                    assert mock_fetch.called
                    assert mock_update.called
                    assert (data_dir / "test.json").exists()