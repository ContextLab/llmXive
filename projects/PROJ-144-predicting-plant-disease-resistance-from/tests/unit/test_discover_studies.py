import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# Import the module functions
from code.data.discover_studies import search_plant_metabolomics_studies, save_study_manifest, main

@patch('code.data.discover_studies.requests.get')
def test_search_plant_metabolomics_studies(mock_get):
    """Test that the search function correctly parses the API response."""
    # Mock response data
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "STUDIES": [
            {"STUDY_ID": "C0001", "TITLE": "Test Plant Study 1", "DOWNLOAD_URL": "http://example.com/1"},
            {"STUDY_ID": "C0002", "TITLE": "Test Plant Study 2", "DOWNLOAD_URL": "http://example.com/2"}
        ]
    }
    mock_get.return_value = mock_response

    studies = search_plant_metabolomics_studies()

    assert len(studies) == 2
    assert studies[0]["study_id"] == "C0001"
    assert studies[0]["title"] == "Test Plant Study 1"
    assert studies[0]["download_url"] == "http://example.com/1"
    
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "subject_type" in kwargs.get("params", {})
    assert kwargs["params"]["subject_type"] == "plant"

@patch('code.data.discover_studies.requests.get')
def test_search_handles_empty_response(mock_get):
    """Test handling of empty study list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"STUDIES": []}
    mock_get.return_value = mock_response

    studies = search_plant_metabolomics_studies()
    assert len(studies) == 0

@patch('code.data.discover_studies.requests.get')
def test_search_handles_list_response(mock_get):
    """Test handling of response that is a list directly."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"STUDY_ID": "C0003", "TITLE": "List Format Study", "DOWNLOAD_URL": "http://example.com/3"}
    ]
    mock_get.return_value = mock_response

    studies = search_plant_metabolomics_studies()
    assert len(studies) == 1
    assert studies[0]["study_id"] == "C0003"

def test_save_study_manifest():
    """Test that the manifest is saved correctly to disk."""
    studies = [
        {"study_id": "C0001", "title": "Test", "download_url": "http://example.com"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "manifest.json")
        save_study_manifest(studies, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 1
        assert loaded[0]["study_id"] == "C0001"

@patch('code.data.discover_studies.requests.get')
@patch('code.data.discover_studies.save_study_manifest')
@patch('code.data.discover_studies.sys.exit')
def test_main_success(mock_exit, mock_save, mock_get):
    """Test main function execution on success."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"STUDIES": [{"STUDY_ID": "C0001", "TITLE": "T", "DOWNLOAD_URL": "U"}]}
    mock_get.return_value = mock_response
    
    main()
    
    mock_get.assert_called_once()
    mock_save.assert_called_once()
    mock_exit.assert_not_called()

@patch('code.data.discover_studies.requests.get')
@patch('code.data.discover_studies.sys.exit')
def test_main_failure(mock_exit, mock_get):
    """Test main function execution on failure."""
    mock_get.side_effect = RuntimeError("Network error")
    
    # Redirect stdout to capture print
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        main()
    
    mock_exit.assert_called_once_with(1)
