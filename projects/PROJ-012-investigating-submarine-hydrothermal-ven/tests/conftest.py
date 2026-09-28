"""
Pytest configuration and shared fixtures for the llmXive submarine hydrothermal vent project.

This module provides:
- Logging configuration for test runs
- Temporary output directory management
- Mock data fixtures for Sample, OTU, and DiversityMetric entities
- Shared test utilities
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any, List

import pytest
import pandas as pd
import numpy as np

# Add project root to path to ensure imports work during tests
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules for fixture usage
try:
    from data_models import Sample, OTU, DiversityMetric
except ImportError:
    # Fallback if data_models not yet imported correctly
    Sample = None
    OTU = None
    DiversityMetric = None

def pytest_configure(config):
    """
    Configure pytest with custom markers and initial settings.
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
    config.addinivalue_line(
        "markers", "contract: marks tests as contract/schema validation tests"
    )

@pytest.fixture(scope="session")
def test_log_handler() -> Generator[logging.Handler, None, None]:
    """
    Provide a temporary logging handler for test output.
    Captures logs during test execution without polluting global logging state.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger('test_runner')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield handler
    
    logger.removeHandler(handler)
    handler.close()

@pytest.fixture(scope="function")
def temp_output_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test outputs.
    Ensures clean state for each test and cleanup after.
    """
    with tempfile.TemporaryDirectory(prefix="llmxive_test_") as tmp_dir:
        output_path = Path(tmp_dir)
        # Create standard subdirectories
        (output_path / "processed").mkdir(exist_ok=True)
        (output_path / "raw").mkdir(exist_ok=True)
        (output_path / "figures").mkdir(exist_ok=True)
        yield output_path

@pytest.fixture
def sample_data() -> List[Dict[str, Any]]:
    """
    Provide mock sample data for ingestion and analysis tests.
    Includes realistic pH, temperature, and metadata fields.
    """
    return [
        {
            "sample_id": "S001",
            "timestamp": "2023-06-15T10:30:00Z",
            "pH": 6.8,
            "temp": 345.5,
            "location": "East Pacific Rise",
            "deployment_event": "E001",
            "sensor_id": "SENS-001",
            "coordinates": "21.5N, 110.5W",
            "fastq_path": "data/raw/sample_S001.fastq.gz"
        },
        {
            "sample_id": "S002",
            "timestamp": "2023-06-15T10:45:00Z",
            "pH": 7.2,
            "temp": 340.2,
            "location": "East Pacific Rise",
            "deployment_event": "E001",
            "sensor_id": "SENS-001",
            "coordinates": "21.5N, 110.5W",
            "fastq_path": "data/raw/sample_S002.fastq.gz"
        },
        {
            "sample_id": "S003",
            "timestamp": "2023-06-15T11:00:00Z",
            "pH": 5.5,  # Edge case: acidic
            "temp": 350.0,
            "location": "Mid-Atlantic Ridge",
            "deployment_event": "E002",
            "sensor_id": "SENS-002",
            "coordinates": "25.0N, 45.0W",
            "fastq_path": "data/raw/sample_S003.fastq.gz"
        },
        {
            "sample_id": "S004",
            "timestamp": "2023-06-15T11:15:00Z",
            "pH": 9.5,  # Edge case: alkaline
            "temp": 330.1,
            "location": "Mid-Atlantic Ridge",
            "deployment_event": "E002",
            "sensor_id": "SENS-002",
            "coordinates": "25.0N, 45.0W",
            "fastq_path": "data/raw/sample_S004.fastq.gz"
        },
        {
            "sample_id": "S005",
            "timestamp": "2023-06-15T11:30:00Z",
            "pH": 10.5,  # Outlier: > 10.0
            "temp": 325.0,
            "location": "Juan de Fuca Ridge",
            "deployment_event": "E003",
            "sensor_id": "SENS-003",
            "coordinates": "45.0N, 130.0W",
            "fastq_path": "data/raw/sample_S005.fastq.gz"
        }
    ]

@pytest.fixture
def otu_data() -> pd.DataFrame:
    """
    Provide mock OTU/ASV table data for diversity analysis tests.
    Format: Rows = samples, Columns = OTUs/ASVs.
    """
    np.random.seed(42)
    samples = ["S001", "S002", "S003", "S004", "S005"]
    otus = [f"OTU_{i:04d}" for i in range(1, 101)]
    
    # Generate sparse count data (typical for microbiome)
    data = np.random.negative_binomial(n=5, p=0.1, size=(len(samples), len(otus)))
    
    df = pd.DataFrame(data, index=samples, columns=otus)
    return df

@pytest.fixture
def diversity_metric_data() -> pd.DataFrame:
    """
    Provide mock diversity metrics for correlation analysis tests.
    Includes Shannon and Simpson indices.
    """
    np.random.seed(42)
    samples = ["S001", "S002", "S003", "S004", "S005"]
    ph_values = [6.8, 7.2, 5.5, 9.5, 10.5]
    
    # Generate correlated diversity metrics
    shannon = np.random.normal(loc=3.5, scale=0.5, size=len(samples))
    simpson = 1 - np.random.beta(alpha=2, beta=5, size=len(samples))
    
    df = pd.DataFrame({
        "sample_id": samples,
        "pH": ph_values,
        "shannon_diversity": shannon,
        "simpson_diversity": simpson,
        "site": ["EPR", "EPR", "MAR", "MAR", "JdFR"]
    })
    return df

@pytest.fixture
def mock_ingestion_input(temp_output_dir: Path) -> Path:
    """
    Create a mock directory structure with CSV files for ingestion testing.
    Returns the path to the mock data directory.
    """
    mock_dir = temp_output_dir / "mock_ingestion"
    mock_dir.mkdir(parents=True, exist_ok=True)
    
    # Create pH CSV
    ph_df = pd.DataFrame({
        "deployment_event": ["E001", "E001", "E002", "E002"],
        "sensor_id": ["SENS-001", "SENS-001", "SENS-002", "SENS-002"],
        "timestamp": [
            "2023-06-15T10:30:00Z",
            "2023-06-15T10:45:00Z",
            "2023-06-15T11:00:00Z",
            "2023-06-15T11:15:00Z"
        ],
        "pH": [6.8, 7.2, 5.5, 9.5],
        "coordinates": ["21.5N, 110.5W", "21.5N, 110.5W", "25.0N, 45.0W", "25.0N, 45.0W"]
    })
    ph_df.to_csv(mock_dir / "pH_log.csv", index=False)
    
    # Create Temp CSV
    temp_df = pd.DataFrame({
        "deployment_event": ["E001", "E001", "E002", "E002"],
        "sensor_id": ["SENS-001", "SENS-001", "SENS-002", "SENS-002"],
        "timestamp": [
            "2023-06-15T10:30:00Z",
            "2023-06-15T10:45:00Z",
            "2023-06-15T11:00:00Z",
            "2023-06-15T11:15:00Z"
        ],
        "temp": [345.5, 340.2, 350.0, 330.1],
        "coordinates": ["21.5N, 110.5W", "21.5N, 110.5W", "25.0N, 45.0W", "25.0N, 45.0W"]
    })
    temp_df.to_csv(mock_dir / "temp_log.csv", index=False)
    
    return mock_dir

def configure_test_logging(level: int = logging.DEBUG):
    """
    Configure root logging for test environment.
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )