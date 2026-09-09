"""
Pytest configuration and fixtures for the llmXive chaotic systems project.

This module provides shared fixtures for:
1. Random seed management to ensure reproducibility
2. Temporary data directories for isolated test execution
3. Configuration fixtures for common test scenarios
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any, Optional
import pytest
import numpy as np

# Add the project root to the path so imports work correctly
# This assumes tests/ is at the same level as code/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_full_config, SimulationConfig, AnalysisConfig, NumericalSettings


@pytest.fixture(autouse=True)
def setup_environment() -> Generator[None, None, None]:
    """
    Autouse fixture to set up environment variables and paths before tests.
    Ensures consistent environment across all tests.
    """
    # Set a default test seed if not already set
    if "TEST_SEED" not in os.environ:
        os.environ["TEST_SEED"] = "42"
    
    # Set project root path
    os.environ["PROJECT_ROOT"] = str(project_root)
    
    yield
    
    # Cleanup after tests if needed
    pass


@pytest.fixture(scope="session")
def test_seed() -> int:
    """
    Fixture providing a fixed random seed for reproducible tests.
    
    Returns:
        int: The seed value (default 42, or from TEST_SEED env var)
    """
    seed_str = os.environ.get("TEST_SEED", "42")
    try:
        return int(seed_str)
    except ValueError:
        return 42


@pytest.fixture
def random_seed(test_seed: int) -> Generator[int, None, None]:
    """
    Fixture that sets and restores the random seed for a single test.
    
    This ensures each test starts with a known random state while
    allowing the seed to be controlled via the test_seed fixture.
    
    Args:
        test_seed: The base seed value from the session fixture
    
    Yields:
        int: The seed value used for the test
    """
    # Set numpy random seed
    np.random.seed(test_seed)
    
    # Set python random seed
    import random
    random.seed(test_seed)
    
    yield test_seed
    
    # Note: We don't restore the seed here because each test
    # should start with a fresh seed anyway


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """
    Fixture creating a temporary directory for data files during tests.
    
    This ensures tests don't pollute the actual data/ directory and
    can clean up after themselves automatically.
    
    Yields:
        Path: Path to the temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix="llmXive_test_")
    temp_path = Path(temp_dir)
    
    # Create subdirectories matching project structure
    (temp_path / "raw").mkdir(parents=True, exist_ok=True)
    (temp_path / "processed").mkdir(parents=True, exist_ok=True)
    (temp_path / "state").mkdir(parents=True, exist_ok=True)
    
    yield temp_path
    
    # Cleanup: remove the temporary directory and all contents
    try:
        shutil.rmtree(temp_path)
    except Exception as e:
        # Log but don't fail the test if cleanup fails
        import warnings
        warnings.warn(f"Failed to cleanup temp directory {temp_path}: {e}")


@pytest.fixture
def sample_config(temp_data_dir: Path) -> Dict[str, Any]:
    """
    Fixture providing a sample configuration dictionary for tests.
    
    Args:
        temp_data_dir: Temporary directory fixture for data paths
    
    Returns:
        Dict with configuration values suitable for testing
    """
    return {
        "simulation": {
            "N_oscillators": 2,
            "t_max": 10.0,
            "dt": 0.01,
            "seed": 42,
        },
        "analysis": {
            "window_sizes": [100, 200, 500],
            "convergence_threshold": 1e-6,
        },
        "data_paths": {
            "raw": str(temp_data_dir / "raw"),
            "processed": str(temp_data_dir / "processed"),
            "state": str(temp_data_dir / "state"),
        },
        "noise_levels": [0.0, 0.01, 0.1],
    }


@pytest.fixture
def full_config(sample_config: Dict[str, Any]) -> SimulationConfig:
    """
    Fixture providing a full SimulationConfig object for integration tests.
    
    Args:
        sample_config: Sample configuration dictionary
    
    Returns:
        SimulationConfig: A configured simulation object
    """
    # Create a minimal valid config for testing
    return SimulationConfig(
        N=sample_config["simulation"]["N_oscillators"],
        t_max=sample_config["simulation"]["t_max"],
        dt=sample_config["simulation"]["dt"],
        seed=sample_config["simulation"]["seed"],
        noise_levels=sample_config.get("noise_levels", [0.0, 0.01]),
    )


@pytest.fixture
def analysis_config(sample_config: Dict[str, Any]) -> AnalysisConfig:
    """
    Fixture providing an AnalysisConfig object for tests.
    
    Args:
        sample_config: Sample configuration dictionary
    
    Returns:
        AnalysisConfig: A configured analysis object
    """
    return AnalysisConfig(
        window_sizes=sample_config["analysis"]["window_sizes"],
        convergence_threshold=sample_config["analysis"]["convergence_threshold"],
    )


@pytest.fixture
def numerical_settings() -> NumericalSettings:
    """
    Fixture providing numerical settings for stability checks.
    
    Returns:
        NumericalSettings: Configuration for numerical tolerances
    """
    return NumericalSettings(
        rtol=1e-9,
        atol=1e-12,
        boundedness_threshold=100.0,
        convergence_tol=1e-6,
    )


@pytest.fixture
def clean_test_environment(temp_data_dir: Path, random_seed: int) -> Dict[str, Path]:
    """
    Composite fixture providing a clean test environment with paths.
    
    Args:
        temp_data_dir: Temporary directory fixture
        random_seed: Random seed fixture
    
    Returns:
        Dict with paths to raw, processed, and state directories
    """
    return {
        "raw": temp_data_dir / "raw",
        "processed": temp_data_dir / "processed",
        "state": temp_data_dir / "state",
        "seed": random_seed,
    }