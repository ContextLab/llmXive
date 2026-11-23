"""
Unit tests for T004a: Resolve Zenodo ID.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We will test the logic by mocking file contents
# Since the actual resolve_zenodo_id.py logic is simple string extraction,
# we test the extraction logic directly.

def test_extract_zenodo_from_doi():
    """Test extraction from a DOI URL."""
    from code.resolve_zenodo_id import extract_zenodo_id
    
    # Create a mock Path object
    mock_path = MagicMock()
    mock_path.read_text.return_value = """
    # Molecular Properties Project
    Dataset: Barrier heights from Zenodo.
    URL: https://doi.org/10.5281/zenodo.1234567
    """
    
    result = extract_zenodo_id(mock_path)
    assert result is not None
    assert result[0] == "1234567"
    assert result[1] == "https://doi.org/10.5281/zenodo.1234567"

def test_extract_zenodo_from_id_string():
    """Test extraction from a plain ID string."""
    from code.resolve_zenodo_id import extract_zenodo_id
    
    mock_path = MagicMock()
    mock_path.read_text.return_value = """
    # Molecular Properties Project
    Zenodo ID: 9876543
    """
    
    result = extract_zenodo_id(mock_path)
    assert result is not None
    assert result[0] == "9876543"
    assert "zenodo.9876543" in result[1]

def test_no_zenodo_found():
    """Test behavior when no Zenodo ID is found."""
    from code.resolve_zenodo_id import extract_zenodo_id
    
    mock_path = MagicMock()
    mock_path.read_text.return_value = """
    # Molecular Properties Project
    Some random text without IDs.
    """
    
    result = extract_zenodo_id(mock_path)
    assert result is None