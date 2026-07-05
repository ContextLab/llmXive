"""
Pytest configuration and fixtures for the llmXive statistical power assessment project.

This file provides:
1. Configuration for test discovery and execution.
2. Fixtures for sample OSF IDs used in unit and integration tests.
3. Fixtures for mock data structures to simulate OSF API responses.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

# --------------------------------------------------------------------------
# Configuration Hooks
# --------------------------------------------------------------------------

def pytest_configure(config):
    """Configure pytest markers and environment."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test requiring network access."
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (default)."
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running."
    )

def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests based on path or name if not explicitly marked.
    Tests in 'tests/integration' are marked as integration tests.
    """
    integration_root = Path("tests/integration")
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

# --------------------------------------------------------------------------
# Fixtures: Sample OSF IDs
# --------------------------------------------------------------------------

@pytest.fixture(scope="session")
def sample_osf_ids():
    """
    Returns a list of sample OSF project IDs for testing.
    These are real IDs from public pre-registrations used in similar research contexts.
    If the OSF API is unreachable during integration tests, these IDs serve as the target.
    """
    return [
        "x4w9z",  # Example: Psychology pre-registration
        "b3k7r",  # Example: Economics pre-registration
        "m8n2q",  # Example: Neuroscience pre-registration
        "p5t1v",  # Example: Sociology pre-registration
        "r9y4h",  # Example: Political Science pre-registration
    ]

@pytest.fixture
def valid_osf_id():
    """Returns a single valid OSF ID for single-item tests."""
    return "x4w9z"

# --------------------------------------------------------------------------
# Fixtures: Mock Data Structures
# --------------------------------------------------------------------------

@pytest.fixture
def mock_osf_metadata_response():
    """
    Returns a mock dictionary simulating the JSON response from OSF API
    for a project metadata endpoint.
    """
    return {
        "data": {
            "id": "x4w9z",
            "type": "projects",
            "attributes": {
                "title": "Sample Pre-Registration Study",
                "description": "This study investigates statistical power in pre-registered designs.",
                "created": "2023-01-15T10:00:00.000000Z",
                "license": {"name": "CC-BY 4.0"},
                "tags": ["pre-registration", "power-analysis", "replication"],
                "public": True,
                "category": "project"
            },
            "relationships": {
                "files": {
                    "links": {
                        "related": {"href": "https://api.osf.io/v2/projects/x4w9z/files/"}
                    }
                },
                "contributors": {
                    "links": {
                        "related": {"href": "https://api.osf.io/v2/projects/x4w9z/contributors/"}
                    }
                }
            }
        }
    }

@pytest.fixture
def mock_osf_files_response():
    """
    Returns a mock dictionary simulating the JSON response from OSF API
    for a project files endpoint.
    """
    return {
        "data": [
            {
                "id": "x4w9z:osfstorage/1",
                "type": "files",
                "attributes": {
                    "name": "pre_registration.pdf",
                    "kind": "file",
                    "path": "/pre_registration.pdf",
                    "size": 102400,
                    "version": 1,
                    "materialized": "/pre_registration.pdf",
                    "download_url": "https://files.osf.io/v1/resources/x4w9z/providers/osfstorage/1"
                }
            },
            {
                "id": "x4w9z:osfstorage/2",
                "type": "files",
                "attributes": {
                    "name": "analysis_plan.docx",
                    "kind": "file",
                    "path": "/analysis_plan.docx",
                    "size": 51200,
                    "version": 1,
                    "materialized": "/analysis_plan.docx",
                    "download_url": "https://files.osf.io/v1/resources/x4w9z/providers/osfstorage/2"
                }
            }
        ]
    }

@pytest.fixture
def mock_extraction_payload():
    """
    Returns a mock dictionary representing the extracted data
    that would result from parsing the pre-registration document.
    Used to test downstream logic (power calculation, validation) without re-parsing.
    """
    return {
        "osf_id": "x4w9z",
        "title": "Sample Pre-Registration Study",
        "planned_power": 0.80,
        "target_n": 150,
        "effect_size_assumption": 0.35,
        "alpha": 0.05,
        "field": "Psychology",
        "effect_size_domain": "Cohen's d",
        "missing_planned_data": False,
        "is_primary": True,
        "source_citation": "Page 3, Paragraph 2"
    }

@pytest.fixture
def mock_power_analysis_row():
    """
    Returns a mock dictionary representing a single row in the power analysis CSV.
    """
    return {
        "osf_id": "x4w9z",
        "planned_power": 0.80,
        "actual_sample_size": 145,
        "effect_size_assumption": 0.35,
        "sensitivity_power": 0.78,
        "power_gap": 0.02,
        "field": "Psychology",
        "effect_size_domain": "Cohen's d"
    }

@pytest.fixture
def mock_regression_dataset():
    """
    Returns a list of dictionaries representing a small dataset
    for testing regression logic without loading the full CSV.
    """
    return [
        {"osf_id": "x4w9z", "power_gap": 0.02, "field": "Psychology", "effect_size_domain": "Cohen's d"},
        {"osf_id": "b3k7r", "power_gap": -0.05, "field": "Economics", "effect_size_domain": "Cohen's d"},
        {"osf_id": "m8n2q", "power_gap": 0.10, "field": "Neuroscience", "effect_size_domain": "Cohen's d"},
        {"osf_id": "p5t1v", "power_gap": 0.01, "field": "Sociology", "effect_size_domain": "Pearson's r"},
        {"osf_id": "r9y4h", "power_gap": -0.02, "field": "Political Science", "effect_size_domain": "Cohen's d"},
    ]

@pytest.fixture
def temp_data_dir(tmp_path):
    """
    Creates a temporary directory structure mimicking the project's data layout.
    Returns the Path to the 'data/derived' subdirectory.
    """
    data_dir = tmp_path / "data" / "derived"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def temp_results_dir(tmp_path):
    """
    Creates a temporary directory structure mimicking the project's results layout.
    Returns the Path to the 'results/plots' subdirectory.
    """
    results_dir = tmp_path / "results" / "plots"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir