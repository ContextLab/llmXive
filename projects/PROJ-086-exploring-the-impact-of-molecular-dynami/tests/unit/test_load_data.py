"""
Unit tests for code/analysis/load_data.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from code.analysis import load_data
from utils.io import write_json

# Mock data for testing
MOCK_INDEX_CONTENT = """
# PDB ID  Resolution  Year
1J22      1.80        2000
2HQP      2.10        2001
3K1A      1.95        2002
4XYZ      2.50        2003
5ABC      1.50        2004
"""

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('code.analysis.load_data.requests.get')
@patch('code.analysis.load_data.PDBParser')
def test_subsample_complexes_success(mock_parser, mock_get, temp_output_dir):
    """
    Test successful subsampling when valid data is available.
    """
    # Mock the index fetch
    mock_index_response = MagicMock()
    mock_index_response.status_code = 200
    mock_index_response.content = b"1J22 1.80\n3K1A 1.95\n5ABC 1.50\n" # Simplified content
    
    # Mock the PDB fetch response
    mock_pdb_response = MagicMock()
    mock_pdb_response.status_code = 200
    mock_pdb_response.content = b"HEADER TEST\nATOM   1  N   ALA A   1      10.000  10.000  10.000  1.00  0.00           N\nEND\n"

    # Setup mock for requests.get
    def side_effect(url, *args, **kwargs):
        if "index.refined" in url:
            return mock_index_response
        elif "rcsb.org" in url:
            return mock_pdb_response
        return MagicMock(status_code=404)

    mock_get.side_effect = side_effect

    # Setup mock PDB structure
    mock_structure = MagicMock()
    mock_model = MagicMock()
    mock_chain = MagicMock()
    mock_residue = MagicMock()
    mock_residue.get_resname.return_value = "ALA"
    
    # Configure the chain iterator to yield one residue
    mock_chain.__iter__ = lambda self: iter([mock_residue])
    mock_model.__iter__ = lambda self: iter([mock_chain])
    mock_structure.__iter__ = lambda self: iter([mock_model])
    
    mock_parser.return_value.get_structure.return_value = mock_structure

    output_path = temp_output_dir / "test_subsample.json"

    # Run the function
    result = load_data.subsample_complexes(target_count=2, output_path=output_path)

    assert len(result) == 2
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert all(item['status'] == 'validated' for item in data)

@patch('code.analysis.load_data.requests.get')
def test_fetch_pdbbind_index_failure(mock_get, temp_output_dir):
    """
    Test handling of index fetch failure.
    """
    mock_get.side_effect = Exception("Network error")
    
    result = load_data.fetch_pdbbind_index()
    assert result is None

@patch('code.analysis.load_data.requests.get')
def test_validate_complex_missing_file(mock_get, temp_output_dir):
    """
    Test validation when file is missing.
    """
    # Mock fetch to return success but file is not actually created (simulated)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"test"
    mock_get.return_value = mock_response

    # Create a fake path that doesn't exist
    fake_path = temp_output_dir / "nonexistent.pdb"
    
    result = load_data.validate_complex("1J22", fake_path)
    assert result is False

@patch('code.analysis.load_data.requests.get')
def test_subsample_complexes_no_valid_results(mock_get, temp_output_dir):
    """
    Test when no complexes meet the criteria.
    """
    # Mock index with high resolution only
    mock_index_response = MagicMock()
    mock_index_response.status_code = 200
    mock_index_response.content = b"1BAD 2.50\n2BAD 3.00\n"
    
    mock_get.side_effect = lambda url: mock_index_response if "index" in url else MagicMock(status_code=404)

    result = load_data.subsample_complexes(target_count=5, output_path=temp_output_dir / "empty.json")
    
    assert result == []
    assert not (temp_output_dir / "empty.json").exists()

@patch('code.analysis.load_data.requests.get')
def test_subsample_complexes_high_res_filter(mock_get, temp_output_dir):
    """
    Test that complexes with resolution > 2.0 are filtered out.
    """
    # Mock index with mixed resolutions
    mock_index_response = MagicMock()
    mock_index_response.status_code = 200
    mock_index_response.content = b"1GOOD 1.80\n2BAD 2.50\n3GOOD 1.90\n"
    
    # Mock PDB fetch to succeed for all
    mock_pdb_response = MagicMock()
    mock_pdb_response.status_code = 200
    mock_pdb_response.content = b"HEADER\nATOM\nEND"

    def side_effect(url, *args, **kwargs):
        if "index" in url:
            return mock_index_response
        elif "rcsb" in url:
            return mock_pdb_response
        return MagicMock(status_code=404)
    
    mock_get.side_effect = side_effect

    # Mock PDB structure to pass validation
    mock_structure = MagicMock()
    mock_model = MagicMock()
    mock_chain = MagicMock()
    mock_residue = MagicMock()
    mock_residue.get_resname.return_value = "ALA"
    mock_chain.__iter__ = lambda self: iter([mock_residue])
    mock_model.__iter__ = lambda self: iter([mock_chain])
    mock_structure.__iter__ = lambda self: iter([mock_model])
    
    # Patch PDBParser inside the module
    with patch('code.analysis.load_data.PDBParser') as mock_parser:
        mock_parser.return_value.get_structure.return_value = mock_structure
        
        result = load_data.subsample_complexes(target_count=10, output_path=temp_output_dir / "filtered.json")
        
        # Should only get the two good ones
        assert len(result) == 2
        pdb_ids = [item['pdb_id'] for item in result]
        assert '1GOOD' in pdb_ids
        assert '3GOOD' in pdb_ids
        assert '2BAD' not in pdb_ids
