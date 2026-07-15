"""
Pytest configuration and fixtures for the test suite.

This file contains shared fixtures and configuration for all tests.
"""
import sys
import os
from pathlib import Path
import pytest

# Add the parent directory to sys.path so imports work
# This allows tests to import from code/ module
@pytest.fixture(autouse=True)
def add_parent_to_path():
    """Automatically add parent directory to sys.path for all tests."""
    parent_dir = str(Path(__file__).parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    yield
    
    # Clean up after test if needed
    if parent_dir in sys.path:
        sys.path.remove(parent_dir)


@pytest.fixture
def sample_mwq_response():
    """Provide a sample MWQ response for testing."""
    # 10 items, typical MWQ length
    return [3, 2, 4, 3, 2, 4, 3, 2, 4, 3]


@pytest.fixture
def sample_config():
    """Provide a sample configuration dictionary for testing."""
    return {
        "paths": {
            "data_raw": "/tmp/test_data/raw",
            "data_processed": "/tmp/test_data/processed",
            "code": "/tmp/test_code",
            "tests": "/tmp/test_tests"
        },
        "random_seed": 42,
        "hyperparameters": {
            "alpha": 1.0,
            "max_iter": 1000
        }
    }


@pytest.fixture
def tmp_test_dir(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_csv_data():
    """Provide sample CSV data for testing."""
    return [
        ["Subject_ID", "Global_Signal_SD", "MWQ_Score", "Age", "Sex"],
        ["sub-001", "0.123", "25", "24", "M"],
        ["sub-002", "0.456", "30", "28", "F"],
        ["sub-003", "0.789", "22", "22", "M"]
    ]


@pytest.fixture
def sample_json_data():
    """Provide sample JSON data for testing."""
    return {
        "subject_id": "sub-001",
        "global_signal_sd": 0.123,
        "mwq_score": 25,
        "age": 24,
        "sex": "M",
        "metadata": {
            "pipeline_version": "1.0.0",
            "processing_date": "2024-01-01"
        }
    }