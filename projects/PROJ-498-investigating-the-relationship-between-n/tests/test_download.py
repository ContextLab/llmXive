"""
Unit tests for the download module (T013).

Tests:
1. read_dataset_id() - file existence, empty file, malformed ID
2. compute_sha256() - hash calculation
3. generate_checksums() - checksum generation
4. save_checksums() - file writing
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download import (
    read_dataset_id,
    compute_sha256,
    generate_checksums,
    save_checksums,
    ensure_directories,
    log_to_file
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def setup_test_files(temp_dir):
    """Setup test files for download module tests."""
    # Create necessary directories
    data_dir = temp_dir / "data"
    raw_dir = data_dir / "raw"
    logs_dir = temp_dir / "logs"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a mock dataset ID file
    dataset_id_file = data_dir / "selected_dataset_id.txt"
    dataset_id_file.write_text("ds004173")
    
    # Create a mock downloaded file
    mock_dataset_dir = raw_dir / "ds004173"
    mock_dataset_dir.mkdir(parents=True, exist_ok=True)
    mock_file = mock_dataset_dir / "test_file.txt"
    mock_file.write_text("test content for hashing")
    
    return {
        "data_dir": data_dir,
        "raw_dir": raw_dir,
        "dataset_id_file": dataset_id_file,
        "mock_dataset_dir": mock_dataset_dir,
        "mock_file": mock_file
    }

def test_ensure_directories(temp_dir):
    """Test that ensure_directories creates required folders."""
    # Temporarily change working directory
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        # Call the function
        ensure_directories()
        
        # Verify directories exist
        assert Path("data/raw").exists()
        assert Path("logs").exists()
        assert Path("data").exists()
    finally:
        os.chdir(original_cwd)

def test_compute_sha256(setup_test_files):
    """Test SHA-256 hash computation."""
    mock_file = setup_test_files["mock_file"]
    hash_value = compute_sha256(str(mock_file))
    
    # Verify hash is 64 hex characters
    assert len(hash_value) == 64
    assert all(c in '0123456789abcdef' for c in hash_value)
    
    # Verify consistency
    hash_value2 = compute_sha256(str(mock_file))
    assert hash_value == hash_value2

def test_read_dataset_id_valid(setup_test_files):
    """Test reading a valid dataset ID."""
    # Temporarily set the DATASET_ID_FILE path
    original_path = None
    try:
        # We need to mock the file path since the module uses a constant
        import download
        original_path = download.DATASET_ID_FILE
        download.DATASET_ID_FILE = str(setup_test_files["dataset_id_file"])
        
        result = read_dataset_id()
        assert result == "ds004173"
    finally:
        if original_path:
            download.DATASET_ID_FILE = original_path

def test_read_dataset_id_missing_file(temp_dir, caplog):
    """Test behavior when dataset ID file is missing."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        import download
        original_path = download.DATASET_ID_FILE
        download.DATASET_ID_FILE = str(temp_dir / "data" / "selected_dataset_id.txt")
        
        # Should return None and log appropriately
        result = read_dataset_id()
        assert result is None
    finally:
        if original_path:
            download.DATASET_ID_FILE = original_path
        os.chdir(original_cwd)

def test_read_dataset_id_empty_file(temp_dir):
    """Test behavior when dataset ID file is empty."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        data_dir = temp_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        import download
        original_path = download.DATASET_ID_FILE
        download.DATASET_ID_FILE = str(data_dir / "selected_dataset_id.txt")
        
        # Create empty file
        download.DATASET_ID_FILE = str(data_dir / "selected_dataset_id.txt")
        Path(download.DATASET_ID_FILE).write_text("")
        
        # Should exit with code 1
        with pytest.raises(SystemExit) as exc_info:
            read_dataset_id()
        assert exc_info.value.code == 1
    finally:
        os.chdir(original_cwd)

def test_read_dataset_id_malformed(temp_dir):
    """Test behavior when dataset ID file has invalid format."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        data_dir = temp_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        import download
        original_path = download.DATASET_ID_FILE
        download.DATASET_ID_FILE = str(data_dir / "selected_dataset_id.txt")
        
        # Create malformed file
        Path(download.DATASET_ID_FILE).write_text("invalid_dataset_id")
        
        # Should exit with code 1
        with pytest.raises(SystemExit) as exc_info:
            read_dataset_id()
        assert exc_info.value.code == 1
    finally:
        os.chdir(original_cwd)

def test_generate_checksums(setup_test_files):
    """Test checksum generation for a dataset."""
    mock_dataset_dir = setup_test_files["mock_dataset_dir"]
    
    # Temporarily change RAW_DIR
    import download
    original_raw_dir = download.RAW_DIR
    download.RAW_DIR = str(setup_test_files["raw_dir"])
    
    try:
        checksums = generate_checksums("ds004173")
        
        # Verify checksums contain the mock file
        assert len(checksums) > 0
        assert any("test_file.txt" in key for key in checksums.keys())
    finally:
        download.RAW_DIR = original_raw_dir

def test_save_checksums(setup_test_files, temp_dir):
    """Test saving checksums to JSON file."""
    import download
    original_checksums_file = download.CHECKSUMS_FILE
    download.CHECKSUMS_FILE = str(temp_dir / "raw" / "checksums.json")
    
    try:
        checksums = {
            "file1.txt": "abc123",
            "file2.txt": "def456"
        }
        
        save_checksums(checksums, "ds004173")
        
        # Verify file exists and contains correct data
        assert Path(download.CHECKSUMS_FILE).exists()
        
        with open(download.CHECKSUMS_FILE, "r") as f:
            data = json.load(f)
        
        assert data["dataset_id"] == "ds004173"
        assert "checksums" in data
        assert "timestamp" in data
    finally:
        download.CHECKSUMS_FILE = original_checksums_file

def test_log_to_file(temp_dir):
    """Test logging to file."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        logs_dir = temp_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        import download
        original_log_file = download.LOG_FILE
        download.LOG_FILE = str(logs_dir / "test.log")
        
        log_to_file("Test message", "INFO")
        
        # Verify log file exists and contains message
        assert Path(download.LOG_FILE).exists()
        with open(download.LOG_FILE, "r") as f:
            content = f.read()
        assert "Test message" in content
    finally:
        if 'original_log_file' in locals():
            download.LOG_FILE = original_log_file
        os.chdir(original_cwd)