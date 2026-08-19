"""
Pytest configuration and fixtures for the project.
"""
import pytest
import json
from pathlib import Path

@pytest.fixture
def sample_study_id():
    """Sample OSF study ID for testing."""
    return "z8x9c"

@pytest.fixture
def mock_osf_metadata():
    """Mock OSF metadata for unit tests."""
    return {
        "id": "z8x9c",
        "title": "Example Pre-registration Study",
        "description": "This study investigates...",
        "attributes": {
            "preprint": True,
            "registration": True
        }
    }

@pytest.fixture
def mock_osf_files():
    """Mock OSF files list for unit tests."""
    return [
        {
            "name": "data_n_100.csv",
            "kind": "file",
            "path": "/files/data_n_100.csv"
        },
        {
            "name": "analysis_script.R",
            "kind": "file",
            "path": "/files/analysis_script.R"
        }
    ]

@pytest.fixture
def sample_study_records():
    """Sample study records for integration tests."""
    return [
        {
            "study_id": "z8x9c",
            "title": "Example Study",
            "planned_power": 0.8,
            "target_n": 100,
            "effect_size_assumption": 0.5
        }
    ]
