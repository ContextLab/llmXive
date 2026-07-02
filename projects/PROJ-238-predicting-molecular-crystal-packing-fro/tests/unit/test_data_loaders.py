import pytest
import os
import tempfile
from pathlib import Path

# Mock the requests module to avoid network calls during unit tests
# but ensure the logic is tested against the canonical URL constant
from unittest.mock import patch, MagicMock
import gzip
import io

# Import the module under test
from utils.data_loaders import fetch_cod_sample_ids, CANONICAL_COD_URL

def test_canonical_url_is_correct():
    """Verify that the code uses the specific canonical URL provided in the task."""
    assert "crystallography.net" in CANONICAL_COD_URL
    assert "sample_ids" in CANONICAL_COD_URL
    
@patch('utils.data_loaders.requests.get')
def test_fetch_cod_sample_ids_creates_file(mock_get):
    """Test that the function successfully fetches and writes IDs to a file."""
    # Prepare mock response data
    mock_ids = [f"COD-{i}" for i in range(150)]
    mock_text = "\n".join(mock_ids)
    
    # Simulate gzip content (since the URL is .txt.gz)
    mock_bytes = io.BytesIO()
    with gzip.open(mock_bytes, 'wt', encoding='utf-8') as f:
        f.write(mock_text)
    mock_bytes.seek(0)
    
    mock_response = MagicMock()
    mock_response.content = mock_bytes.read()
    mock_response.raise_for_status = MagicMock()
    
    mock_get.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_ids.txt")
        
        ids = fetch_cod_sample_ids(output_path)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        assert len(lines) == 150
        assert lines == mock_ids
        assert len(ids) == 150

@patch('utils.data_loaders.requests.get')
def test_fetch_cod_sample_ids_handles_empty_response(mock_get):
    """Test that the function raises an error if no IDs are found."""
    mock_response = MagicMock()
    mock_response.content = b"" # Empty response
    mock_response.raise_for_status = MagicMock()
    
    mock_get.return_value = mock_response
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_ids.txt")
        
        with pytest.raises(ValueError, match="No IDs found"):
            fetch_cod_sample_ids(output_path)