"""
Pytest shared fixtures and configuration for llmXive project.

This module provides:
- pytest_configure: Custom configuration for the test session.
- temp_output_dir: A temporary directory fixture for test outputs.
- sample_data, otu_data, diversity_metric_data: Mock data fixtures.
- test_log_handler: A logging handler for capturing test logs.
- configure_test_logging: Setup for test-specific logging.
"""
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, List, Dict, Any

import pytest
import pandas as pd

# Ensure the code directory is in the path for imports
# This assumes tests are run from the project root
_code_dir = Path(__file__).parent.parent / "code"
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))


def pytest_configure(config):
    """
    Custom pytest configuration.
    Sets up markers and initial configuration if needed.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture(scope="session")
def test_log_handler() -> Generator[logging.Handler, None, None]:
    """
    Provides a logging handler that captures log output for the session.
    Useful for verifying that logging calls occur with correct levels/messages.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    yield handler
    handler.close()


@pytest.fixture(scope="function")
def temp_output_dir(tmp_path: Path) -> Path:
    """
    Creates a temporary directory for test outputs that persists for the duration
    of the test function.
    
    Args:
        tmp_path: Pytest built-in temporary path fixture.
        
    Returns:
        Path: The path to the temporary directory.
    """
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture(scope="function")
def sample_data() -> pd.DataFrame:
    """
    Provides a mock DataFrame representing Sample data.
    Matches the schema expected by code/data_models.py and code/ingestion.py.
    
    Columns:
        sample_id: Unique identifier
        timestamp: ISO formatted timestamp
        pH: pH value
        temp: Temperature in Celsius
        pH_sd: Standard deviation of pH in window
        location: Location name
        fastq_path: Path to FASTQ file
        deployment_event: Event ID
        sensor_id: Sensor identifier
        coordinates: Lat/Lon string
    """
    data = {
        "sample_id": ["S001", "S002", "S003", "S004"],
        "timestamp": [
            "2023-01-01T10:00:00",
            "2023-01-01T10:15:00",
            "2023-01-01T10:30:00",
            "2023-01-01T10:45:00"
        ],
        "pH": [6.5, 7.2, 1.5, 8.9],  # Includes an outlier (1.5) and edge cases
        "temp": [2.5, 3.1, 12.0, 4.0],
        "pH_sd": [0.05, 0.12, 0.25, 0.08],  # S003 has high heterogeneity
        "location": ["Vent_A", "Vent_A", "Vent_B", "Vent_C"],
        "fastq_path": [
            "data/raw/S001.fastq",
            "data/raw/S002.fastq",
            "data/raw/S003.fastq",
            "data/raw/S004.fastq"
        ],
        "deployment_event": ["DEP_001"] * 4,
        "sensor_id": ["SENS_01", "SENS_01", "SENS_02", "SENS_03"],
        "coordinates": ["45N,120W"] * 4
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def otu_data() -> pd.DataFrame:
    """
    Provides a mock DataFrame representing OTU/ASV table data.
    Rows are samples, columns are OTUs.
    """
    data = {
        "sample_id": ["S001", "S002", "S003"],
        "OTU_001": [100, 50, 200],
        "OTU_002": [50, 200, 50],
        "OTU_003": [0, 10, 5],
        "OTU_004": [20, 30, 15]
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def diversity_metric_data() -> pd.DataFrame:
    """
    Provides a mock DataFrame representing calculated diversity metrics.
    """
    data = {
        "sample_id": ["S001", "S002", "S003", "S004"],
        "shannon": [2.5, 1.8, 3.1, 2.0],
        "simpson": [0.85, 0.70, 0.92, 0.75],
        "pH": [6.5, 7.2, 1.5, 8.9],
        "temp": [2.5, 3.1, 12.0, 4.0]
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def configure_test_logging(test_log_handler: logging.Handler) -> Generator[None, None, None]:
    """
    Configures the root logger for the test session to use the test_log_handler.
    Yields control to the test, then ensures cleanup.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(test_log_handler)
    yield
    logger.removeHandler(test_log_handler)
    test_log_handler.flush()