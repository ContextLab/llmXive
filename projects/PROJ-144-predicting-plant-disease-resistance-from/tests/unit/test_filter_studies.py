"""
Unit tests for T013c (filter_studies.py).
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
CODE_DIR = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from data.filter_studies import load_manifest, fetch_phenotype_metadata, has_resistance_metadata, filter_studies, save_filtered_manifest, MANIFEST_PATH, FILTERED_MANIFEST_PATH

@pytest.fixture
def temp_manifest_dir():
    """Creates a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create necessary directories
        raw_dir = Path(tmpdir) / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        # Set global paths for the module
        import data.filter_studies as fs
        fs.DATA_RAW_DIR = raw_dir
        fs.MANIFEST_PATH = raw_dir / "study_manifest.json"
        fs.FILTERED_MANIFEST_PATH = raw_dir / "filtered_study_manifest.json"
        
        yield raw_dir

def test_load_manifest_file_not_found(temp_manifest_dir):
    """Test that load_manifest raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_manifest()

def test_load_manifest_success(temp_manifest_dir):
    """Test loading a valid manifest."""
    manifest_data = [{"study_id": "P001", "title": "Test"}]
    with open(temp_manifest_dir / "study_manifest.json", 'w') as f:
        json.dump(manifest_data, f)
    
    result = load_manifest()
    assert result == manifest_data

@patch('data.filter_studies.requests.get')
def test_fetch_phenotype_metadata_success(mock_get, temp_manifest_dir):
    """Test successful metadata fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "phenotype": [
            {"column": "resistance_score", "values": [1, 0]}
        ]
    }
    mock_get.return_value = mock_response
    
    result = fetch_phenotype_metadata("P001")
    assert result is not None
    assert "phenotype" in result
    mock_get.assert_called_once()

@patch('data.filter_studies.requests.get')
def test_fetch_phenotype_metadata_failure(mock_get, temp_manifest_dir):
    """Test failed metadata fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    result = fetch_phenotype_metadata("P001")
    assert result is None

def test_has_resistance_metadata_positive(temp_manifest_dir):
    """Test detection of resistance metadata."""
    # Mock the fetch function to return data with resistance column
    with patch('data.filter_studies.fetch_phenotype_metadata') as mock_fetch:
        mock_fetch.return_value = {
            "phenotype": [{"column": "resistance_score"}]
        }
        assert has_resistance_metadata("P001") is True

def test_has_resistance_metadata_negative(temp_manifest_dir):
    """Test detection of missing resistance metadata."""
    with patch('data.filter_studies.fetch_phenotype_metadata') as mock_fetch:
        mock_fetch.return_value = {
            "phenotype": [{"column": "other_data"}]
        }
        assert has_resistance_metadata("P001") is False

def test_filter_studies(temp_manifest_dir):
    """Test filtering logic."""
    manifest = [
        {"study_id": "P001"},
        {"study_id": "P002"},
        {"study_id": "P003"}
    ]
    with open(temp_manifest_dir / "study_manifest.json", 'w') as f:
        json.dump(manifest, f)
    
    # Mock filtering functions
    with patch('data.filter_studies.has_resistance_metadata') as mock_res, \
         patch('data.filter_studies.has_temporal_metadata') as mock_temp:
        
        # P001: Yes/Yes -> Included
        # P002: No/Yes -> Excluded
        # P003: Yes/No -> Excluded
        mock_res.side_effect = lambda x: x == "P001"
        mock_temp.side_effect = lambda x: x == "P001"
        
        filtered = filter_studies(manifest)
        assert len(filtered) == 1
        assert filtered[0]['study_id'] == "P001"
        assert filtered[0]['filter_status'] == 'included'

def test_save_filtered_manifest(temp_manifest_dir):
    """Test saving the filtered manifest."""
    studies = [{"study_id": "P001", "filter_status": "included"}]
    save_filtered_manifest(studies, temp_manifest_dir / "filtered_study_manifest.json")
    
    assert (temp_manifest_dir / "filtered_study_manifest.json").exists()
    with open(temp_manifest_dir / "filtered_study_manifest.json", 'r') as f:
        data = json.load(f)
    assert data == studies