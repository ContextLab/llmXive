import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data_ingestion import (
    download_with_backoff,
    compute_dataset_hash,
    save_dataset_metadata,
    filter_python_snippets,
    ingest_codesearchnet,
    ingest_codegen,
    verify_datasets,
    run_ingestion_pipeline
)
from code.checksum import register_dataset_checksum

@pytest.fixture
def mock_dataset():
    """Create a mock dataset object."""
    mock = MagicMock()
    mock.__len__ = lambda self: 100
    mock.__getitem__ = lambda self, idx: {
        "language": "python",
        "code": f"def test_func_{idx}():\n    pass",
        "repo": f"repo_{idx}"
    }
    return mock

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_download_with_backoff_success(mock_dataset):
    """Test successful download with backoff."""
    with patch('code.data_ingestion.load_dataset', return_value=mock_dataset):
        result = download_with_backoff("test_dataset", split="train")
        assert result == mock_dataset

def test_download_with_backoff_retry():
    """Test download with retries."""
    mock_dataset = MagicMock()
    mock_dataset.__len__ = lambda self: 100
    mock_dataset.__getitem__ = lambda self, idx: {"language": "python", "code": "pass"}
    
    call_count = 0
    def mock_load(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Network error")
        return mock_dataset
    
    with patch('code.data_ingestion.load_dataset', side_effect=mock_load):
        with patch('code.data_ingestion.time.sleep'):  # Skip actual sleep
            result = download_with_backoff("test_dataset", split="train")
            assert result == mock_dataset
            assert call_count == 3

def test_compute_dataset_hash(mock_dataset):
    """Test dataset hash computation."""
    hash_val = compute_dataset_hash(mock_dataset, "test")
    assert len(hash_val) == 64  # SHA-256 hex length
    assert isinstance(hash_val, str)

def test_save_dataset_metadata(temp_dir):
    """Test saving dataset metadata."""
    metadata_path = temp_dir / "metadata.json"
    save_dataset_metadata("test_dataset", "train", "abc123", metadata_path)
    
    assert metadata_path.exists()
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    assert data["dataset_name"] == "test_dataset"
    assert data["split"] == "train"
    assert data["hash"] == "abc123"

def test_filter_python_snippets(mock_dataset):
    """Test filtering to Python snippets."""
    snippets = filter_python_snippets(mock_dataset)
    assert len(snippets) == 100
    assert all(s["language"] == "python" for s in snippets)
    assert all("code" in s for s in snippets)

def test_filter_python_snippets_non_python():
    """Test filtering excludes non-Python code."""
    mock = MagicMock()
    mock.__len__ = lambda self: 10
    mock.__getitem__ = lambda self, idx: {
        "language": "javascript",
        "code": "function test() {}"
    }
    
    snippets = filter_python_snippets(mock)
    assert len(snippets) == 0

def test_ingest_codesearchnet(temp_dir):
    """Test CodeSearchNet ingestion."""
    mock_dataset = MagicMock()
    mock_dataset.__len__ = lambda self: 50
    mock_dataset.__getitem__ = lambda self, idx: {
        "language": "python",
        "code": f"def func_{idx}(): pass",
        "repo": "test_repo"
    }
    
    with patch('code.data_ingestion.load_dataset', return_value=mock_dataset):
        with patch('code.data_ingestion.compute_dataset_hash', return_value="test_hash"):
            with patch('code.data_ingestion.register_dataset_checksum'):
                snippets, hash_val = ingest_codesearchnet(temp_dir)
                
                assert len(snippets) == 50
                assert hash_val == "test_hash"
                assert (temp_dir / "codesearchnet_raw.json").exists()

def test_verify_datasets_success(temp_dir):
    """Test successful dataset verification."""
    verified_path = temp_dir / "verified_sources.json"
    with open(verified_path, 'w') as f:
        json.dump({
            "code_search_net": {"verified": True},
            "codeparrot/codegen": {"verified": True}
        }, f)
    
    assert verify_datasets(temp_dir) is True

def test_verify_datasets_missing(temp_dir):
    """Test verification fails for missing dataset."""
    verified_path = temp_dir / "verified_sources.json"
    with open(verified_path, 'w') as f:
        json.dump({
            "code_search_net": {"verified": True}
            # Missing codeparrot/codegen
        }, f)
    
    assert verify_datasets(temp_dir) is False

def test_run_ingestion_pipeline(temp_dir):
    """Test full ingestion pipeline."""
    mock_dataset = MagicMock()
    mock_dataset.__len__ = lambda self: 10
    mock_dataset.__getitem__ = lambda self, idx: {
        "language": "python",
        "code": f"def func_{idx}(): pass",
        "repo": "test_repo"
    }
    
    with patch('code.data_ingestion.load_dataset', return_value=mock_dataset):
        with patch('code.data_ingestion.compute_dataset_hash', return_value="test_hash"):
            with patch('code.data_ingestion.register_dataset_checksum'):
                with patch('code.data_ingestion.verify_datasets', return_value=True):
                    results = run_ingestion_pipeline(temp_dir)
                    
                    assert results["codesearchnet"]["success"] is True
                    assert results["codegen"]["success"] is True
                    assert results["verification_passed"] is True
                    assert results["codesearchnet"]["snippets"] == 10
                    assert results["codegen"]["snippets"] == 10