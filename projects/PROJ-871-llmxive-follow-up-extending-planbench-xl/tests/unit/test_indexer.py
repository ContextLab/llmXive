import json
import tempfile
from pathlib import Path
import pytest

# Import the module functions
# We need to adjust the import path to match the project structure relative to tests/
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.dataset.indexer import (
    load_injected_data,
    extract_failure_signatures,
    build_failure_index,
    save_index,
    ERROR_SUFFIX
)

def test_extract_failure_signatures_basic():
    """Test that signatures are correctly extracted from records with injected errors."""
    test_records = [
        {
            "task_id": "1",
            "injected_error": True,
            "tool_outputs": [
                {"tool_id": "search_web", "output": "Found results."},
                {"tool_id": "calculator", "output": f"Error: 42 {ERROR_SUFFIX}"}
            ]
        },
        {
            "task_id": "2",
            "injected_error": False,
            "tool_outputs": [
                {"tool_id": "search_web", "output": "Success"}
            ]
        },
        {
            "task_id": "3",
            "injected_error": True,
            "tool_outputs": [
                {"tool_id": "weather_api", "output": f"Timeout {ERROR_SUFFIX}"}
            ]
        }
    ]

    signatures = extract_failure_signatures(test_records)

    assert "calculator" in signatures
    assert signatures["calculator"] == ERROR_SUFFIX
    assert "weather_api" in signatures
    assert signatures["weather_api"] == ERROR_SUFFIX
    assert "search_web" not in signatures  # The one in task 1 didn't have error, task 2 is not injected

def test_extract_failure_signatures_empty():
    """Test extraction with no injected errors."""
    test_records = [
        {
            "task_id": "1",
            "injected_error": False,
            "tool_outputs": [{"tool_id": "tool_a", "output": "OK"}]
        }
    ]
    signatures = extract_failure_signatures(test_records)
    assert len(signatures) == 0

def test_build_failure_index_schema():
    """Test that the index is built with the correct schema."""
    raw_signatures = {
        "tool_a": ERROR_SUFFIX,
        "tool_b": ERROR_SUFFIX
    }

    index_data = build_failure_index(raw_signatures)

    assert isinstance(index_data, list)
    assert len(index_data) == 2

    for entry in index_data:
        assert "tool_id" in entry
        assert "pattern" in entry
        assert "recovery_strategy" in entry
        assert entry["recovery_strategy"] == "replan"
        assert entry["pattern"] == ERROR_SUFFIX

def test_save_and_load_index():
    """Test the full cycle of saving and loading the index file."""
    index_data = [
        {"tool_id": "test_tool", "pattern": ERROR_SUFFIX, "recovery_strategy": "replan"}
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "test_index.json"
        
        save_index(index_data, tmp_path)
        
        assert tmp_path.exists()
        
        with open(tmp_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == index_data

def test_extract_failure_signatures_mixed_outputs():
    """Test extraction when outputs contain mixed success and failure."""
    test_records = [
        {
            "task_id": "1",
            "injected_error": True,
            "tool_outputs": [
                {"tool_id": "tool_success", "output": "All good"},
                {"tool_id": "tool_fail", "output": f"Crash {ERROR_SUFFIX}"},
                {"tool_id": "tool_success_2", "output": "Still good"}
            ]
        }
    ]
    
    signatures = extract_failure_signatures(test_records)
    
    assert "tool_fail" in signatures
    assert "tool_success" not in signatures
    assert "tool_success_2" not in signatures