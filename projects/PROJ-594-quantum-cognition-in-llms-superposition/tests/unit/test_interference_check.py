import os
import sys
import json
import tempfile
import pytest
import torch

# Add project root to path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from code.analysis.interference_check import (
    load_cross_term_data,
    verify_negative_cross_terms,
    save_results
)

def test_verify_negative_cross_terms():
    """Test that verify_negative_cross_terms correctly identifies negative values."""
    # Mock data with some negative values
    mock_data = {
        "cross_term_values": [1.5, -2.3, 0.5, -0.1, 3.0],
        "ambiguous_indices": [0, 1, 2, 3, 4]
    }
    
    result = verify_negative_cross_terms(mock_data)
    
    assert result["min_cross_term"] == -2.3
    assert result["percentage_negative"] == 0.4  # 2 out of 5
    assert result["valid"] is True

def test_verify_negative_cross_terms_all_positive():
    """Test that valid is False when no negative values exist."""
    mock_data = {
        "cross_term_values": [1.5, 2.3, 0.5, 0.1, 3.0],
        "ambiguous_indices": [0, 1, 2, 3, 4]
    }
    
    result = verify_negative_cross_terms(mock_data)
    
    assert result["min_cross_term"] == 0.1
    assert result["percentage_negative"] == 0.0
    assert result["valid"] is False

def test_verify_negative_cross_terms_empty():
    """Test handling of empty list."""
    mock_data = {
        "cross_term_values": [],
        "ambiguous_indices": []
    }
    
    result = verify_negative_cross_terms(mock_data)
    
    assert result["min_cross_term"] == 0.0
    assert result["percentage_negative"] == 0.0
    assert result["valid"] is False

def test_load_cross_term_data_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_cross_term_data("non_existent_file.json")

def test_save_results():
    """Test that save_results writes valid JSON."""
    test_data = {
        "min_cross_term": -1.0,
        "percentage_negative": 0.5,
        "valid": True
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.json")
        save_results(test_data, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == test_data