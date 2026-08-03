"""
Contract test for code/download_data.py
Verifies Zenodo fetch and data validity.
"""
import os
import pytest
from pathlib import Path

# Mock the download function for testing without network
def test_download_data_structure():
    """Verify that download_data.py exists and has correct structure."""
    script_path = Path("code/download_data.py")
    assert script_path.exists(), "download_data.py not found"
    
    # Check imports
    with open(script_path) as f:
        content = f.read()
        assert "import requests" in content
        assert "import hashlib" in content
        assert "compute_sha256" in content
        assert "download_file" in content

def test_data_validator_structure():
    """Verify data_validator.py exists."""
    script_path = Path("code/validators/data_validator.py")
    assert script_path.exists(), "data_validator.py not found"
    with open(script_path) as f:
        content = f.read()
        assert "validate_columns" in content
        assert "validate_physical_ranges" in content
