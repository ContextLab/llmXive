"""
Shared pytest fixtures for the llmXive fMRI entropy project.

This module provides reusable fixtures for test data paths, mock entropy vectors,
and configuration overrides to ensure consistent test environments.
"""
import os
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import project config to ensure path consistency
try:
    from config import Config
except ImportError:
    # Fallback if running in a context where config isn't directly importable
    # but usually config is in code/ and tests are in tests/
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import Config


@pytest.fixture(scope="session")
def project_root():
    """Return the root directory of the project."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"


@pytest.fixture(scope="session")
def raw_data_dir(data_dir):
    """Return the raw data directory path."""
    return data_dir / "raw"


@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    """Return the processed data directory path."""
    return data_dir / "processed"


@pytest.fixture(scope="session")
def logs_dir(data_dir):
    """Return the logs directory path."""
    return data_dir / "logs"


@pytest.fixture(scope="function")
def temp_output_dir():
    """Create a temporary directory for test outputs that are cleaned up after."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_entropy_vector():
    """
    Generate a deterministic sample entropy vector for testing.
    
    Returns a 1D numpy array of float64 values representing a time series.
    Values are generated using a fixed seed to ensure reproducibility.
    """
    np.random.seed(42)
    # Simulate a short fMRI-like time series (500 time points)
    # Mix of sine wave and noise to create some structure
    t = np.linspace(0, 10, 500)
    signal = np.sin(t) + 0.5 * np.cos(2 * t) + 0.1 * np.random.randn(500)
    return signal.astype(np.float64)


@pytest.fixture
def sample_multiscale_data():
    """
    Generate a 2D matrix representing multiscale entropy input.
    
    Returns a 2D numpy array (subjects x timepoints) for testing
    multiscale entropy calculations.
    """
    np.random.seed(123)
    n_subjects = 5
    n_timepoints = 200
    # Create varied signals for different subjects
    data = np.zeros((n_subjects, n_timepoints))
    for i in range(n_subjects):
        t = np.linspace(0, 5 * (i + 1), n_timepoints)
        data[i] = np.sin(t) + 0.2 * np.random.randn(n_timepoints)
    return data.astype(np.float64)


@pytest.fixture
def mock_config_paths(temp_output_dir):
    """
    Override Config paths to point to temporary directories for testing.
    
    Yields a modified Config object or a dictionary of paths pointing to temp locations.
    """
    original_phenotype = Config.PHENOTYPE_PATH
    original_raw = Config.RAW_DATA_DIR
    original_processed = Config.PROCESSED_DATA_DIR
    
    # Set temp paths
    Config.PHENOTYPE_PATH = temp_output_dir / "test_phenotype.csv"
    Config.RAW_DATA_DIR = temp_output_dir / "raw"
    Config.PROCESSED_DATA_DIR = temp_output_dir / "processed"
    
    # Ensure dirs exist
    Config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    Config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    yield Config
    
    # Restore original paths
    Config.PHENOTYPE_PATH = original_phenotype
    Config.RAW_DATA_DIR = original_raw
    Config.PROCESSED_DATA_DIR = original_processed


@pytest.fixture
def sample_parcels_data(sample_entropy_vector):
    """
    Create a mock parcel-level entropy dataset.
    
    Returns a pandas DataFrame with mock entropy values for multiple parcels.
    """
    n_parcels = 360  # HCP 360-parcel atlas
    np.random.seed(42)
    
    # Create mock data: some valid, some NaN to test filtering
    entropy_values = np.random.rand(n_parcels) * 2.0
    # Introduce ~5% NaNs
    nan_indices = np.random.choice(n_parcels, size=int(n_parcels * 0.05), replace=False)
    entropy_values[nan_indices] = np.nan
    
    df = pd.DataFrame({
        "parcel_id": range(1, n_parcels + 1),
        "entropy_value": entropy_values,
        "subject_id": "test_sub_001"
    })
    return df


@pytest.fixture
def sample_network_mapping():
    """
    Provide a mock mapping of parcels to networks.
    
    Returns a dictionary mapping network names to lists of parcel IDs.
    """
    return {
        "DMN": list(range(1, 61)),
        "FPN": list(range(61, 121)),
        "CON": list(range(121, 181)),
        "VIS": list(range(181, 241)),
        "SM": list(range(241, 301)),
        "AUD": list(range(301, 361))
    }


@pytest.fixture
def mock_phenotype_csv(temp_output_dir):
    """
    Create a mock phenotype CSV file for testing data loading.
    
    Returns the path to the created CSV file.
    """
    data = {
        "subject_id": [f"sub_{i:03d}" for i in range(1, 11)],
        "age": [22, 24, 21, 25, 23, 22, 24, 21, 26, 23],
        "sex": ["M", "F", "M", "F", "M", "F", "M", "F", "M", "F"],
        "creative_score": [8.5, 9.2, 7.8, 8.9, 8.1, 9.0, 7.5, 8.8, 9.3, 8.2]
    }
    df = pd.DataFrame(data)
    path = temp_output_dir / "Creative_Problem_Solving.csv"
    df.to_csv(path, index=False)
    return path
