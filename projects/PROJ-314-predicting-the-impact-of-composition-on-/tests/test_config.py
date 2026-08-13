import os
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to import the load_env function from code/__init__.py
# Since code/__init__.py might trigger initialization, we handle imports carefully.
# We assume the test runs from the project root or the code directory is in sys.path.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code import load_env
from code.config import get_config_value

def test_env_loading():
    """
    Test that load_env() correctly loads variables from a .env file.
    """
    # Create a temporary directory to simulate a project root
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    original_env = os.environ.copy()

    try:
        # Change to temp directory
        os.chdir(temp_dir)

        # Create a mock .env file
        env_file = Path(temp_dir) / ".env"
        test_key = "TEST_CONFIG_VAR"
        test_value = "test_value_123"
        
        with open(env_file, "w") as f:
            f.write(f"{test_key}={test_value}\n")
            f.write("ANOTHER_VAR=another_value\n")

        # Call load_env
        result = load_env()
        
        # Assert load_env returned True
        assert result is True, "load_env should return True on success"

        # Assert the variable is now in os.environ
        assert test_key in os.environ, f"Key {test_key} not found in environment"
        assert os.environ[test_key] == test_value, f"Value mismatch for {test_key}"
        assert os.environ["ANOTHER_VAR"] == "another_value"

    finally:
        # Restore environment and directory
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
        shutil.rmtree(temp_dir)

def test_env_missing_file():
    """
    Test that load_env handles a missing .env file gracefully (returns False).
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)
        # Ensure no .env exists
        env_file = Path(temp_dir) / ".env"
        if env_file.exists():
            env_file.unlink()

        result = load_env()
        assert result is False, "load_env should return False if .env is missing"
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

def test_config_value_retrieval():
    """
    Test that get_config_value can retrieve values loaded via .env.
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    original_env = os.environ.copy()

    try:
        os.chdir(temp_dir)
        
        env_file = Path(temp_dir) / ".env"
        with open(env_file, "w") as f:
            f.write("CONFIG_TEST_KEY=config_test_value\n")

        load_env()
        
        # Retrieve using the config helper
        val = get_config_value("CONFIG_TEST_KEY")
        assert val == "config_test_value", "Config value retrieval failed"
        
        # Test default value
        default_val = get_config_value("MISSING_KEY", default="default_val")
        assert default_val == "default_val", "Default value retrieval failed"

    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
        shutil.rmtree(temp_dir)