import os
import json
import tempfile
import shutil
import sys
import pytest
from datetime import datetime

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_collection import (
    ensure_data_directory,
    load_existing_logs,
    save_logs,
    calculate_checksum,
    update_checksums,
    export_raw_data,
    process_help_requests,
    handle_abandoned_records
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data testing."""
    temp_dir = tempfile.mkdtemp()
    # Mock the global paths by temporarily overriding them or using a context
    # For this test, we will use relative paths assuming the test runs from project root
    # or we patch the module's constants.
    # Since constants are global, we'll run the test in a way that creates data in temp
    # but the module expects 'data'. We will use monkeypatch or just verify file creation logic.
    
    # To keep it simple and robust: we create the structure in the temp dir,
    # but the module writes to 'data'. We will verify that 'data' is created if it doesn't exist.
    # Actually, better approach: patch the DATA_DIR constant in the module if possible,
    # or just ensure 'data' exists and clean it up.
    # Let's just ensure 'data' is clean and use the real paths.
    
    # Save original state
    original_logs = os.path.exists("data/raw/participant_logs.json")
    original_checksums = os.path.exists("data/checksums.txt")
    
    yield temp_dir
    
    # Cleanup
    if os.path.exists("data/raw/participant_logs.json") and not original_logs:
        os.remove("data/raw/participant_logs.json")
    if os.path.exists("data/checksums.txt") and not original_checksums:
        # Remove last line if we only added one, or clear file if it was empty
        pass # Simple cleanup for test isolation

def test_ensure_data_directory_creates_structure():
    """Test that ensure_data_directory creates the required folders."""
    # Remove data dir if exists to test creation
    if os.path.exists("data"):
        shutil.rmtree("data")
    
    ensure_data_directory()
    
    assert os.path.isdir("data")
    assert os.path.isdir("data/raw")
    assert os.path.isdir("data/processed")
    assert os.path.isdir("data/reports")

def test_save_and_load_logs():
    """Test saving and loading logs."""
    test_logs = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"}
    ]
    
    save_logs(test_logs)
    loaded_logs = load_existing_logs()
    
    assert len(loaded_logs) == 2
    assert loaded_logs[0]["id"] == "1"
    assert loaded_logs[1]["name"] == "Bob"

def test_calculate_checksum():
    """Test checksum calculation."""
    # Create a temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = calculate_checksum(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
        assert checksum != ""
    finally:
        os.remove(temp_path)

def test_export_raw_data_creates_file_and_checksum():
    """Test that export_raw_data creates the JSON file and updates checksums."""
    test_data = [
        {
            "participant_id": "TEST-001",
            "condition": "LLM",
            "help_requests": [
                {"timestamp": "2023-01-01T00:00:00", "content": "Hello", "category": "general"}
            ],
            "time_on_task": 1200,
            "session_active": False
        }
    ]
    
    # Ensure clean state
    if os.path.exists("data/raw/participant_logs.json"):
        os.remove("data/raw/participant_logs.json")
    if os.path.exists("data/checksums.txt"):
        # Remove only our test entry if possible, or just append logic handles it
        pass
    
    # Run export
    export_raw_data(test_data)
    
    # Verify file creation
    assert os.path.exists("data/raw/participant_logs.json")
    
    # Verify content
    with open("data/raw/participant_logs.json", 'r') as f:
        content = json.load(f)
    assert len(content) == 1
    assert content[0]["participant_id"] == "TEST-001"
    
    # Verify checksum file update
    # We check if the file exists and has content
    assert os.path.exists("data/checksums.txt")
    with open("data/checksums.txt", 'r') as f:
        lines = f.readlines()
        assert len(lines) > 0
        # Check if the last line contains the expected file name
        assert "participant_logs.json" in lines[-1]

def test_process_help_requests_calculates_proxy():
    """Test cognitive load proxy calculation."""
    logs = [
        {
            "help_requests": [{"content": "Q1"}, {"content": "Q2"}],
            "time_on_task": 600
        }
    ]
    
    result = process_help_requests(logs)
    
    # Count = 2, Avg Time = 300, Proxy = 600
    assert result[0]["cognitive_load_proxy"] == 600

def test_handle_abandoned_records():
    """Test that abandoned records are separated."""
    logs = [
        {"id": "1", "session_active": True},
        {"id": "2", "session_active": False},
        {"id": "3", "status": "abandoned"}
    ]
    
    valid = handle_abandoned_records(logs)
    
    # Active ones should be marked as abandoned and moved to dropouts
    # But handle_abandoned_records returns the list after marking.
    # It saves dropouts to file.
    # We verify the returned list contains the non-active ones?
    # Actually, the function returns 'valid_logs' which are those NOT active.
    # Wait, the logic: if active -> mark abandoned, add to dropouts. else -> valid.
    # So valid should contain id 2 and 3 (since 3 was already abandoned, it's not active).
    # But 1 was active, so it was moved to dropouts.
    
    # Let's re-read the logic in the function:
    # if active OR status == abandoned: mark abandoned, add to dropouts
    # else: valid
    
    # Input:
    # 1: active=True -> dropouts
    # 2: active=False -> valid
    # 3: status=abandoned -> dropouts (because condition is active OR status==abandoned)
    
    # So valid should only have id 2.
    assert len(valid) == 1
    assert valid[0]["id"] == "2"
    
    # Verify dropouts file was created
    assert os.path.exists("data/raw/dropouts.json")
    with open("data/raw/dropouts.json", 'r') as f:
        dropouts = json.load(f)
    assert len(dropouts) == 2 # ID 1 and ID 3
    assert dropouts[0]["id"] == "1"
    assert dropouts[1]["id"] == "3"
    
    # Cleanup
    os.remove("data/raw/dropouts.json")