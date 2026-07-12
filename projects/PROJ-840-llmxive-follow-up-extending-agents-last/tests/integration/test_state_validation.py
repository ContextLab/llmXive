"""
Integration test for State Reconstruction Validator (T013).

This test verifies that the state_validator correctly calculates accuracy
against a golden subset. It mocks the golden subset file to ensure
deterministic behavior without relying on external data generation in this specific test.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(project_root))

from classification.state_validator import calculate_reconstruction_accuracy, load_golden_subset

@pytest.fixture
def temp_golden_file():
    """Creates a temporary golden subset file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = [
            {
                "trace_id": "trace-001",
                "ground_truth_label": {"state": "completed", "value": 10.0},
                "step_state": {"state": "completed", "value": 10.0},
                "task_description": "Complete task A"
            },
            {
                "trace_id": "trace-002",
                "ground_truth_label": {"state": "failed", "value": 5.0},
                "step_state": {"state": "failed", "value": 5.0000001}, # Within 1e-6 tolerance
                "task_description": "Complete task B"
            },
            {
                "trace_id": "trace-003",
                "ground_truth_label": {"state": "pending", "value": 0.0},
                "step_state": {"state": "pending", "value": 1.0}, # Mismatch
                "task_description": "Complete task C"
            }
        ]
        json.dump(data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_load_golden_subset(temp_golden_file):
    """Test that the golden subset is loaded correctly."""
    data = load_golden_subset(temp_golden_file)
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["trace_id"] == "trace-001"

def test_reconstruction_accuracy_calculation(temp_golden_file):
    """
    Test the accuracy calculation logic.
    
    Expected results based on fixture:
    - trace-001: Match (exact)
    - trace-002: Match (within 1e-6 tolerance)
    - trace-003: Mismatch
    
    Expected Accuracy: 2/3 = 0.666...
    """
    golden_data = load_golden_subset(temp_golden_file)
    results = calculate_reconstruction_accuracy(golden_data, tolerance=1e-6)
    
    assert "reconstruction_accuracy" in results
    assert "total_traces" in results
    assert "correct_traces" in results
    assert "failed_traces" in results
    
    assert results["total_traces"] == 3
    assert results["correct_traces"] == 2
    assert results["failed_traces"] == 1
    assert abs(results["reconstruction_accuracy"] - (2/3)) < 1e-9

def test_empty_golden_subset():
    """Test behavior with an empty golden subset."""
    results = calculate_reconstruction_accuracy([], tolerance=1e-6)
    assert results["reconstruction_accuracy"] == 1.0
    assert results["total_traces"] == 0
    assert results["correct_traces"] == 0

def test_malformed_trace_skipped(temp_golden_file):
    """Test that traces missing required fields are skipped."""
    # Create a new temp file with a malformed trace
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = [
            {
                "trace_id": "trace-good",
                "ground_truth_label": {"a": 1},
                "step_state": {"a": 1},
                "task_description": "test"
            },
            {
                "trace_id": "trace-bad",
                # Missing ground_truth_label and step_state
                "task_description": "test"
            }
        ]
        json.dump(data, f)
        temp_path = f.name
    
    try:
        golden_data = load_golden_subset(temp_path)
        results = calculate_reconstruction_accuracy(golden_data, tolerance=1e-6)
        
        # Should process 1, skip 1
        assert results["total_traces"] == 2 # Total items in list
        # The logic in calculate_reconstruction_accuracy counts 'total' as len(golden_subset)
        # but skips processing. We need to check the details.
        
        # Check details for the skip
        skipped = [d for d in results["details"] if d["status"] == "skipped"]
        assert len(skipped) == 1
        assert skipped[0]["trace_id"] == "trace-bad"
        
        # Check details for the pass
        passed = [d for d in results["details"] if d["status"] == "pass"]
        assert len(passed) == 1
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
