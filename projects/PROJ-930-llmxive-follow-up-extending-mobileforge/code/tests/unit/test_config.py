import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

from utils.config import (
    ProjectConfig,
    get_config,
    reset_config,
    validate_config,
    set_environment_variables,
    DEFAULT_CONFIG_PATH,
)

class TestProjectConfig:
    """Unit tests for ProjectConfig class."""

    @pytest.fixture
    def mock_env_vars(self):
        """Fixture to set up mock environment variables."""
        env = {
            'LLMXIVE_DATA_RAW': '/tmp/test_raw',
            'LLMXIVE_DATA_PROCESSED': '/tmp/test_processed',
            'LLMXIVE_DATA_EVALUATION': '/tmp/test_eval',
            'LLMXIVE_MODELS_DIR': '/tmp/test_models',
            'LLMXIVE_STATE_DIR': '/tmp/test_state',
            'LLMXIVE_RESULTS_DIR': '/tmp/test_results',
            'LLMXIVE_RANDOM_SEED': '42',
            'LLMXIVE_CPU_ONLY': 'true',
            'LLMXIVE_MIN_TRIPLES': '5000',
            'LLMXIVE_POWER_ALPHA': '0.05',
            'LLMXIVE_POWER_TARGET': '0.80',
            'LLMXIVE_MODEL_NAME': 't5-small',
            'LLMXIVE_MAX_SEQ_LENGTH': '512',
            'LLMXIVE_BATCH_SIZE': '8',
            'LLMXIVE_LEARNING_RATE': '3e-5',
            'LLMXIVE_EPOCHS': '10',
            'LLMXIVE_N_TASKS': '100',
            'LLMXIVE_USE_STREAMING': 'true',
        }
        with patch.dict(os.environ, env, clear=True):
            yield env

    def test_from_env_success(self, mock_env_vars):
        """Test successful configuration from environment variables."""
        reset_config()
        config = ProjectConfig.from_env()
        
        assert config.random_seed == 42
        assert config.torch_seed == 42
        assert config.numpy_seed == 42
        assert config.cpu_only is True
        assert config.min_triples == 5000
        assert config.power_alpha == 0.05
        assert config.power_target == 0.80
        assert config.model_name == 't5-small'
        assert config.max_seq_length == 512
        assert config.batch_size == 8
        assert config.learning_rate == 3e-5
        assert config.epochs == 10
        assert config.n_tasks_default == 100
        assert config.use_streaming is True

    def test_from_env_missing_seed(self, mock_env_vars):
        """Test that missing seed raises ValueError."""
        del mock_env_vars['LLMXIVE_RANDOM_SEED']
        reset_config()
        
        with pytest.raises(ValueError, match="LLMXIVE_RANDOM_SEED environment variable must be set"):
            ProjectConfig.from_env()

    def test_from_env_invalid_seed(self, mock_env_vars):
        """Test that invalid seed value raises ValueError."""
        mock_env_vars['LLMXIVE_RANDOM_SEED'] = 'not_a_number'
        reset_config()
        
        with pytest.raises(ValueError, match="LLMXIVE_RANDOM_SEED must be an integer"):
            ProjectConfig.from_env()

    def test_to_dict(self, mock_env_vars):
        """Test configuration serialization to dictionary."""
        reset_config()
        config = ProjectConfig.from_env()
        config_dict = config.to_dict()
        
        assert 'random_seed' in config_dict
        assert config_dict['random_seed'] == 42
        assert 'cpu_only' in config_dict
        assert config_dict['cpu_only'] is True

    def test_save_and_load(self, mock_env_vars, tmp_path):
        """Test saving and loading configuration to/from file."""
        reset_config()
        config = ProjectConfig.from_env()
        
        config_file = tmp_path / "config.json"
        config.save_to_file(config_file)
        
        assert config_file.exists()
        
        loaded_config = ProjectConfig.load_from_file(config_file)
        assert loaded_config.random_seed == config.random_seed
        assert loaded_config.cpu_only == config.cpu_only

    def test_apply_seeds(self, mock_env_vars):
        """Test that apply_seeds sets random seeds."""
        reset_config()
        config = ProjectConfig.from_env()
        
        # Just test that it doesn't raise an exception
        config.apply_seeds()

    def test_cpu_only_constraint(self, mock_env_vars):
        """Test CPU-only constraint validation."""
        mock_env_vars['LLMXIVE_CPU_ONLY'] = 'true'
        reset_config()
        config = ProjectConfig.from_env()
        
        assert config.cpu_only is True

class TestGetConfig:
    """Unit tests for get_config function."""

    @pytest.fixture
    def mock_env_vars(self):
        env = {
            'LLMXIVE_DATA_RAW': '/tmp/test_raw',
            'LLMXIVE_DATA_PROCESSED': '/tmp/test_processed',
            'LLMXIVE_DATA_EVALUATION': '/tmp/test_eval',
            'LLMXIVE_MODELS_DIR': '/tmp/test_models',
            'LLMXIVE_STATE_DIR': '/tmp/test_state',
            'LLMXIVE_RESULTS_DIR': '/tmp/test_results',
            'LLMXIVE_RANDOM_SEED': '123',
        }
        with patch.dict(os.environ, env, clear=True):
            yield env

    def test_get_config_returns_instance(self, mock_env_vars):
        """Test that get_config returns a ProjectConfig instance."""
        reset_config()
        config = get_config()
        
        assert isinstance(config, ProjectConfig)
        assert config.random_seed == 123

    def test_get_config_singleton(self, mock_env_vars):
        """Test that get_config returns the same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2

    def test_reset_config(self, mock_env_vars):
        """Test that reset_config clears the singleton instance."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        assert config1 is not config2

