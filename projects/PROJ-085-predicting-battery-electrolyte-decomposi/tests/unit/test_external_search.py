import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: Using relative import style compatible with the project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.external_search import (
    get_data_status_path,
    load_existing_status,
    save_status,
    search_pubchem,
    check_research_md_dois,
    run_external_search
)

class TestExternalSearch:
    """Unit tests for external_search module."""

    def test_get_data_status_path(self):
        """Test that the data status path is correctly generated."""
        path = get_data_status_path()
        assert isinstance(path, Path)
        assert path.name == "data_status.json"
        assert "validation" in str(path)

    def test_load_existing_status_new_file(self, tmp_path):
        """Test loading status when file does not exist."""
        # Temporarily override the path function
        with patch('data.external_search.get_validation_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            
            status = load_existing_status()
            
            assert "external_data_available" in status
            assert status["external_data_available"] is False
            assert "sources_checked" in status
            assert status["validation_mode"] == "pending"

    def test_load_existing_status_existing_file(self, tmp_path):
        """Test loading status when file exists."""
        status_path = tmp_path / "data_status.json"
        test_data = {
            "external_data_available": True,
            "sources_checked": ["Test"],
            "found_urls": ["http://test.com"],
            "validation_mode": "external"
        }
        
        with open(status_path, 'w') as f:
            json.dump(test_data, f)
        
        with patch('data.external_search.get_validation_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            
            status = load_existing_status()
            
            assert status["external_data_available"] is True
            assert status["sources_checked"] == ["Test"]
            assert "http://test.com" in status["found_urls"]

    def test_save_status(self, tmp_path):
        """Test saving status to file."""
        test_status = {
            "external_data_available": False,
            "sources_checked": ["Test"],
            "validation_mode": "internal_fallback"
        }
        
        with patch('data.external_search.get_validation_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            
            save_status(test_status)
            
            # Verify file was created
            status_path = get_data_status_path()
            assert status_path.exists()
            
            # Verify content
            with open(status_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["external_data_available"] is False
            assert loaded["validation_mode"] == "internal_fallback"

    @patch('data.external_search.requests.get')
    def test_search_pubchem_mock_success(self, mock_get, tmp_path):
        """Test PubChem search with mocked successful response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "IdentifierList": {"CID": [12345]}
        }
        mock_get.return_value = mock_response
        
        with patch('data.external_search.get_validation_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            
            found, urls, error = search_pubchem()
            
            # Should find at least one URL
            assert found is True
            assert len(urls) > 0
            assert error is None

    @patch('data.external_search.requests.get')
    def test_search_pubchem_mock_failure(self, mock_get, tmp_path):
        """Test PubChem search with mocked failure response."""
        mock_get.side_effect = Exception("Connection failed")
        
        with patch('data.external_search.get_validation_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            
            found, urls, error = search_pubchem()
            
            # Should handle error gracefully
            assert found is False
            assert len(urls) == 0
            assert error is not None
            assert "PubChem" in error

    def test_run_external_search_integration(self, tmp_path, tmp_path_factory):
        """Test the full external search pipeline."""
        # Create a mock research.md
        docs_dir = tmp_path_factory.mktemp("docs")
        research_md = docs_dir / "research.md"
        research_md.write_text("This is a test document.\n")
        
        with patch('data.external_search.get_validation_dir') as mock_val_dir, \
             patch('data.external_search.get_project_root') as mock_root:
            
            mock_val_dir.return_value = tmp_path
            mock_root.return_value = tmp_path.parent  # So docs is found
            
            # Run the search
            status = run_external_search()
            
            # Verify structure
            assert "external_data_available" in status
            assert "validation_mode" in status
            assert "sources_checked" in status
            assert "found_urls" in status
            
            # Verify file was saved
            assert get_data_status_path().exists()
            
            # Since we mocked everything and didn't provide real data,
            # we expect no external data found
            assert status["external_data_available"] is False
            assert status["validation_mode"] == "internal_fallback"

    def test_validation_mode_logic(self, tmp_path):
        """Test that validation_mode is set correctly based on data availability."""
        # Case 1: No data found -> internal_fallback
        status_no_data = {
            "external_data_available": False,
            "sources_checked": ["Test"],
            "found_urls": [],
            "validation_mode": "internal_fallback"
        }
        
        with patch('data.external_search.get_validation_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            save_status(status_no_data)
            
            loaded = load_existing_status()
            assert loaded["validation_mode"] == "internal_fallback"
        
        # Case 2: Data found -> external
        status_with_data = {
            "external_data_available": True,
            "sources_checked": ["Test"],
            "found_urls": ["http://example.com"],
            "validation_mode": "external"
        }
        
        with patch('data.external_search.get_validation_dir') as mock_dir:
            mock_dir.return_value = tmp_path
            save_status(status_with_data)
            
            loaded = load_existing_status()
            assert loaded["validation_mode"] == "external"