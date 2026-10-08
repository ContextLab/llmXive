"""
Unit tests for the configuration management module (code/config.py).
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    load_env_config,
    validate_config,
    init_config,
    set_random_seed,
    ConfigError
)

class TestLoadEnvConfig:
    def test_load_valid_env_file(self):
        """Test loading a valid .env file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write("KEY1=value1\n")
            f.write("KEY2='value2'\n")
            f.write("KEY3=\"value3\"\n")
            f.write("# Comment\n")
            f.write("KEY4=value with spaces\n")
            env_path = Path(f.name)
        
        try:
            result = load_env_config(env_path)
            assert result["KEY1"] == "value1"
            assert result["KEY2"] == "value2"
            assert result["KEY3"] == "value3"
            assert result["KEY4"] == "value with spaces"
            assert "KEY1" in os.environ
        finally:
            os.unlink(env_path)

    def test_load_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_env_config(Path("/nonexistent/path/.env"))

    def test_empty_lines_and_comments(self):
        """Test that empty lines and comments are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write("\n")
            f.write("# This is a comment\n")
            f.write("   \n")
            f.write("KEY=value\n")
            env_path = Path(f.name)
        
        try:
            result = load_env_config(env_path)
            assert len(result) == 1
            assert result["KEY"] == "value"
        finally:
            os.unlink(env_path)

class TestValidateConfig:
    def test_valid_config(self):
        """Test validation with all required keys present."""
        config = {"DRYAD_API_KEY": "valid_key"}
        try:
            validate_config(config)
        except ConfigError:
            pytest.fail("validate_config raised ConfigError unexpectedly")

    def test_missing_required_key(self):
        """Test validation fails when required key is missing."""
        config = {}
        with pytest.raises(ConfigError, match="Missing or empty required configuration key: DRYAD_API_KEY"):
            validate_config(config)

    def test_empty_required_key(self):
        """Test validation fails when required key is empty."""
        config = {"DRYAD_API_KEY": ""}
        with pytest.raises(ConfigError, match="Missing or empty required configuration key: DRYAD_API_KEY"):
            validate_config(config)

    def test_invalid_seed_type(self):
        """Test validation fails when RANDOM_SEED is not an integer."""
        config = {"DRYAD_API_KEY": "key", "RANDOM_SEED": "not_a_number"}
        with pytest.raises(ConfigError, match="RANDOM_SEED must be an integer"):
            validate_config(config)

class TestSetRandomSeed:
    def test_set_seed(self):
        """Test that set_random_seed sets the seed for random and numpy."""
        set_random_seed(12345)
        
        # Check random
        val1 = random.random()
        set_random_seed(12345)
        val2 = random.random()
        assert val1 == val2

        # Check numpy if available
        try:
            import numpy as np
            set_random_seed(54321)
            arr1 = np.random.rand(5)
            set_random_seed(54321)
            arr2 = np.random.rand(5)
            assert np.array_equal(arr1, arr2)
        except ImportError:
            pass

class TestInitConfig:
    def test_init_config_from_file(self):
        """Test init_config loads from a temporary .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            with open(env_path, 'w') as f:
                f.write("DRYAD_API_KEY=test_key_123\n")
                f.write("RANDOM_SEED=999\n")
            
            # Temporarily override the default path
            import config
            original_path = config.ENV_FILE_PATH
            config.ENV_FILE_PATH = env_path
            
            try:
                result = init_config(env_path)
                assert result["DRYAD_API_KEY"] == "test_key_123"
                assert result["RANDOM_SEED"] == "999"
            finally:
                config.ENV_FILE_PATH = original_path

    def test_init_config_missing_required(self):
        """Test init_config raises ConfigError if required key is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            with open(env_path, 'w') as f:
                f.write("ANAGE_API_KEY=some_key\n") # Missing DRYAD_API_KEY
            
            import config
            original_path = config.ENV_FILE_PATH
            config.ENV_FILE_PATH = env_path
            
            try:
                with pytest.raises(ConfigError):
                    init_config(env_path)
            finally:
                config.ENV_FILE_PATH = original_path
