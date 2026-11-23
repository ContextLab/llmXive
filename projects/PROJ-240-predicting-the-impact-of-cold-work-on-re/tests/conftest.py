"""
Pytest configuration and shared fixtures for the llmXive project.

This module provides fixtures for test isolation, data paths, and
reusable test utilities.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add the code directory to the path so imports work during tests
# This assumes the project root is the parent of 'code' and 'tests'
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def code_dir():
    """Return the code directory path."""
    return CODE_DIR


@pytest.fixture(scope="session")
def data_dir():
    """Return the data directory path."""
    return DATA_DIR


@pytest.fixture(scope="session")
def artifacts_dir():
    """Return the artifacts directory path."""
    return ARTIFACTS_DIR


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Create a temporary directory for test outputs.
    
    Returns the Path to the temporary directory.
    """
    return tmp_path


@pytest.fixture
def sample_synthetic_data_path(data_dir):
    """
    Return the path to the synthetic baseline data.
    
    This fixture assumes the data generator (T007) has run and
    produced data/raw/synthetic_baseline.csv.
    """
    path = data_dir / "raw" / "synthetic_baseline.csv"
    if not path.exists():
        pytest.skip(f"Synthetic data file not found at {path}. Run T007 first.")
    return path


@pytest.fixture
def sample_validated_data_path(data_dir):
    """
    Return the path to the validated processed data.
    
    This fixture assumes the ingestion pipeline (T012) has run and
    produced data/processed/validated.csv.
    """
    path = data_dir / "processed" / "validated.csv"
    if not path.exists():
        pytest.skip(f"Validated data file not found at {path}. Run T012 first.")
    return path


@pytest.fixture
def sample_engineered_data_path(data_dir):
    """
    Return the path to the engineered features data.
    
    This fixture assumes the engineering pipeline (T018) has run and
    produced data/processed/engineered_features.csv.
    """
    path = data_dir / "processed" / "engineered_features.csv"
    if not path.exists():
        pytest.skip(f"Engineered data file not found at {path}. Run T018 first.")
    return path


@pytest.fixture
def sample_final_dataset_path(data_dir):
    """
    Return the path to the final dataset.
    
    This fixture assumes the finalization pipeline (T020) has run and
    produced data/processed/final_dataset.csv.
    """
    path = data_dir / "processed" / "final_dataset.csv"
    if not path.exists():
        pytest.skip(f"Final dataset file not found at {path}. Run T020 first.")
    return path


@pytest.fixture
def sample_trained_model_path(artifacts_dir):
    """
    Return the path to the trained model artifact.
    
    This fixture assumes the training pipeline (T027) has run and
    produced artifacts/models/kinetic_model.pkl.
    """
    path = artifacts_dir / "models" / "kinetic_model.pkl"
    if not path.exists():
        pytest.skip(f"Trained model file not found at {path}. Run T027 first.")
    return path


@pytest.fixture
def config_constants():
    """
    Return common configuration constants used in tests.
    """
    return {
        "SEED": 42,
        "TEST_SIZE": 0.2,
        "N_PERMUTATIONS": 1000,
        "MIN_ROWS": 50,
        "MAX_ROWS": 10000,
    }