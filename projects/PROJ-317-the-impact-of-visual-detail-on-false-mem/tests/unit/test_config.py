import os
import tempfile
from pathlib import Path
import pytest

# We need to test the config module. Since it uses global state,
# we need to be careful with test isolation.
# We will test by importing the functions and checking behavior.

def test_get_project_root_defaults_to_cwd():
    """Test that get_project_root returns current working directory by default."""
    from config import get_project_root
    expected = Path.cwd()
    actual = get_project_root()
    assert actual == expected

def test_ensure_directories_creates_expected_structure(tmp_path):
    """Test that ensure_directories creates all required directories."""
    from config import Config, get_config, _config
    
    # Create a temporary directory to act as project root
    # We need to reset the global config to use our temp path
    global _config
    _config = None  # Reset global state
    
    # Create a Config with the temp path
    test_config = Config(project_root=tmp_path)
    _config = test_config
    
    # Call ensure_directories
    from config import ensure_directories
    ensure_directories()
    
    # Verify directories exist
    assert (tmp_path / "data").exists()
    assert (tmp_path / "data" / "stimuli").exists()
    assert (tmp_path / "data" / "stimuli_metadata").exists()
    assert (tmp_path / "data" / "responses").exists()
    assert (tmp_path / "data" / "processed").exists()
    assert (tmp_path / "data" / "ethics").exists()
    assert (tmp_path / "data" / "logs").exists()
    assert (tmp_path / "figures").exists()
    assert (tmp_path / "code").exists()
    assert (tmp_path / "code" / "data").exists()
    assert (tmp_path / "code" / "stimuli").exists()
    assert (tmp_path / "code" / "participants").exists()
    assert (tmp_path / "code" / "analysis").exists()
    assert (tmp_path / "tests").exists()
    assert (tmp_path / "tests" / "unit").exists()
    assert (tmp_path / "tests" / "integration").exists()
    assert (tmp_path / "tests" / "contract").exists()
    assert (tmp_path / "docs").exists()
    assert (tmp_path / "docs" / "ethics").exists()

def test_get_log_level_defaults_to_info():
    """Test that get_log_level returns INFO by default."""
    from config import get_log_level
    # Ensure env var is not set
    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]
    assert get_log_level() == "INFO"

def test_get_log_level_respects_env_var():
    """Test that get_log_level respects LOG_LEVEL environment variable."""
    from config import get_log_level
    os.environ["LOG_LEVEL"] = "DEBUG"
    assert get_log_level() == "DEBUG"
    # Clean up
    del os.environ["LOG_LEVEL"]

def test_get_dataset_source_defaults_to_mock():
    """Test that get_dataset_source returns 'mock' by default."""
    from config import get_dataset_source
    if "DATASET_SOURCE" in os.environ:
        del os.environ["DATASET_SOURCE"]
    assert get_dataset_source() == "mock"

def test_get_dataset_source_respects_env_var():
    """Test that get_dataset_source respects DATASET_SOURCE environment variable."""
    from config import get_dataset_source
    os.environ["DATASET_SOURCE"] = "real"
    assert get_dataset_source() == "real"
    del os.environ["DATASET_SOURCE"]

def test_get_alpha_level_defaults_to_0_05():
    """Test that get_alpha_level returns 0.05 by default."""
    from config import get_alpha_level
    if "ALPHA_LEVEL" in os.environ:
        del os.environ["ALPHA_LEVEL"]
    assert get_alpha_level() == 0.05

def test_get_alpha_level_respects_env_var():
    """Test that get_alpha_level respects ALPHA_LEVEL environment variable."""
    from config import get_alpha_level
    os.environ["ALPHA_LEVEL"] = "0.01"
    assert get_alpha_level() == 0.01
    del os.environ["ALPHA_LEVEL"]

def test_get_power_target_defaults_to_0_80():
    """Test that get_power_target returns 0.80 by default."""
    from config import get_power_target
    if "POWER_TARGET" in os.environ:
        del os.environ["POWER_TARGET"]
    assert get_power_target() == 0.80

def test_get_effect_size_defaults_to_0_25():
    """Test that get_effect_size returns 0.25 by default."""
    from config import get_effect_size
    if "EFFECT_SIZE" in os.environ:
        del os.environ["EFFECT_SIZE"]
    assert get_effect_size() == 0.25