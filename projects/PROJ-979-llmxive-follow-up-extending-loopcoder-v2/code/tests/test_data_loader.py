import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import json

# Import functions to test
from src.data_loader import (
    ensure_directories,
    compute_sha256,
    determine_strata,
    stratified_sample,
    save_strata_log,
    save_processed_split,
    save_checksums,
    DATASETS_CONFIG
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

@pytest.fixture
def mock_dataset():
    """Create a mock dataset object."""
    data = [
        {"task_id": "1", "difficulty": "easy", "prompt": "Hello"},
        {"task_id": "2", "difficulty": "easy", "prompt": "World"},
        {"task_id": "3", "difficulty": "medium", "prompt": "Foo"},
        {"task_id": "4", "difficulty": "medium", "prompt": "Bar"},
        {"task_id": "5", "difficulty": "hard", "prompt": "Baz"},
        {"task_id": "6", "difficulty": "hard", "prompt": "Qux"},
        {"task_id": "7", "difficulty": "hard", "prompt": "Quux"},
        {"task_id": "8", "difficulty": "hard", "prompt": "Quuz"},
        {"task_id": "9", "difficulty": "hard", "prompt": "Corge"},
        {"task_id": "10", "difficulty": "hard", "prompt": "Grault"},
    ]
    # Mock dataset object with to_pandas method
    mock_ds = MagicMock()
    mock_ds.__len__ = lambda self: len(data)
    mock_ds.__getitem__ = lambda self, i: data[i]
    mock_ds.column_names = ["task_id", "difficulty", "prompt"]
    mock_ds.to_pandas = MagicMock(return_value=MagicMock(to_dict=MagicMock(return_value=data)))
    return mock_ds

def test_ensure_directories(temp_dir):
    """Test that ensure_directories creates the necessary folders."""
    # Mock the global paths to use temp_dir
    import src.data_loader as dl
    original_raw = dl.DATA_RAW_DIR
    original_processed = dl.DATA_PROCESSED_DIR
    
    dl.DATA_RAW_DIR = temp_dir / "raw"
    dl.DATA_PROCESSED_DIR = temp_dir / "processed"
    
    try:
        ensure_directories()
        assert dl.DATA_RAW_DIR.exists()
        assert dl.DATA_PROCESSED_DIR.exists()
    finally:
        dl.DATA_RAW_DIR = original_raw
        dl.DATA_PROCESSED_DIR = original_processed

def test_compute_sha256(temp_dir):
    """Test SHA256 computation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_sha256(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_determine_strata_with_difficulty(mock_dataset):
    """Test strata determination using difficulty column."""
    strata = determine_strata(mock_dataset, strata_column="difficulty")
    
    assert "easy" in strata
    assert "medium" in strata
    assert "hard" in strata
    assert len(strata["easy"]) == 2
    assert len(strata["medium"]) == 2
    assert len(strata["hard"]) == 6

def test_determine_strata_with_task_id_hash(mock_dataset):
    """Test strata determination using task_id hash when no difficulty column."""
    # Remove difficulty from column names to trigger fallback
    mock_dataset.column_names = ["task_id", "prompt"]
    
    strata = determine_strata(mock_dataset, strata_column="difficulty")
    
    # Should have created bins based on hash
    assert len(strata) > 0
    for indices in strata.values():
        assert len(indices) > 0

def test_stratified_sample_logic(mock_dataset):
    """Test stratified sampling logic."""
    strata = determine_strata(mock_dataset, strata_column="difficulty")
    
    # Sample 50%
    sampled = stratified_sample(mock_dataset, strata, ratio=0.5)
    
    # Check that we sampled from each stratum
    easy_count = sum(1 for idx in sampled if mock_dataset[idx]["difficulty"] == "easy")
    medium_count = sum(1 for idx in sampled if mock_dataset[idx]["difficulty"] == "medium")
    hard_count = sum(1 for idx in sampled if mock_dataset[idx]["difficulty"] == "hard")
    
    # With 50% ratio and small numbers, we expect at least 1 from each if size >= 2
    assert easy_count >= 1
    assert medium_count >= 1
    assert hard_count >= 1

def test_stratified_sample_underpowered(mock_dataset):
    """Test behavior when a stratum has < 50 samples (underpowered)."""
    # Create a dataset with a very small stratum
    small_data = [
        {"task_id": "1", "difficulty": "tiny"},
        {"task_id": "2", "difficulty": "tiny"},
        {"task_id": "3", "difficulty": "tiny"},
    ]
    mock_small = MagicMock()
    mock_small.__len__ = lambda self: len(small_data)
    mock_small.__getitem__ = lambda self, i: small_data[i]
    mock_small.column_names = ["task_id", "difficulty"]
    
    strata = determine_strata(mock_small, strata_column="difficulty")
    sampled = stratified_sample(mock_small, strata, ratio=0.5)
    
    # Should still sample, even if small
    assert len(sampled) > 0

def test_save_strata_log(temp_dir, mock_dataset):
    """Test saving strata log."""
    import src.data_loader as dl
    original_log = dl.STRATA_LOG_FILE
    dl.STRATA_LOG_FILE = temp_dir / "strata_log.json"
    
    try:
        strata = determine_strata(mock_dataset, strata_column="difficulty")
        save_strata_log(strata, underpowered_threshold=50)
        
        assert dl.STRATA_LOG_FILE.exists()
        with open(dl.STRATA_LOG_FILE) as f:
            log_data = json.load(f)
        
        assert "strata" in log_data
        assert "underpowered_strata" in log_data
        assert "easy" in log_data["underpowered_strata"]  # Size 2 < 50
    finally:
        dl.STRATA_LOG_FILE = original_log

def test_save_processed_split(temp_dir, mock_dataset):
    """Test saving processed split."""
    import src.data_loader as dl
    original_processed = dl.DATA_PROCESSED_DIR
    dl.DATA_PROCESSED_DIR = temp_dir / "processed"
    dl.DATA_PROCESSED_DIR.mkdir()
    
    try:
        strata = determine_strata(mock_dataset, strata_column="difficulty")
        sampled = stratified_sample(mock_dataset, strata, ratio=0.5)
        
        save_processed_split(mock_dataset, sampled, "test_split.jsonl")
        
        output_file = dl.DATA_PROCESSED_DIR / "test_split.jsonl"
        assert output_file.exists()
        
        with open(output_file) as f:
            lines = f.readlines()
        assert len(lines) == len(sampled)
    finally:
        dl.DATA_PROCESSED_DIR = original_processed

def test_save_checksums(temp_dir):
    """Test saving checksums."""
    checksum_file = temp_dir / "checksums.txt"
    
    import src.data_loader as dl
    original_file = dl.CHECKSUMS_FILE
    dl.CHECKSUMS_FILE = checksum_file
    
    try:
        save_checksums(Path("test.txt"), "abc123")
        
        assert checksum_file.exists()
        with open(checksum_file) as f:
            content = f.read()
        assert "test.txt: abc123" in content
    finally:
        dl.CHECKSUMS_FILE = original_file
