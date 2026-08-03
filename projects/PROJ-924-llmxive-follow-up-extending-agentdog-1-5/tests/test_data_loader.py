import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datasets import Dataset

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_loader import (
    LoudFailureError,
    verify_checksum,
    validate_data_integrity,
    load_jsonl_file,
    save_jsonl_file,
    fetch_advbench,
    fetch_hf4,
    fetch_taxonomy
)
from config import get_path

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

def test_verify_checksum(temp_dir):
    """Test checksum verification."""
    # Create a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    # Calculate expected checksum
    import hashlib
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    
    # Verify checksum
    assert verify_checksum(str(test_file), expected) is True
    
    # Verify with wrong checksum
    assert verify_checksum(str(test_file), "wrong_checksum") is False

def test_validate_data_integrity(temp_dir):
    """Test data integrity validation."""
    # Create test file
    test_file = temp_dir / "test.jsonl"
    test_file.write_text('{"text": "test"}\n')
    
    # Create checksums file
    checksums_file = temp_dir / "checksums.json"
    import hashlib
    expected = hashlib.sha256(b'{"text": "test"}\n').hexdigest()
    checksums_file.write_text(json.dumps({"test.jsonl": expected}))
    
    # Validate
    assert validate_data_integrity(str(test_file), str(checksums_file)) is True
    
    # Test with wrong checksum
    checksums_file.write_text(json.dumps({"test.jsonl": "wrong"}))
    with pytest.raises(ValueError):
        validate_data_integrity(str(test_file), str(checksums_file))

def test_load_jsonl_file(temp_dir):
    """Test loading JSONL file."""
    test_file = temp_dir / "test.jsonl"
    test_file.write_text('{"text": "test1"}\n{"text": "test2"}\n')
    
    data = load_jsonl_file(str(test_file))
    assert len(data) == 2
    assert data[0]["text"] == "test1"
    assert data[1]["text"] == "test2"

def test_save_jsonl_file(temp_dir):
    """Test saving JSONL file."""
    test_file = temp_dir / "test.jsonl"
    data = [{"text": "test1"}, {"text": "test2"}]
    
    save_jsonl_file(data, str(test_file))
    
    assert test_file.exists()
    content = test_file.read_text().strip().split('\n')
    assert len(content) == 2
    assert json.loads(content[0]) == {"text": "test1"}

@patch('data_loader.load_dataset')
def test_fetch_advbench_success(mock_load_dataset, temp_dir):
    """Test successful AdvBench fetch."""
    # Mock dataset
    mock_dataset = [
        {"prompt": "Test prompt 1"},
        {"prompt": "Test prompt 2"}
    ]
    mock_load_dataset.return_value = mock_dataset
    
    output_path = str(temp_dir / "advbench.jsonl")
    data = fetch_advbench(output_path)
    
    assert len(data) == 2
    assert all(item["label"] == "jailbreak" for item in data)
    assert os.path.exists(output_path)

@patch('data_loader.load_dataset')
def test_fetch_advbench_failure(mock_load_dataset, temp_dir):
    """Test AdvBench fetch failure."""
    mock_load_dataset.side_effect = Exception("Network error")
    
    output_path = str(temp_dir / "advbench.jsonl")
    
    with pytest.raises(LoudFailureError) as exc_info:
        fetch_advbench(output_path)
    
    assert "Failed to fetch AdvBench dataset" in str(exc_info.value)

@patch('data_loader.load_dataset')
def test_fetch_hf4_success(mock_load_dataset, temp_dir):
    """Test successful HF4 fetch."""
    # Mock dataset
    mock_dataset = [
        {"chosen": [{"content": "Safe response 1"}]},
        {"chosen": [{"content": "Safe response 2"}]}
    ]
    mock_load_dataset.return_value = mock_dataset
    
    output_path = str(temp_dir / "hf4.jsonl")
    data = fetch_hf4(output_path)
    
    assert len(data) == 2
    assert all(item["label"] == "safe" for item in data)
    assert os.path.exists(output_path)

@patch('data_loader.load_dataset')
def test_fetch_hf4_failure(mock_load_dataset, temp_dir):
    """Test HF4 fetch failure."""
    mock_load_dataset.side_effect = Exception("Network error")
    
    output_path = str(temp_dir / "hf4.jsonl")
    
    with pytest.raises(LoudFailureError) as exc_info:
        fetch_hf4(output_path)
    
    assert "Failed to fetch HF4 dataset" in str(exc_info.value)

@patch('data_loader.urllib.request.urlopen')
def test_fetch_taxonomy_success(mock_urlopen, temp_dir):
    """Test successful taxonomy fetch."""
    # Mock response
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"categories": ["cat1", "cat2"]}).encode('utf-8')
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response
    
    output_path = str(temp_dir / "taxonomy.json")
    data = fetch_taxonomy(output_path)
    
    assert "categories" in data
    assert len(data["categories"]) == 2
    assert os.path.exists(output_path)

@patch('data_loader.urllib.request.urlopen')
def test_fetch_taxonomy_failure(mock_urlopen, temp_dir):
    """Test taxonomy fetch failure."""
    mock_urlopen.side_effect = Exception("Network error")
    
    output_path = str(temp_dir / "taxonomy.json")
    
    with pytest.raises(LoudFailureError) as exc_info:
        fetch_taxonomy(output_path)
    
    assert "Failed to fetch taxonomy" in str(exc_info.value)

@patch('data_loader.urllib.request.urlopen')
def test_fetch_taxonomy_fallback(mock_urlopen, temp_dir):
    """Test taxonomy fetch with local fallback."""
    # Mock network failure
    mock_urlopen.side_effect = Exception("Network error")
    
    # Create local fallback
    local_path = str(temp_dir / "taxonomy_agentdog_local.json")
    with open(local_path, 'w') as f:
        json.dump({"local": "data"}, f)
    
    # Patch get_path to return our temp directory
    with patch('data_loader.get_path', return_value=temp_dir):
        data = fetch_taxonomy()
    
    assert "local" in data
    assert data["local"] == "data"
