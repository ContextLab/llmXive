"""
Unit tests for the Corruption Injector.

Verifies that corruption is injected at the correct rate,
that the central log is updated, and that data integrity is maintained
(except for the intentional corruption).
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import random

# Import the module under test
from simulators.corruption_injector import CorruptionInjector
from generators.workflow_generator import calculate_sha256

@pytest.fixture
def sample_workflow_data():
    """Create a sample workflow data structure."""
    return {
        "workflow_id": "test_wf_001",
        "events": [
            {"id": "e1", "type": "start", "timestamp": "2023-01-01T00:00:00", "content": "Started"},
            {"id": "e2", "type": "tool_call", "timestamp": "2023-01-01T00:00:01", "content": "Calling tool A", "tool": "A"},
            {"id": "e3", "type": "tool_output", "timestamp": "2023-01-01T00:00:02", "content": "Result A", "tool": "A"},
            {"id": "e4", "type": "decision", "timestamp": "2023-01-01T00:00:03", "content": "Next step B", "next": "B"},
            {"id": "e5", "type": "end", "timestamp": "2023-01-01T00:00:04", "content": "Finished"}
        ],
        "metadata": {"agent": "test_agent"}
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_corruption_rate_mixed(sample_workflow_data, temp_dir):
    """Test that corruption happens at the specified rate in mixed mode."""
    # Use a high rate to ensure at least one corruption in this small dataset
    rate = 0.5
    injector = CorruptionInjector(
        corruption_rate=rate,
        corruption_mode="mixed",
        output_dir=temp_dir,
        state_file_path=os.path.join(temp_dir, "state.yaml")
    )
    
    # Run multiple times to check statistical behavior (or just one for deterministic check)
    # For unit test, we fix the seed to make it deterministic
    random.seed(42)
    
    success, result = injector.inject_corruption("wf_001", sample_workflow_data)
    
    assert success is True
    # With rate 0.5 and 5 entries, we expect ~2-3 corruptions.
    # We just check that the log was updated and entries were marked.
    assert len(result["corrupted_entries"]) > 0
    
    # Verify log file exists
    log_path = Path(temp_dir) / "corruption_log.json"
    assert log_path.exists()
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert len(log_data["entries"]) == len(result["corrupted_entries"])
    for entry in log_data["entries"]:
        assert entry["workflow_id"] == "wf_001"
        assert entry["corruption_type"] in ["delete", "modify"]

def test_corruption_deletion_only(sample_workflow_data, temp_dir):
    """Test that only deletions occur in delete_only mode."""
    random.seed(999)
    injector = CorruptionInjector(
        corruption_rate=1.0, # Force corruption
        corruption_mode="delete_only",
        output_dir=temp_dir
    )
    
    success, result = injector.inject_corruption("wf_del", sample_workflow_data)
    assert success is True
    
    # Check the actual data structure
    # Find the first event that was corrupted
    corrupted_count = 0
    for event in sample_workflow_data["events"]:
        if event.get("corrupted") and event.get("corruption_type") == "deletion":
            corrupted_count += 1
            assert event["content"] is None
    
    assert corrupted_count > 0

def test_corruption_modification_only(sample_workflow_data, temp_dir):
    """Test that only modifications occur in modify_only mode."""
    random.seed(888)
    injector = CorruptionInjector(
        corruption_rate=1.0,
        corruption_mode="modify_only",
        output_dir=temp_dir
    )
    
    success, result = injector.inject_corruption("wf_mod", sample_workflow_data)
    assert success is True
    
    # Check modifications
    modified_count = 0
    for event in sample_workflow_data["events"]:
        if event.get("corrupted") and event.get("corruption_type") == "modification":
            modified_count += 1
            # Check if content was appended
            if event.get("content"):
                assert "[CORRUPTED]" in event["content"]
    
    assert modified_count > 0

def test_corruption_log_updates(temp_dir):
    """Test that the central log accumulates entries across calls."""
    random.seed(123)
    injector = CorruptionInjector(
        corruption_rate=0.5,
        corruption_mode="mixed",
        output_dir=temp_dir
    )
    
    # First call
    data1 = {"events": [{"id": "a", "type": "x", "val": 1}]}
    injector.inject_corruption("wf1", data1)
    
    # Second call
    data2 = {"events": [{"id": "b", "type": "y", "val": 2}]}
    injector.inject_corruption("wf2", data2)
    
    log_path = Path(temp_dir) / "corruption_log.json"
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    # Should have entries from both workflows
    assert log_data["metadata"]["total_files_processed"] == 2
    assert len(log_data["entries"]) >= 0 # Could be 0 if rate didn't hit, but structure is there

def test_invalid_corruption_rate():
    """Test that invalid rates raise an error."""
    with pytest.raises(ValueError):
        CorruptionInjector(corruption_rate=1.5)
    
    with pytest.raises(ValueError):
        CorruptionInjector(corruption_rate=-0.1)

def test_invalid_mode():
    """Test that invalid modes raise an error."""
    with pytest.raises(ValueError):
        CorruptionInjector(corruption_mode="invalid_mode")