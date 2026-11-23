"""
Pytest configuration and shared fixtures for the Submarine Hydrothermal Vent project.

This module sets up the test environment, including logging configuration,
temporary directories for test outputs, and shared fixtures for data models.
"""
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Add the project root to sys.path to ensure local imports work
# This assumes the test is run from the project root or via pytest discovery
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import project modules for fixtures
from code.data_models import Sample, OTU, DiversityMetric
from code.utils import setup_logging, get_logger


# Configure pytest logging to show output during tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


@pytest.fixture(scope="session")
def test_log_handler() -> Generator[logging.Handler, None, None]:
    """
    Provides a stream handler for capturing logs during tests.
    Ensures logs are visible in test output without polluting the main application logs.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(name)s: %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger = get_logger()
    logger.addHandler(handler)
    
    yield handler
    
    logger.removeHandler(handler)


@pytest.fixture(scope="function")
def temp_output_dir() -> Generator[Path, None, None]:
    """
    Creates a temporary directory for test outputs (CSVs, logs, etc.).
    The directory is automatically cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def sample_data(temp_output_dir: Path) -> Sample:
    """
    Creates a valid Sample instance with realistic test data.
    Uses the Sample dataclass from code/data_models.
    """
    return Sample(
        sample_id="TEST_001",
        timestamp="2023-10-27T10:00:00",
        ph=7.2,
        temperature=12.5,
        location="East Pacific Rise",
        deployment_event="EPR-2023-A",
        sensor_id="SENS-001",
        coordinates=(12.5, -104.5),
        fastq_path=str(temp_output_dir / "test_sample.fastq.gz"),
        ph_heterogeneous=False,
        ph_sd=0.05
    )


@pytest.fixture(scope="function")
def otu_data() -> OTU:
    """
    Creates a valid OTU instance with test data.
    """
    return OTU(
        otu_id="OTU_001",
        sequence="ATCGATCGATCG",
        taxonomy=["Bacteria", "Proteobacteria", "Gamma"],
        counts={
            "TEST_001": 150,
            "TEST_002": 200
        }
    )


@pytest.fixture(scope="function")
def diversity_metric_data() -> DiversityMetric:
    """
    Creates a valid DiversityMetric instance.
    """
    return DiversityMetric(
        sample_id="TEST_001",
        shannon_index=3.45,
        simpson_index=0.89,
        observed_otus=45,
        calculated_at="2023-10-27T11:00:00"
    )


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """
    Automatically configures logging for the test session.
    """
    setup_logging(level=logging.INFO, log_to_console=True)
    yield
    # Teardown if necessary