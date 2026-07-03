"""
Pytest configuration and fixtures for llmXive project.

This file provides shared fixtures for testing the SLR analysis pipeline.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config, get_config
from code.data.ingestion import DataUnavailableError


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data artifacts."""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture(scope="function")
def mock_config():
    """
    Create a mock configuration object for testing.
    
    Returns a Config object with test-specific paths and URLs.
    """
    config = Config(
        project_root=str(project_root),
        data_dir=str(project_root / "data"),
        code_dir=str(project_root / "code"),
        verified_dataset_urls={
            "LAGEOS-1": "https://cddis.nasa.gov/archive/slr/normal_points/LAGEOS1/",
            "LAGEOS-2": "https://cddis.nasa.gov/archive/slr/normal_points/LAGEOS2/",
            "Etalon-1": "https://cddis.nasa.gov/archive/slr/normal_points/Etalon1/",
            "Etalon-2": "https://cddis.nasa.gov/archive/slr/normal_points/Etalon2/",
            "Starlette": "https://cddis.nasa.gov/archive/slr/normal_points/Starlette/"
        },
        hyperparams={
            "residual_threshold_cm": 2.0,
            "min_points_per_satellite": 500,
            "convergence_tolerance": 1e-5
        }
    )
    return config


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text("""
    project_root: /tmp/test_project
    data_dir: /tmp/test_project/data
    code_dir: /tmp/test_project/code
    verified_dataset_urls:
      LAGEOS-1: https://example.com/lageos1
      LAGEOS-2: https://example.com/lageos2
    hyperparams:
      residual_threshold_cm: 2.0
      min_points_per_satellite: 100
    """)
    return config_path


@pytest.fixture
def mock_fetch_response():
    """Mock response object for testing fetch functions."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    1983 01 01 12 00 00 000 1000 1.234 0.001
    1983 01 02 12 00 00 000 1000 1.235 0.002
    1983 01 03 12 00 00 000 1000 1.236 0.001
    """
    mock_response.iter_lines.return_value = [line.encode() for line in mock_response.text.strip().split('\n')]
    return mock_response


@pytest.fixture
def mock_empty_response():
    """Mock response object simulating empty data."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.iter_lines.return_value = []
    return mock_response


@pytest.fixture
def mock_403_response():
    """Mock response object simulating 403 Forbidden."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden: Access denied"
    return mock_response


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, mock_config):
    """
    Automatically set up test environment for all tests.
    
    Patches get_config to return mock_config during tests.
    """
    monkeypatch.setattr("code.config.get_config", lambda: mock_config)
    monkeypatch.setenv("LLMXIVE_ENV", "test")


@pytest.fixture
def sample_normal_points():
    """
    Generate sample normal point data for testing.
    
    Returns a list of dictionaries representing SLR observations.
    """
    return [
        {
            "year": 1983,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "station_id": 7110,
            "range": 1000.0,
            "residual": 1.234,
            "sigma": 0.001
        },
        {
            "year": 1983,
            "month": 1,
            "day": 2,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "station_id": 7110,
            "range": 1000.0,
            "residual": 1.235,
            "sigma": 0.002
        }
    ]