class TestValidateConfig:
    """Unit tests for validate_config function."""

    @pytest.fixture
    def mock_env_vars(self):
        env = {
            'LLMXIVE_DATA_RAW': '/tmp/test_raw',
            'LLMXIVE_DATA_PROCESSED': '/tmp/test_processed',
            'LLMXIVE_DATA_EVALUATION': '/tmp/test_eval',
            'LLMXIVE_MODELS_DIR': '/tmp/test_models',
            'LLMXIVE_STATE_DIR': '/tmp/test_state',
            'LLMXIVE_RESULTS_DIR': '/tmp/test_results',
            'LLMXIVE_RANDOM_SEED': '42',
        }
        with patch.dict(os.environ, env, clear=True):
            yield env

    def test_validate_valid_config(self, mock_env_vars):
        """Test validation of a valid configuration."""
        reset_config()
        config = ProjectConfig.from_env()
        
        # Create directories to avoid validation errors
        for path in [config.data_raw_dir, config.data_processed_dir,
                     config.data_evaluation_dir, config.models_dir,
                     config.state_dir, config.results_dir]:
            path.mkdir(parents=True, exist_ok=True)
        
        assert validate_config(config) is True

    def test_validate_invalid_alpha(self, mock_env_vars):
        """Test validation fails for invalid alpha."""
        mock_env_vars['LLMXIVE_POWER_ALPHA'] = '1.5'
        reset_config()
        config = ProjectConfig.from_env()
        
        with pytest.raises(ValueError, match="Invalid alpha"):
            validate_config(config)

    def test_validate_invalid_power_target(self, mock_env_vars):
        """Test validation fails for invalid power target."""
        mock_env_vars['LLMXIVE_POWER_TARGET'] = '1.5'
        reset_config()
        config = ProjectConfig.from_env()
        
        with pytest.raises(ValueError, match="Invalid power target"):
            validate_config(config)

class TestSetEnvironmentVariables:
    """Unit tests for set_environment_variables function."""

    @pytest.fixture
    def mock_env_vars(self):
        env = {
            'LLMXIVE_DATA_RAW': '/tmp/test_raw',
            'LLMXIVE_DATA_PROCESSED': '/tmp/test_processed',
            'LLMXIVE_DATA_EVALUATION': '/tmp/test_eval',
            'LLMXIVE_MODELS_DIR': '/tmp/test_models',
            'LLMXIVE_STATE_DIR': '/tmp/test_state',
            'LLMXIVE_RESULTS_DIR': '/tmp/test_results',
            'LLMXIVE_RANDOM_SEED': '42',
        }
        with patch.dict(os.environ, env, clear=True):
            yield env

    def test_set_environment_variables(self, mock_env_vars):
        """Test that set_environment_variables sets all env vars."""
        reset_config()
        config = ProjectConfig.from_env()
        
        # Clear existing env vars
        for key in list(os.environ.keys()):
            if key.startswith('LLMXIVE_'):
                del os.environ[key]
        
        set_environment_variables(config)
        
        assert os.environ['LLMXIVE_RANDOM_SEED'] == '42'
        assert os.environ['LLMXIVE_CPU_ONLY'] == 'true'
        assert os.environ['LLMXIVE_MIN_TRIPLES'] == '5000'

class TestConstitutionPrincipleI:
    """Tests specifically for Constitution Principle I compliance."""

    @pytest.fixture
    def mock_env_vars(self):
        env = {
            'LLMXIVE_DATA_RAW': '/tmp/test_raw',
            'LLMXIVE_DATA_PROCESSED': '/tmp/test_processed',
            'LLMXIVE_DATA_EVALUATION': '/tmp/test_eval',
            'LLMXIVE_MODELS_DIR': '/tmp/test_models',
            'LLMXIVE_STATE_DIR': '/tmp/test_state',
            'LLMXIVE_RESULTS_DIR': '/tmp/test_results',
            'LLMXIVE_RANDOM_SEED': '42',
        }
        with patch.dict(os.environ, env, clear=True):
            yield env

    def test_all_paths_explicitly_configured(self, mock_env_vars):
        """Test that all paths are explicitly configured."""
        reset_config()
        config = ProjectConfig.from_env()
        
        # All path attributes should be set
        assert hasattr(config, 'data_raw_dir')
        assert hasattr(config, 'data_processed_dir')
        assert hasattr(config, 'data_evaluation_dir')
        assert hasattr(config, 'models_dir')
        assert hasattr(config, 'state_dir')
        assert hasattr(config, 'results_dir')

    def test_random_seeds_configured(self, mock_env_vars):
        """Test that random seeds are configured."""
        reset_config()
        config = ProjectConfig.from_env()
        
        assert config.random_seed is not None
        assert config.torch_seed is not None
        assert config.numpy_seed is not None

    def test_no_default_seeds(self):
        """Test that configuration fails without explicit seed."""
        env = {
            'LLMXIVE_DATA_RAW': '/tmp/test_raw',
            'LLMXIVE_DATA_PROCESSED': '/tmp/test_processed',
            'LLMXIVE_DATA_EVALUATION': '/tmp/test_eval',
            'LLMXIVE_MODELS_DIR': '/tmp/test_models',
            'LLMXIVE_STATE_DIR': '/tmp/test_state',
            'LLMXIVE_RESULTS_DIR': '/tmp/test_results',
        }
        with patch.dict(os.environ, env, clear=True):
            reset_config()
            with pytest.raises(ValueError):
                ProjectConfig.from_env()