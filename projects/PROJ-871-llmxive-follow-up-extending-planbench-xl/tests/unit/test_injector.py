import json
import os
import tempfile
from pathlib import Path
import pytest

# Add parent to path for imports if running standalone, though usually handled by test runner
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.dataset.injector import (
    inject_failures, 
    ERROR_PATTERN, 
    RANDOM_SEED,
    INJECTION_RATIO
)


@pytest.fixture
def sample_success_data():
    """Creates a mock dataset with success ground truth."""
    return [
        {
            "task_id": "task_1",
            "ground_truth": "success",
            "tool_output": "Result A",
            "status": "completed"
        },
        {
            "task_id": "task_2",
            "ground_truth": "success",
            "tool_output": "Result B",
            "status": "completed"
        },
        {
            "task_id": "task_3",
            "ground_truth": "failure",
            "tool_output": "Error C",
            "status": "failed"
        },
        {
            "task_id": "task_4",
            "ground_truth": "success",
            "tool_output": "Result D",
            "status": "completed"
        },
        {
            "task_id": "task_5",
            "ground_truth": True,
            "tool_output": "Result E",
            "status": "completed"
        },
    ]


@pytest.fixture
def sample_success_data_list_outputs():
    """Creates a mock dataset with list-based tool outputs."""
    return [
        {
            "task_id": "list_task_1",
            "ground_truth": "success",
            "outputs": ["Step 1", "Step 2"]
        },
        {
            "task_id": "list_task_2",
            "ground_truth": "success",
            "outputs": ["Step 1"]
        },
    ]


def test_inject_failures_deterministic(sample_success_data):
    """Verifies that the injection is deterministic with the fixed seed."""
    # Run twice with same seed
    result1 = inject_failures(sample_success_data, seed=RANDOM_SEED)
    result2 = inject_failures(sample_success_data, seed=RANDOM_SEED)
    
    assert result1 == result2, "Injection results must be deterministic given the same seed."


def test_inject_failures_only_success_tasks(sample_success_data):
    """Verifies that only tasks with 'success' ground truth are candidates for injection."""
    # With a high ratio, we expect all success tasks to potentially be injected
    # But we must ensure 'failure' tasks are NEVER injected
    result = inject_failures(sample_success_data, seed=RANDOM_SEED, ratio=1.0)
    
    for record in result:
        if record["task_id"] == "task_3":
            assert record["injected_error"] is False, "Failure tasks must not be injected."
            assert ERROR_PATTERN not in record.get("tool_output", "")


def test_inject_failures_preserves_ground_truth(sample_success_data):
    """Verifies that the ground_truth field is NOT modified."""
    result = inject_failures(sample_success_data, seed=RANDOM_SEED, ratio=1.0)
    
    for i, record in enumerate(result):
        original = sample_success_data[i]
        assert record["ground_truth"] == original["ground_truth"], "Ground truth must not be modified."
        assert record["status"] == original["status"], "Status must not be modified."


def test_inject_failures_adds_flag(sample_success_data):
    """Verifies that the injected_error flag is added."""
    result = inject_failures(sample_success_data, seed=RANDOM_SEED, ratio=1.0)
    
    for record in result:
        assert "injected_error" in record, "injected_error flag must be present."
        # At least some should be True given ratio=1.0 and multiple success tasks
        if record["ground_truth"] == "success" or record["ground_truth"] is True:
            # We can't guarantee 100% injection if the random sample logic is weird,
            # but with ratio=1.0 and 4 success tasks, we expect at least 1.
            pass 
    
    # Check that at least one was injected (since we have multiple success tasks)
    injected_count = sum(1 for r in result if r.get("injected_error", False))
    assert injected_count > 0, "At least one success task should be injected."


def test_inject_failures_modifies_tool_output(sample_success_data):
    """Verifies that the error pattern is appended to tool outputs."""
    result = inject_failures(sample_success_data, seed=RANDOM_SEED, ratio=1.0)
    
    injected_found = False
    for record in result:
        if record.get("injected_error"):
            injected_found = True
            # Check string modification
            if "tool_output" in record:
                assert ERROR_PATTERN in record["tool_output"], "Error pattern must be in tool_output."
            # Check synthetic fallback if no tool_output found
            elif "_injected_error_pattern" in record:
                assert record["_injected_error_pattern"] == ERROR_PATTERN
    
    assert injected_found, "No records were marked as injected."


def test_inject_failures_list_outputs(sample_success_data_list_outputs):
    """Verifies injection works with list-based tool outputs."""
    result = inject_failures(sample_success_data_list_outputs, seed=RANDOM_SEED, ratio=1.0)
    
    for record in result:
        if record.get("injected_error"):
            outputs = record.get("outputs", [])
            assert len(outputs) > 0, "Outputs list should not be empty."
            last_output = outputs[-1]
            assert ERROR_PATTERN in last_output, "Error pattern must be in the last output element."
