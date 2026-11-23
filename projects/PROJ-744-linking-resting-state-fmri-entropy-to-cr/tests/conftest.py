"""
Shared pytest fixtures for the llmXive fMRI Entropy project.

Provides:
- Temporary directory structure mimicking the project layout.
- Mock entropy vectors for unit testing without loading large NIfTI files.
- Helper paths for data and logs during test execution.
"""
import os
import tempfile
import shutil
import pytest
import numpy as np
from pathlib import Path
import pandas as pd

# Ensure we can import from the code/ directory if tests are run from root
# Adjust PYTHONPATH if necessary, though pytest usually handles this via conftest location
import sys
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

@pytest.fixture(scope="session")
def test_data_dir():
    """
    Creates a temporary directory structure mimicking the project's data layout.
    Yields the path and ensures cleanup after tests.
    """
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
    try:
        # Create subdirectories expected by the code
        (Path(temp_dir) / "raw").mkdir(parents=True)
        (Path(temp_dir) / "processed").mkdir(parents=True)
        (Path(temp_dir) / "logs").mkdir(parents=True)
        yield temp_dir
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@pytest.fixture
def sample_entropy_vector():
    """
    Returns a deterministic 1D numpy array suitable for testing entropy calculations.
    Uses a known pattern to ensure reproducible results across test runs.
    """
    # A simple chaotic-like sequence generated from a logistic map for reproducibility
    # r=3.9, x0=0.5, N=1000
    r = 3.9
    x = 0.5
    sequence = []
    for _ in range(1000):
        x = r * x * (1 - x)
        sequence.append(x)
    return np.array(sequence, dtype=np.float64)

@pytest.fixture
def sample_multiscale_data():
    """
    Returns a 2D numpy array (subjects x timepoints) for multiscale entropy testing.
    """
    np.random.seed(42)
    # 10 subjects, 200 timepoints
    return np.random.randn(10, 200) * 0.5

@pytest.fixture
def mock_config_paths(test_data_dir):
    """
    Returns a dictionary of paths pointing to the temporary test directories.
    Useful for mocking Config class behavior in tests.
    """
    return {
        "RAW_DATA_DIR": str(Path(test_data_dir) / "raw"),
        "PROCESSED_DATA_DIR": str(Path(test_data_dir) / "processed"),
        "LOGS_DIR": str(Path(test_data_dir) / "logs"),
        "PHENOTYPE_PATH": str(Path(test_data_dir) / "processed" / "fake_phenotype.csv"),
    }

@pytest.fixture
def mock_valid_subjects_df():
    """
    Returns a DataFrame mimicking the structure of data/processed/valid_subjects.csv.
    """
    data = {
        "subject_id": [f"100307_{i:03d}" for i in range(10)],
        "is_valid": [True] * 10
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_atlas_mapping():
    """
    Returns a dictionary mapping parcel indices to network names.
    Simulates the HCP 360-parcel atlas structure for unit tests.
    """
    return {
        "DMN": list(range(0, 20)),
        "FPN": list(range(20, 40)),
        "CON": list(range(40, 60)),
        "VISUAL": list(range(60, 80)),
    }