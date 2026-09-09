import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import hashlib

from src.download import generate_manifest_v1, fetch_viral_genomes
from src.config import DATA_RAW_PATH

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory for raw data to avoid polluting real data/."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the DATA_RAW_PATH config variable temporarily
        original_path = DATA_RAW_PATH
        # We cannot easily mock the imported constant in config, so we patch the function's internal path usage
        # by passing a custom path or ensuring the test runs in a context where DATA_RAW_PATH is valid.
        # For this test, we will patch the Path creation inside generate_manifest_v1
        # Actually, generate_manifest_v1 uses DATA_RAW_PATH from src.config.
        # We will create a temp dir and set an environment variable or mock the config.
        # Simpler: Mock the Path object used in the function.
        
        # Let's just create the dir and ensure it exists, then mock the actual write location
        # to be inside this temp dir.
        yield tmpdir

def test_manifest_v1_structure(temp_raw_dir):
    """Test that generate_manifest_v1 produces the correct JSON structure."""
    accessions = ["GCF_123", "GCF_456"]
    raw_files = [
        ("GCF_123", b">GCF_123\nATCG\n"),
        ("GCF_456", b">GCF_456\nGGCC\n")
    ]
    
    # We need to patch the Path(DATA_RAW_PATH) inside the function to point to temp_raw_dir
    # Since the function uses Path(DATA_RAW_PATH), we can patch the config import or the Path constructor.
    # Easier: Patch the function to use a specific path.
    # But the function is defined with `Path(DATA_RAW_PATH)`.
    # We will patch `src.download.Path` to return a Path in temp_raw_dir when called with DATA_RAW_PATH.
    
    # Actually, let's just call the function and verify the file content if we set up the environment correctly.
    # Since we can't easily change the config constant at runtime without reloading,
    # we will patch the function's internal logic.
    
    # Better approach for this specific test:
    # Mock the `Path` constructor in `src.download` to return a path inside temp_raw_dir.
    mock_path_instance = MagicMock()
    mock_path_instance.parent = MagicMock()
    mock_path_instance.parent.mkdir = MagicMock()
    mock_path_instance.__truediv__ = MagicMock(return_value=Path(temp_raw_dir) / "manifest_v1.json")
    
    with patch('src.download.Path', return_value=mock_path_instance):
        # Also need to mock the open call to capture the content written
        with patch('src.download.open', new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            
            result_path = generate_manifest_v1(accessions, raw_files)
            
            # Verify json.dump was called
            assert mock_file.write.called
            
            # Retrieve the argument passed to json.dump
            call_args = mock_file.write.call_args[0][0]
            content = json.loads(call_args)
            
            assert "accessions" in content
            assert content["accessions"] == accessions
            assert "source" in content
            assert content["source"] == "NCBI Virus"
            assert "timestamp" in content
            assert "version" in content
            assert "checksums" in content
            assert isinstance(content["checksums"], dict)
            assert "GCF_123" in content["checksums"]
            assert "GCF_456" in content["checksums"]

def test_manifest_overwrites_existing(temp_raw_dir):
    """Test that generate_manifest_v1 overwrites existing files (does not append)."""
    accessions = ["GCF_NEW"]
    raw_files = [("GCF_NEW", b">GCF_NEW\nAT\n")]
    
    # Mock Path to use temp_raw_dir
    mock_path_instance = MagicMock()
    mock_path_instance.parent = MagicMock()
    mock_path_instance.parent.mkdir = MagicMock()
    mock_path_instance.__truediv__ = MagicMock(return_value=Path(temp_raw_dir) / "manifest_v1.json")
    
    with patch('src.download.Path', return_value=mock_path_instance):
        with patch('src.download.open', new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            
            generate_manifest_v1(accessions, raw_files)
            
            # Check that open was called with 'w' mode (overwrite)
            mock_open.assert_called_once()
            call_args = mock_open.call_args
            assert call_args[0][1] == 'w'

def test_manifest_checksums_data(temp_raw_dir):
    """Test that checksums are correctly calculated as SHA-256."""
    acc = "GCF_TEST"
    data = b"ATCGATCG"
    expected_hash = hashlib.sha256(data).hexdigest()
    
    raw_files = [(acc, data)]
    accessions = [acc]
    
    mock_path_instance = MagicMock()
    mock_path_instance.parent = MagicMock()
    mock_path_instance.parent.mkdir = MagicMock()
    mock_path_instance.__truediv__ = MagicMock(return_value=Path(temp_raw_dir) / "manifest_v1.json")
    
    with patch('src.download.Path', return_value=mock_path_instance):
        with patch('src.download.open', new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            
            generate_manifest_v1(accessions, raw_files)
            
            call_args = mock_file.write.call_args[0][0]
            content = json.loads(call_args)
            
            assert content["checksums"][acc] == expected_hash

def test_manifest_empty_accessions(temp_raw_dir):
    """Test behavior with empty accessions list."""
    raw_files = []
    accessions = []
    
    mock_path_instance = MagicMock()
    mock_path_instance.parent = MagicMock()
    mock_path_instance.parent.mkdir = MagicMock()
    mock_path_instance.__truediv__ = MagicMock(return_value=Path(temp_raw_dir) / "manifest_v1.json")
    
    with patch('src.download.Path', return_value=mock_path_instance):
        with patch('src.download.open', new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            
            generate_manifest_v1(accessions, raw_files)
            
            call_args = mock_file.write.call_args[0][0]
            content = json.loads(call_args)
            
            assert content["accessions"] == []
            assert content["checksums"] == {}
