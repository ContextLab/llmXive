"""
Pytest configuration and fixtures for the llmXive pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path for imports
# This assumes conftest.py is in code/ or tests/ and we want to import from code/
project_root = Path(__file__).parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

@pytest.fixture
def ci_mode_env(monkeypatch):
    """Fixture to set CI_MODE environment variable for testing."""
    monkeypatch.setenv("CI_MODE", "true")
    return os.environ.get("CI_MODE")

@pytest.fixture
def mock_data_dir(tmp_path):
    """Fixture to create a temporary directory with mock data files."""
    mock_dir = tmp_path / "data" / "raw"
    mock_dir.mkdir(parents=True)
    return mock_dir

@pytest.fixture
def sample_aligned_data():
    """Sample data structure matching the aligned_dataset schema."""
    return {
        "species_id": "9606",
        "species_name": "Homo sapiens",
        "bgc_counts": {"NRPS": 10, "PKS": 5},
        "metabolite_abundances": {"InChIKey1": 1.23, "InChIKey2": 4.56}
    }

@pytest.fixture
def sample_model_results():
    """Sample data structure matching the model_results schema."""
    return {
        "model_type": "RandomForest",
        "cross_validation": {
            "r2_mean": 0.75,
            "r2_std": 0.05,
            "mse_mean": 0.12,
            "fold_scores": [0.72, 0.78, 0.74, 0.76, 0.75]
        },
        "pvr_results": {
            "eigenvectors_used": 3,
            "r2_adjusted": 0.70,
            "p_value": 0.02
        },
        "permutation_test": {
            "iterations": 100,
            "null_distribution_mean": 0.05,
            "observed_statistic": 0.75,
            "p_value": 0.01
        }
    }
