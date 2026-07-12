"""
Pytest configuration and shared fixtures for llmXive unit tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the code directory to the path for imports
@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Set up test environment variables."""
    # Create necessary directories
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    
    # Set environment variables for test isolation
    os.environ["TEST_MODE"] = "true"
    os.environ["DATA_PATH"] = str(tmp_path / "data")
    
    yield
    
    # Cleanup
    if "TEST_MODE" in os.environ:
        del os.environ["TEST_MODE"]
    if "DATA_PATH" in os.environ:
        del os.environ["DATA_PATH"]

@pytest.fixture
def sample_trace_data():
    """Provide sample ALE trace data for testing."""
    return {
        "trace_id": "sample_001",
        "steps": [
            {
                "step_id": 1,
                "action": "initialize",
                "state": {"x": 0.0, "y": 0.0, "angle": 0.0}
            },
            {
                "step_id": 2,
                "action": "move",
                "state": {"x": 1.0, "y": 0.0, "angle": 0.0}
            },
            {
                "step_id": 3,
                "action": "rotate",
                "state": {"x": 1.0, "y": 0.0, "angle": 90.0}
            }
        ],
        "task_description": "Move to (1,0) and rotate 90 degrees",
        "ground_truth": "success"
    }

@pytest.fixture
def sample_classification_results():
    """Provide sample classification results for testing."""
    return [
        {
            "trace_id": "trace_001",
            "failure_mode": "state_persistence",
            "confidence": 0.95
        },
        {
            "trace_id": "trace_002",
            "failure_mode": "reasoning_deficit",
            "confidence": 0.88
        },
        {
            "trace_id": "trace_003",
            "failure_mode": "state_persistence",
            "confidence": 0.92
        }
    ]

@pytest.fixture
def sample_baseline_results():
    """Provide sample baseline execution results."""
    return {
        "task_001": {"passed": True, "steps": 10},
        "task_002": {"passed": False, "steps": 5},
        "task_003": {"passed": True, "steps": 8},
        "task_004": {"passed": False, "steps": 3},
        "task_005": {"passed": True, "steps": 12}
    }

@pytest.fixture
def sample_intervention_results():
    """Provide sample intervention execution results."""
    return {
        "task_001": {"passed": True, "steps": 10},
        "task_002": {"passed": True, "steps": 6},  # Improved
        "task_003": {"passed": True, "steps": 8},
        "task_004": {"passed": False, "steps": 3},
        "task_005": {"passed": True, "steps": 11}  # Slightly improved
    }