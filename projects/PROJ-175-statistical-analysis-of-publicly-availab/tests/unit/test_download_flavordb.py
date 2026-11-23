import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
sys_path = Path(__file__).resolve().parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from code.data.download import download_flavordb_chunked, save_memory_profile, MEMORY_PROFILE_PATH

@pytest.fixture
def mock_hf_hub_download():
    """Mock hf_hub_download to simulate file download without network."""
    with patch('code.data.download.hf_hub_download') as mock:
        # Simulate returning a path in the temp directory
        mock.return_value = "/tmp/mock_flavordb/chemical_matrix.csv"
        yield mock

@pytest.fixture
def mock_list_repo_files():
    """Mock list_repo_files to return expected files."""
    with patch('code.data.download.list_repo_files') as mock:
        mock.return_value = ["chemical_matrix.csv", "ingredient_map.csv"]
        yield mock

@pytest.fixture
def mock_shutil_copy():
    """Mock shutil.copy2."""
    with patch('code.data.download.shutil.copy2') as mock:
        yield mock

@pytest.fixture
def mock_gc_collect():
    """Mock gc.collect."""
    with patch('code.data.download.gc.collect') as mock:
        yield mock

@pytest.fixture
def mock_check_memory_limit():
    """Mock check_memory_limit to always pass."""
    with patch('code.data.download.check_memory_limit', return_value=True):
        pass

def test_flavordb_chunked_download_calls_hf_hub(mock_hf_hub_download, 
                                                mock_list_repo_files, 
                                                mock_shutil_copy,
                                                mock_gc_collect,
                                                mock_check_memory_limit):
    """Test that download_flavordb_chunked calls hf_hub_download for each expected file."""
    files = download_flavordb_chunked()
    
    # Verify list_repo_files was called
    mock_list_repo_files.assert_called_once_with("jnh1994/FlavorDB")
    
    # Verify hf_hub_download was called for both expected files
    assert mock_hf_hub_download.call_count == 2
    calls = mock_hf_hub_download.call_args_list
    
    # Check arguments for the first call (chemical_matrix.csv)
    assert calls[0][1]['repo_id'] == "jnh1994/FlavorDB"
    assert calls[0][1]['filename'] == "chemical_matrix.csv"
    assert calls[0][1]['repo_type'] == "dataset"
    
    # Check arguments for the second call (ingredient_map.csv)
    assert calls[1][1]['repo_id'] == "jnh1994/FlavorDB"
    assert calls[1][1]['filename'] == "ingredient_map.csv"
    assert calls[1][1]['repo_type'] == "dataset"

def test_flavordb_download_handles_memory_limit(mock_hf_hub_download, 
                                                mock_list_repo_files, 
                                                mock_shutil_copy,
                                                mock_check_memory_limit):
    """Test that the function fails loudly if memory limit is exceeded."""
    # Reset the mock to fail on the second call
    mock_check_memory_limit.side_effect = [True, False] # Pass first, fail second
    
    with pytest.raises(MemoryError, match="Memory limit exceeded"):
        download_flavordb_chunked()

def test_memory_profile_generation(tmp_path, monkeypatch):
    """Test that save_memory_profile creates the correct JSON structure."""
    profile_path = tmp_path / "memory_profile_test.json"
    monkeypatch.setattr('code.data.download.MEMORY_PROFILE_PATH', profile_path)
    
    save_memory_profile(
        task_id="T035b",
        dataset="test_dataset",
        mode="chunked",
        rows_processed=100,
        peak_memory_gb=2.5,
        limit_gb=6.0,
        status="success",
        duration_seconds=10.5,
        output_files=["file1.csv"]
    )
    
    assert profile_path.exists()
    with open(profile_path, 'r') as f:
        data = json.load(f)
    
    assert data['task'] == "T035b"
    assert data['dataset'] == "test_dataset"
    assert data['mode'] == "chunked"
    assert data['peak_memory_gb'] == 2.5
    assert data['status'] == "success"
    assert "file1.csv" in data['output_files']