"""
Shared pytest fixtures for the llmXive automated science pipeline.

This module provides reusable fixtures for:
- Project directory structure setup
- Sample data generation for unit/integration tests
- Temporary directories for test artifacts

All fixtures use the project's root directory structure as defined in T001.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure the code directory is in the Python path for imports
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.logger import get_logger

# Initialize logger for test fixtures
_logger = get_logger("conftest")

@pytest.fixture(scope="session")
def project_root():
    """
    Returns the project root directory.
    
    In a real execution environment, this would be the actual project root.
    For testing, we use a temporary directory that mimics the structure.
    """
    # For unit tests, we use the actual code directory as root if running from there,
    # otherwise we create a temp structure.
    # Here we assume the test is run from the project root or code/ directory.
    # We try to detect the project root by looking for 'data' or 'src' directories.
    
    current = Path(__file__).parent.parent
    # Check if we are in 'code' directory
    if (current / 'src').exists() and (current / 'data').exists():
        return current
    
    # Fallback: use a temporary directory with the required structure
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
    temp_path = Path(temp_dir)
    
    # Create required directories per T001
    dirs = [
        "src/ingestion", "src/preprocessing", "src/analysis", "src/utils",
        "tests/contract", "tests/integration", "tests/unit",
        "data/raw", "data/processed", "data/processed/results",
        "docs", "state"
    ]
    for d in dirs:
        (temp_path / d).mkdir(parents=True, exist_ok=True)
    
    _logger.info(f"Created temporary project root at {temp_path}")
    return temp_path

@pytest.fixture
def data_dir(project_root):
    """Returns the data directory."""
    return project_root / "data"

@pytest.fixture
def processed_dir(project_root):
    """Returns the processed data directory."""
    return project_root / "data" / "processed"

@pytest.fixture
def results_dir(project_root):
    """Returns the results directory."""
    return project_root / "data" / "processed" / "results"

@pytest.fixture
def temp_dir():
    """Creates a temporary directory for test-specific artifacts."""
    temp_path = tempfile.mkdtemp(prefix="llmxive_test_artifact_")
    yield Path(temp_path)
    # Cleanup after test
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def sample_agp_df():
    """
    Generates a sample DataFrame mimicking the American Gut Project (AGP) data structure.
    
    Includes:
    - sample_id
    - fiber_g_day (intake in grams per day)
    - read_count (sequencing depth)
    - cohort_id (set to 'AGP')
    - Some taxon abundance columns (mocked)
    - Covariates (age, bmi, antibiotic_use)
    """
    np.random.seed(42)  # For reproducibility
    n_samples = 50
    
    data = {
        "sample_id": [f"AGP_{i:04d}" for i in range(n_samples)],
        "fiber_g_day": np.random.uniform(5, 50, n_samples),
        "read_count": np.random.randint(5000, 50000, n_samples),
        "cohort_id": ["AGP"] * n_samples,
        "age": np.random.randint(20, 70, n_samples),
        "bmi": np.random.uniform(18.5, 35.0, n_samples),
        "antibiotic_use": np.random.choice([0, 1], n_samples),
        # Mock taxon abundances (relative)
        "Bacteroides": np.random.dirichlet(np.ones(10), n_samples)[:, 0],
        "Prevotella": np.random.dirichlet(np.ones(10), n_samples)[:, 1],
        "Faecalibacterium": np.random.dirichlet(np.ones(10), n_samples)[:, 2],
    }
    
    # Add some missing values to test imputation logic
    data["age"][5] = np.nan
    data["bmi"][10] = np.nan
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_ukbb_df():
    """
    Generates a sample DataFrame mimicking the UK Biobank (UKBB) data structure.
    
    Similar to AGP but with 'UKBB' cohort ID and slightly different distributions.
    """
    np.random.seed(123)  # Different seed for variety
    n_samples = 50
    
    data = {
        "sample_id": [f"UKBB_{i:04d}" for i in range(n_samples)],
        "fiber_g_day": np.random.uniform(10, 60, n_samples),  # Slightly higher intake
        "read_count": np.random.randint(10000, 100000, n_samples),
        "cohort_id": ["UKBB"] * n_samples,
        "age": np.random.randint(30, 80, n_samples),
        "bmi": np.random.uniform(20.0, 40.0, n_samples),
        "antibiotic_use": np.random.choice([0, 1], n_samples),
        # Mock taxon abundances
        "Bacteroides": np.random.dirichlet(np.ones(10), n_samples)[:, 0],
        "Prevotella": np.random.dirichlet(np.ones(10), n_samples)[:, 1],
        "Faecalibacterium": np.random.dirichlet(np.ones(10), n_samples)[:, 2],
    }
    
    # Add some missing values
    data["age"][3] = np.nan
    data["antibiotic_use"][15] = np.nan
    
    return pd.DataFrame(data)

@pytest.fixture
def setup_path():
    """
    Provides the path to the setup script (src/setup_data_structure.py).
    Useful for tests that need to verify directory creation logic.
    """
    return Path(__file__).parent.parent / "src" / "setup_data_structure.py"