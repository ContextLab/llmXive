"""
Tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Import the module under test
from src.config.env_config import (
    Config,
    get_config,
    reset_config,
    get_data_path,
    get_figures_path,
    get_logs_path,
    get_contracts_path,
    ProjectPaths
)


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("PROJECT_ROOT=/tmp/test_project\n")
        f.write("DATA_DIR=test_data\n")
        f.write("RANDOM_SEED=123\n")
        f.write("MOTION_THRESHOLD=0.3\n")
        env_path = f.name
    yield env_path
    os.unlink(env_path)


@pytest.fixture
def reset_config_before_test():
    """Reset configuration before each test."""
    reset_config()
    yield
    reset_config()


def test_config_default_values():
    """Test that default configuration values are set correctly."""
    config = Config()
    assert config.random_seed == 42
    assert config.motion_threshold == 0.5
    assert config.vif_threshold == 5.0
    assert config.n_jobs == -1
    assert config.fmriprep_container == "nipreps/fmriprep:latest"


def test_config_from_env(temp_env_file, reset_config_before_test):
    """Test that configuration loads from environment variables."""
    # Set the environment variable for .env file location
    os.environ['DOTENV_PATH'] = temp_env_file
    
    # Reload environment variables
    load_dotenv(temp_env_file, override=True)
    
    # Reset and get new config
    reset_config()
    config = get_config()
    
    assert config.random_seed == 123
    assert config.motion_threshold == 0.3


def test_get_data_path(reset_config_before_test):
    """Test that get_data_path returns correct absolute paths."""
    config = get_config()
    path = get_data_path("sub-01/fMRI.nii.gz")
    
    assert isinstance(path, Path)
    assert path.is_absolute()
    assert "data" in str(path)


def test_get_figures_path(reset_config_before_test):
    """Test that get_figures_path returns correct absolute paths."""
    path = get_figures_path("networks/graph.png")
    
    assert isinstance(path, Path)
    assert path.is_absolute()
    assert "figures" in str(path)


def test_get_logs_path(reset_config_before_test):
    """Test that get_logs_path returns correct absolute paths."""
    path = get_logs_path("preprocessing.log")
    
    assert isinstance(path, Path)
    assert path.is_absolute()
    assert "logs" in str(path)


def test_ensure_directories(reset_config_before_test):
    """Test that ensure_directories creates required directories."""
    config = get_config()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        config.project_root = Path(tmpdir)
        config.data_dir = Path("data")
        config.figures_dir = Path("figures")
        config.logs_dir = Path("logs")
        config.contracts_dir = Path("contracts")
        
        config.ensure_directories()
        
        # Check that directories were created
        assert (Path(tmpdir) / "data").exists()
        assert (Path(tmpdir) / "figures").exists()
        assert (Path(tmpdir) / "logs").exists()
        assert (Path(tmpdir) / "contracts").exists()
        assert (Path(tmpdir) / "data" / "preprocessing").exists()


def test_config_validation(reset_config_before_test):
    """Test that configuration validation works."""
    config = get_config()
    
    # Should not raise any exceptions
    config.validate()


def test_project_paths_model():
    """Test the ProjectPaths Pydantic model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = ProjectPaths(
            root=Path(tmpdir),
            data=Path(tmpdir) / "data",
            figures=Path(tmpdir) / "figures",
            logs=Path(tmpdir) / "logs",
            contracts=Path(tmpdir) / "contracts"
        )
        
        assert paths.root == Path(tmpdir)
        assert paths.data == Path(tmpdir) / "data"


def test_config_get_full_path(reset_config_before_test):
    """Test that get_full_path resolves paths correctly."""
    config = get_config()
    full_path = config.get_full_path("data/test.txt")
    
    assert full_path.is_absolute()
    assert "data" in str(full_path)
