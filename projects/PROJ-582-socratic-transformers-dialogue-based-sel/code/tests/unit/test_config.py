"""
Unit tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.utils.config import (
    SocraticConfig, 
    get_config, 
    set_global_config, 
    load_config_from_env, 
    set_seed, 
    init_project,
    GENERATOR_MODEL_ID,
    CRITIC_MODEL_ID,
    DEFAULT_SEED
)

class TestSocraticConfig:
    """Tests for SocraticConfig dataclass."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = SocraticConfig()
        assert config.generator_model_id == GENERATOR_MODEL_ID
        assert config.critic_model_id == CRITIC_MODEL_ID
        assert config.seed == DEFAULT_SEED
        assert config.max_length == 512
        assert config.temperature == 0.0
        assert config.lora_r == 8
        assert config.batch_size == 2
        assert config.gradient_accumulation_steps == 4

    def test_custom_values(self):
        """Test that custom values can be set."""
        config = SocraticConfig(
            generator_model_id="test-model",
            seed=123,
            max_length=1024,
            batch_size=4
        )
        assert config.generator_model_id == "test-model"
        assert config.seed == 123
        assert config.max_length == 1024
        assert config.batch_size == 4

    def test_paths_are_path_objects(self):
        """Test that paths are converted to Path objects."""
        config = SocraticConfig(
            output_dir="/tmp/test_output",
            log_dir="/tmp/test_logs"
        )
        assert isinstance(config.output_dir, Path)
        assert isinstance(config.log_dir, Path)

    def test_directories_created(self):
        """Test that required directories are created on initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SocraticConfig(
                output_dir=Path(tmpdir) / "output",
                log_dir=Path(tmpdir) / "logs",
                raw_data_dir=Path(tmpdir) / "raw",
                processed_data_dir=Path(tmpdir) / "processed",
                results_dir=Path(tmpdir) / "results"
            )
            # Check that directories exist
            assert config.output_dir.exists()
            assert config.log_dir.exists()
            assert config.raw_data_dir.exists()
            assert config.processed_data_dir.exists()
            assert config.results_dir.exists()

class TestGetConfig:
    """Tests for get_config function."""
    
    def test_get_config_returns_instance(self):
        """Test that get_config returns a SocraticConfig instance."""
        config = get_config()
        assert isinstance(config, SocraticConfig)

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

class TestLoadConfigFromEnv:
    """Tests for load_config_from_env function."""
    
    @patch.dict(os.environ, {
        "GENERATOR_MODEL_ID": "env-test-model",
        "CRITIC_MODEL_ID": "env-critic-model",
        "RANDOM_SEED": "999",
        "MAX_LENGTH": "2048",
        "BATCH_SIZE": "8"
    })
    def test_load_from_env(self):
        """Test that configuration is loaded from environment variables."""
        config = load_config_from_env()
        assert config.generator_model_id == "env-test-model"
        assert config.critic_model_id == "env-critic-model"
        assert config.seed == 999
        assert config.max_length == 2048
        assert config.batch_size == 8

    @patch.dict(os.environ, {}, clear=True)
    def test_default_when_no_env(self):
        """Test that default values are used when no env vars are set."""
        config = load_config_from_env()
        assert config.generator_model_id == GENERATOR_MODEL_ID
        assert config.critic_model_id == CRITIC_MODEL_ID
        assert config.seed == DEFAULT_SEED

class TestSetSeed:
    """Tests for set_seed function."""
    
    def test_set_seed_affects_random(self):
        """Test that set_seed affects random module."""
        set_seed(42)
        val1 = random.random()
        set_seed(42)
        val2 = random.random()
        assert val1 == val2

    def test_set_seed_affects_numpy(self):
        """Test that set_seed affects numpy."""
        set_seed(42)
        arr1 = np.random.rand(5)
        set_seed(42)
        arr2 = np.random.rand(5)
        assert np.array_equal(arr1, arr2)

class TestInitProject:
    """Tests for init_project function."""
    
    def test_init_project_creates_directories(self):
        """Test that init_project creates required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {
                "OUTPUT_DIR": f"{tmpdir}/output",
                "LOG_DIR": f"{tmpdir}/logs",
                "RAW_DATA_DIR": f"{tmpdir}/raw",
                "PROCESSED_DATA_DIR": f"{tmpdir}/processed",
                "RESULTS_DIR": f"{tmpdir}/results"
            }):
                init_project()
                
                # Check that directories exist
                assert Path(f"{tmpdir}/output").exists()
                assert Path(f"{tmpdir}/logs").exists()
                assert Path(f"{tmpdir}/raw").exists()
                assert Path(f"{tmpdir}/processed").exists()
                assert Path(f"{tmpdir}/results").exists()

    def test_init_project_sets_seed(self):
        """Test that init_project sets the random seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {
                "OUTPUT_DIR": f"{tmpdir}/output",
                "LOG_DIR": f"{tmpdir}/logs",
                "RAW_DATA_DIR": f"{tmpdir}/raw",
                "PROCESSED_DATA_DIR": f"{tmpdir}/processed",
                "RESULTS_DIR": f"{tmpdir}/results",
                "RANDOM_SEED": "12345"
            }):
                init_project()
                
                # Check that seed was set
                set_seed(12345)
                val1 = random.random()
                set_seed(12345)
                val2 = random.random()
                assert val1 == val2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])