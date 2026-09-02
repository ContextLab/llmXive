import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import os

# Add the code directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from spec_update_t008b import update_spec_md

def test_update_spec_md_replaces_text():
    """Test that the update function correctly replaces the target string."""
    original_spec = """
    # Specification Document
    
    ## SC-005 Statistical Validation
    The system must validate results using a bootstrap difference-of-means test (p ≤ 0.05).
    
    ## Other Sections
    """
    
    expected_spec = """
    # Specification Document
    
    ## SC-005 Statistical Validation
    The system must validate results using a descriptive trend analysis.
    
    ## Other Sections
    """
    
    with patch("spec_update_t008b.Path") as mock_path_class:
        mock_path_instance = mock_path_class.return_value
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_text.return_value = original_spec
        
        update_spec_md()
        
        mock_path_instance.write_text.assert_called_once()
        written_content = mock_path_instance.write_text.call_args[0][0]
        
        assert "bootstrap difference-of-means test (p ≤ 0.05)" not in written_content
        assert "descriptive trend analysis" in written_content
        assert written_content == expected_spec

def test_update_spec_md_file_not_found():
    """Test that FileNotFoundError is raised if spec.md is missing."""
    with patch("spec_update_t008b.Path") as mock_path_class:
        mock_path_instance = mock_path_class.return_value
        mock_path_instance.exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            update_spec_md()

def test_update_spec_md_missing_target_text():
    """Test that ValueError is raised if the target text is not found."""
    original_spec = """
    # Specification Document
    
    ## SC-005 Statistical Validation
    The system uses some other method.
    """
    
    with patch("spec_update_t008b.Path") as mock_path_class:
        mock_path_instance = mock_path_class.return_value
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_text.return_value = original_spec
        
        with pytest.raises(ValueError) as excinfo:
            update_spec_md()
        
        assert "Could not find the expected text" in str(excinfo.value)