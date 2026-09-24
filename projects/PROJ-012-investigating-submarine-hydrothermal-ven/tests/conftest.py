"""
Pytest configuration and fixtures for contract tests (T006, T007).

Provides shared fixtures for schema validation tests across all user stories.
"""
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
import pytest
import yaml
import pandas as pd
import numpy as np

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "code"))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Generate mock sample data for testing."""
    return pd.DataFrame({
        'sample_id': ['S001', 'S002', 'S003'],
        'timestamp': ['2024-01-01T10:00:00', '2024-01-01T10:15:00', '2024-01-01T10:30:00'],
        'pH': [7.5, 6.8, 8.2],
        'temp': [12.5, 13.1, 11.9],
        'pH_sd': [0.05, 0.12, 0.08],
        'location': ['Vent_A', 'Vent_B', 'Vent_C'],
        'fastq_path': ['data/raw/S001.fastq', 'data/raw/S002.fastq', 'data/raw/S003.fastq'],
        'deployment_event': ['E001', 'E001', 'E001'],
        'sensor_id': ['SENS_01', 'SENS_01', 'SENS_02'],
        'coordinates': ['45.123,-123.456', '45.124,-123.457', '45.125,-123.458']
    })


@pytest.fixture
def otu_data() -> Dict[str, Any]:
    """Generate mock OTU table data for testing."""
    return {
        'otu_table': {
            'S001': {'OTU_001': 100, 'OTU_002': 50},
            'S002': {'OTU_001': 80, 'OTU_002': 60},
            'S003': {'OTU_001': 120, 'OTU_002': 40}
        },
        'taxonomy': {
            'OTU_001': 'Bacteria;Proteobacteria;Gammaproteobacteria;Vibrionales;Vibrionaceae;Vibrio;Vibrio_1',
            'OTU_002': 'Bacteria;Firmicutes;Bacilli;Bacillales;Staphylococcaceae;Staphylococcus;Staphylococcus_1'
        },
        'sample_ids': ['S001', 'S002', 'S003'],
        'otu_ids': ['OTU_001', 'OTU_002']
    }


@pytest.fixture
def diversity_metric_data() -> pd.DataFrame:
    """Generate mock diversity metric data for testing."""
    return pd.DataFrame({
        'sample_id': ['S001', 'S002', 'S003'],
        'shannon': [2.5, 2.1, 2.8],
        'simpson': [0.85, 0.78, 0.92],
        'observed_otus': [50, 45, 60],
        'chao1': [55.2, 48.7, 62.1],
        'rarefaction_depth': [1000, 1000, 1000],
        'transformed': [False, False, False]
    })


@pytest.fixture
def test_log_handler(tmp_path) -> logging.Handler:
    """Create a test log handler that writes to a temporary file."""
    log_file = tmp_path / "test.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    return handler


def configure_test_logging(test_log_handler: logging.Handler):
    """Configure logging for tests."""
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(test_log_handler)
    return logger
