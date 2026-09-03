import pytest
from unittest.mock import patch, MagicMock
import logging
import json
from pathlib import Path

# Import the module to test
from code.utils.data_loader import (
    load_dataset_streaming, 
    load_gsm8k_streaming, 
    load_humaneval_streaming,
    load_common_crawl_streaming,
    load_dolly_streaming,
    _log_streaming_config
)

@pytest.fixture
def mock_load_dataset():
    with patch('code.utils.data_loader.load_dataset') as mock:
        # Create a mock iterator that yields a sample
        mock_iterator = iter([{"text": "sample data"}])
        mock.return_value = mock_iterator
        yield mock

def test_load_dataset_streaming_success(mock_load_dataset, caplog):
    """Test that streaming mode is enabled and returns an iterator."""
    with caplog.at_level(logging.INFO):
        result = load_dataset_streaming("test_dataset", split="train", streaming=True)
        
        # Verify load_dataset was called with streaming=True
        mock_load_dataset.assert_called_once_with("test_dataset", split="train", streaming=True)
        
        # Verify result is an iterator
        assert hasattr(result, '__iter__')
        
        # Verify log message
        assert "Attempting to stream dataset" in caplog.text

def test_load_dataset_streaming_failure_raises_error(mock_load_dataset):
    """Test that a fetch failure raises RuntimeError without fallback."""
    mock_load_dataset.side_effect = Exception("Network Error")
    
    with pytest.raises(RuntimeError) as exc_info:
        load_dataset_streaming("test_dataset", split="train", streaming=True)
    
    assert "Failed to load real dataset" in str(exc_info.value)
    assert "Network Error" in str(exc_info.value)

def test_log_streaming_config_creates_file(tmp_path, monkeypatch):
    """Test that logging creates the config file in data/processed."""
    # Monkeypatch the LOG_DIR to use a temporary directory
    import code.utils.data_loader as dl
    original_log_dir = dl.LOG_DIR
    dl.LOG_DIR = tmp_path
    dl.STREAMING_LOG_PATH = tmp_path / "streaming_config.log"
    
    try:
        _log_streaming_config("test_ds", "train", "streaming", 100.0)
        
        log_file = tmp_path / "streaming_config.log"
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            content = f.read().strip()
            entry = json.loads(content)
            
            assert entry["dataset"] == "test_ds"
            assert entry["split"] == "train"
            assert entry["strategy"] == "streaming"
            assert entry["estimated_size_mb"] == 100.0
    finally:
        dl.LOG_DIR = original_log_dir
        dl.STREAMING_LOG_PATH = original_log_dir / "streaming_config.log"

def test_load_gsm8k_streaming(mock_load_dataset):
    """Test GSM8K specific loader calls the generic function correctly."""
    result = load_gsm8k_streaming()
    mock_load_dataset.assert_called_once_with("gsm8k", split="train", streaming=True)
    assert hasattr(result, '__iter__')

def test_load_humaneval_streaming(mock_load_dataset):
    """Test HumanEval specific loader calls the generic function correctly."""
    result = load_humaneval_streaming()
    mock_load_dataset.assert_called_once_with("openai_humaneval", split="test", streaming=True)
    assert hasattr(result, '__iter__')

def test_load_common_crawl_streaming(mock_load_dataset):
    """Test CommonCrawl loader uses correct dataset name."""
    result = load_common_crawl_streaming(subset="cc-en")
    mock_load_dataset.assert_called_once_with("common_crawl/cc-en", split="train", streaming=True)
    assert hasattr(result, '__iter__')

def test_load_dolly_streaming(mock_load_dataset):
    """Test Dolly loader uses correct dataset name."""
    result = load_dolly_streaming()
    mock_load_dataset.assert_called_once_with("databricks/dolly-15k", split="train", streaming=True)
    assert hasattr(result, '__iter__')
