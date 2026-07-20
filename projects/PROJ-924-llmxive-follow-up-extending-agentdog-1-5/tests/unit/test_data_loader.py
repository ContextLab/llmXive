import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys_path = Path(__file__).parent.parent.parent / "code"
import sys
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

from data_loader import fetch_taxonomy, verify_checksum
from config import get_path


def test_fetch_taxonomy_structure():
    """
    Test that fetch_taxonomy successfully downloads and saves the OWASP taxonomy.
    This is a unit test that mocks the dataset loading to avoid network dependency in CI,
    but verifies the logic and file saving.
    """
    # Mock the load_dataset function
    mock_data = [
        {"id": "1", "name": "Test Category", "description": "Test Description"},
        {"id": "2", "name": "Another Category", "description": "Another Description"}
    ]
    
    with patch('data_loader.load_dataset') as mock_load:
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_data)
        mock_load.return_value = mock_dataset
        
        # Call the function
        result = fetch_taxonomy()
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Test Category"
        
        # Verify the file was saved
        output_path = get_path("data/raw/taxonomy_owasp.json")
        assert output_path.exists()
        
        # Verify the content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == mock_data

def test_verify_checksum():
    """Test checksum verification logic."""
    # Create a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        # Calculate expected checksum
        import hashlib
        sha256_hash = hashlib.sha256("test content".encode()).hexdigest()
        
        # Test valid checksum
        assert verify_checksum(temp_path, sha256_hash) is True
        
        # Test invalid checksum
        assert verify_checksum(temp_path, "invalid_checksum") is False
    finally:
        os.unlink(temp_path)
