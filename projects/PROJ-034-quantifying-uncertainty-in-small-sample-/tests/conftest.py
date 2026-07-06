"""
Shared fixtures and configuration for the llmXive project tests.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

import pytest
import numpy as np
from numpy.typing import ArrayLike

# Ensure the project root is in the path so imports work
# This assumes tests are at project_root/tests/ and code is at project_root/code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from simulation.config import SimulationConfig
from simulation.engine import DatasetInstance, generate_dataset, calculate_vif


@pytest.fixture(scope="session")
def temp_project_root() -> Iterator[Path]:
    """
    Creates a temporary directory to act as the project root for testing.
    This isolates file I/O tests from the actual repository.
    """
    tmp_dir = tempfile.mkdtemp(prefix="llmXive_test_")
    tmp_path = Path(tmp_dir)
    
    # Create necessary subdirectories
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "simulated").mkdir(parents=True)
    (tmp_path / "data" / "results").mkdir(parents=True)
    (tmp_path / "code").mkdir(parents=True)
    (tmp_path / "tests").mkdir(parents=True)

    yield tmp_path

    # Cleanup
    shutil.rmtree(tmp_dir)


@pytest.fixture
def sample_config() -> SimulationConfig:
    """
    Provides a standard SimulationConfig for small sample testing.
    N=20, 3 predictors, low correlation, standard noise.
    """
    return SimulationConfig(
        n=20,
        n_predictors=3,
        correlation=0.2,
        noise_std=1.0,
        true_coefficients=[1.5, -2.0, 0.5],
        seed=42
    )


@pytest.fixture
def sample_dataset(sample_config: SimulationConfig) -> DatasetInstance:
    """
    Generates a valid DatasetInstance using the sample_config.
    """
    return generate_dataset(sample_config)


@pytest.fixture
def high_corr_config() -> SimulationConfig:
    """
    Configuration designed to produce high VIF (collinearity).
    """
    return SimulationConfig(
        n=20,
        n_predictors=3,
        correlation=0.95,  # High correlation
        noise_std=1.0,
        true_coefficients=[1.0, 1.0, 1.0],
        seed=123
    )


@pytest.fixture
def low_sample_config() -> SimulationConfig:
    """
    Configuration with very low N to test rank-deficiency handling.
    """
    return SimulationConfig(
        n=5,
        n_predictors=3,
        correlation=0.1,
        noise_std=1.0,
        true_coefficients=[1.0, 1.0, 1.0],
        seed=999
    )


@pytest.fixture
def mock_output_dir(temp_project_root: Path) -> Path:
    """
    Returns a specific directory within the temp root for saving outputs.
    """
    output_dir = temp_project_root / "data" / "simulated"
    return output_dir