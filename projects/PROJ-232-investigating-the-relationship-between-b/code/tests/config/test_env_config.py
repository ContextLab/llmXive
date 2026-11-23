"""
Tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest
from dotenv import load_dotenv
from src.config.env_config import (
    load_dotenv_file,
    get_env_var,
    get_config,
    ensure_directories,
    get_data_path,
    get_figures_path,
    get_logs_path,
    get_project_version,
    ProjectPaths,
    EnvConfig,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("OPENNEURO_API_KEY=test_key_123\n")
        f.write("FMRIPREP_PATH=/usr/local/bin/fmriprep\n")
        f.write("SCHAEFER_ATLAS_PATH=/data/atlas/schaefer\n")
        env_path = f.name
    yield Path(env_path)
    os.unlink(env_path)

@pytest.fixture
def reset_config_before_test():
    """Reset environment variables before each test."""
    # Save original values
    original_vars = {}
    for var in ["OPENNEURO_API_KEY", "FMRIPREP_PATH", "SCHAEFER_ATLAS_PATH"]:
        if var in os.environ:
            original_vars[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_vars.items():
        os.environ[var] = value

def test_config_default_values(reset_config_before_test):
    """Test that default configuration values are set correctly."""
    config = get_config()
    assert config.project_paths.data.exists()
    assert config.project_paths.figures.exists()
    assert config.project_paths.logs.exists()
    assert config.project_paths.preprocessing.exists()
    assert config.project_paths.results.exists()
    assert config.openneuro_api_key is None
    assert config.fmriprep_path is None
    assert config.schaefer_atlas_path is None

def test_config_from_env(temp_env_file, reset_config_before_test):
    """Test that configuration is loaded from .env file."""
    # Load the temp .env file
    load_dotenv_file(temp_env_file)
    
    config = get_config()
    assert config.openneuro_api_key == "test_key_123"
    assert config.fmriprep_path == "/usr/local/bin/fmriprep"
    assert config.schaefer_atlas_path == "/data/atlas/schaefer"

def test_get_data_path():
    """Test that get_data_path returns the correct path."""
    path = get_data_path()
    assert isinstance(path, Path)
    assert path.exists()

def test_get_figures_path():
    """Test that get_figures_path returns the correct path."""
    path = get_figures_path()
    assert isinstance(path, Path)
    assert path.exists()

def test_get_logs_path():
    """Test that get_logs_path returns the correct path."""
    path = get_logs_path()
    assert isinstance(path, Path)
    assert path.exists()

def test_ensure_directories(reset_config_before_test):
    """Test that ensure_directories creates missing directories."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a custom config with paths in tmpdir
        custom_paths = ProjectPaths(
            data=tmp_path / "data",
            figures=tmp_path / "figures",
            logs=tmp_path / "logs",
            preprocessing=tmp_path / "preprocessing",
            results=tmp_path / "results",
        )
        
        config = EnvConfig(project_paths=custom_paths)
        paths = ensure_directories(config)
        
        # Verify all directories were created
        for name, path in paths.items():
            assert path.exists(), f"Directory {name} was not created"
            assert path.is_dir(), f"Path {name} is not a directory"

def test_config_validation(reset_config_before_test):
    """Test that configuration validation works correctly."""
    # Test that invalid paths are converted to absolute
    paths = ProjectPaths(data="relative/path")
    assert paths.data.is_absolute()
    
    # Test that directories are created
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_dir = tmp_path / "test"
        assert not test_dir.exists()
        
        paths = ProjectPaths(data=tmp_path / "test")
        config = EnvConfig(project_paths=paths)
        
        # This should create the directory
        _ = ensure_directories(config)
        assert test_dir.exists()

def test_project_paths_model():
    """Test ProjectPaths model validation."""
    # Test with default values
    paths = ProjectPaths()
    assert paths.data == Path("data")
    assert paths.figures == Path("figures")
    
    # Test with custom values
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        custom_paths = ProjectPaths(
            data=tmp_path / "custom_data",
            figures=tmp_path / "custom_figures",
        )
        assert custom_paths.data == tmp_path / "custom_data"
        assert custom_paths.figures == tmp_path / "custom_figures"

def test_config_get_full_path():
    """Test get_full_path function."""
    from src.config.env_config import get_full_path, PROJECT_ROOT
    
    test_path = get_full_path("test/file.txt")
    expected_path = PROJECT_ROOT / "test" / "file.txt"
    assert test_path == expected_path
