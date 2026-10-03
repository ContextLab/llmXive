"""
Pytest configuration and shared fixtures for the llmXive submarine hydrothermal vent project.

This module provides:
- Global pytest configuration hooks
- Shared logging handlers for test execution
- Temporary output directories for test artifacts
- Mock data fixtures for Sample, OTU, and DiversityMetric entities
- Logging configuration for test isolation
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import pandas as pd
import numpy as np

# Import project modules for fixture creation
# Note: We assume these are installed or in the path when running tests
try:
    from code.data_models import Sample, OTU, DiversityMetric
    from code.utils import setup_logging, get_logger
except ImportError:
    # Fallback for direct pytest run without full package install
    # In CI/CD, the path will be configured correctly
    pass

# ============================================================================
# Pytest Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest at startup.
    
    Sets up custom markers and initial configuration.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "contract: marks tests as contract/schema validation tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

# ============================================================================
# Shared Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_log_handler() -> logging.Handler:
    """
    Provide a shared logging handler for test execution.
    
    Returns:
        A StreamHandler configured for test output.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    return handler

@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provide a temporary directory for test output artifacts.
    
    This fixture ensures that test outputs do not pollute the project
    data directories. The directory is automatically cleaned up after
    the test.
    
    Args:
        tmp_path: Pytest's built-in temporary path fixture.
        
    Yields:
        A Path object pointing to the temporary directory.
    """
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir
    # Cleanup happens automatically when tmp_path is destroyed

@pytest.fixture
def sample_data() -> Dict[str, Any]:
    """
    Provide mock Sample data for testing ingestion and validation.
    
    Returns:
        Dictionary containing a list of mock Sample records.
    """
    return {
        "samples": [
            {
                "sample_id": "SAMPLE_001",
                "timestamp": "2023-05-15T10:30:00",
                "pH": 6.8,
                "temperature": 350.5,
                "location": "East_Pacific_Rise",
                "deployment_event": "EXP_2023_A",
                "sensor_id": "SENSOR_A1",
                "coordinates": {"lat": -23.5, "lon": -110.5, "depth": 2500},
                "fastq_path": "data/raw/fastq/SAMPLE_001_R1.fastq.gz"
            },
            {
                "sample_id": "SAMPLE_002",
                "timestamp": "2023-05-15T10:45:00",
                "pH": 7.2,
                "temperature": 345.0,
                "location": "East_Pacific_Rise",
                "deployment_event": "EXP_2023_A",
                "sensor_id": "SENSOR_A1",
                "coordinates": {"lat": -23.5, "lon": -110.5, "depth": 2500},
                "fastq_path": "data/raw/fastq/SAMPLE_002_R1.fastq.gz"
            },
            {
                "sample_id": "SAMPLE_003",
                "timestamp": "2023-05-15T11:00:00",
                "pH": 5.5,  # Edge case: acidic
                "temperature": 360.2,
                "location": "Juan_de_Fuca_Ridge",
                "deployment_event": "EXP_2023_B",
                "sensor_id": "SENSOR_B2",
                "coordinates": {"lat": 44.5, "lon": -130.0, "depth": 2800},
                "fastq_path": "data/raw/fastq/SAMPLE_003_R1.fastq.gz"
            },
            {
                "sample_id": "SAMPLE_004",
                "timestamp": "2023-05-15T11:15:00",
                "pH": 9.8,  # Edge case: alkaline
                "temperature": 340.0,
                "location": "Mid_Atlantic_Ridge",
                "deployment_event": "EXP_2023_C",
                "sensor_id": "SENSOR_C3",
                "coordinates": {"lat": 25.0, "lon": -45.0, "depth": 3000},
                "fastq_path": "data/raw/fastq/SAMPLE_004_R1.fastq.gz"
            }
        ]
    }

@pytest.fixture
def otu_data() -> Dict[str, Any]:
    """
    Provide mock OTU/ASV table data for testing diversity calculations.
    
    Returns:
        Dictionary containing a mock OTU table as a pandas DataFrame.
    """
    # Create a mock OTU table with samples as rows and OTUs as columns
    data = {
        "OTU_001": [100, 150, 50, 200],
        "OTU_002": [50, 80, 20, 100],
        "OTU_003": [200, 300, 100, 400],
        "OTU_004": [10, 15, 5, 25],
        "OTU_005": [30, 45, 15, 60],
    }
    index = ["SAMPLE_001", "SAMPLE_002", "SAMPLE_003", "SAMPLE_004"]
    df = pd.DataFrame(data, index=index)
    return {
        "table": df,
        "metadata": {
            "rarefaction_depth": 1000,
            "min_reads": 10,
            "max_reads": 10000
        }
    }

@pytest.fixture
def diversity_metric_data() -> Dict[str, Any]:
    """
    Provide mock DiversityMetric data for testing analysis pipelines.
    
    Returns:
        Dictionary containing mock diversity metrics.
    """
    return {
        "metrics": [
            {
                "sample_id": "SAMPLE_001",
                "shannon": 2.5,
                "simpson": 0.85,
                "observed_otus": 50,
                "pH": 6.8,
                "temperature": 350.5,
                "site": "East_Pacific_Rise"
            },
            {
                "sample_id": "SAMPLE_002",
                "shannon": 2.7,
                "simpson": 0.88,
                "observed_otus": 55,
                "pH": 7.2,
                "temperature": 345.0,
                "site": "East_Pacific_Rise"
            },
            {
                "sample_id": "SAMPLE_003",
                "shannon": 1.8,
                "simpson": 0.70,
                "observed_otus": 30,
                "pH": 5.5,
                "temperature": 360.2,
                "site": "Juan_de_Fuca_Ridge"
            },
            {
                "sample_id": "SAMPLE_004",
                "shannon": 2.9,
                "simpson": 0.92,
                "observed_otus": 60,
                "pH": 9.8,
                "temperature": 340.0,
                "site": "Mid_Atlantic_Ridge"
            }
        ]
    }

# ============================================================================
# Test-Specific Fixtures
# ============================================================================

@pytest.fixture
def config_for_test() -> Dict[str, Any]:
    """
    Provide a configuration dictionary for test runs.
    
    Returns:
        Dictionary with default test configuration.
    """
    return {
        "output_dir": "tests/temp_output",
        "log_level": "INFO",
        "random_seed": 42,
        "parallel_workers": 1,
        "validation_strict": True
    }

# ============================================================================
# Helper Functions for Tests
# ============================================================================

def configure_test_logging(handler: logging.Handler) -> None:
    """
    Configure logging for the current test module.
    
    Args:
        handler: The logging handler to attach.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.addHandler(handler)