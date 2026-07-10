"""
Tests for environment variable management configuration.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the config module
from code.utils.config import (
    ProjectConfig,
    ConfigError,
    get_config,
    reset_config,
)


class TestProjectConfig:
    """Tests for ProjectConfig class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset global config before each test
        reset_config()
        # Save original environment
        self._original_env = os.environ.copy()
    
    def teardown_method(self):
        """Clean up after tests."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self._original_env)
        # Reset global config
        reset_config()
    
    def test_missing_required_variables_raises_error(self):
        """Test that missing required variables raise ConfigError."""
        # Clear all environment variables
        os.environ.clear()
        
        with pytest.raises(ConfigError) as exc_info:
            ProjectConfig()
        
        assert "DATA_RAW_PATH" in str(exc_info.value)
        assert "RANDOM_SEED" in str(exc_info.value)
    
    def test_valid_config_creation(self):
        """Test that valid environment variables create a config."""
        # Set minimum required variables
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        
        assert config.data_raw_path == Path("/tmp/raw")
        assert config.random_seed == 42
    
    def test_get_path_returns_path_object(self):
        """Test that get_path returns a Path object."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        path = config.get_path("DATA_RAW_PATH")
        
        assert isinstance(path, Path)
        assert path == Path("/tmp/raw")
    
    def test_get_int_parses_integer(self):
        """Test that get_int correctly parses integers."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "123"
        
        config = ProjectConfig()
        seed = config.get_int("RANDOM_SEED")
        
        assert seed == 123
        assert isinstance(seed, int)
    
    def test_get_int_raises_error_for_invalid(self):
        """Test that get_int raises error for non-integer values."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "not_a_number"
        
        config = ProjectConfig()
        
        with pytest.raises(ConfigError) as exc_info:
            config.get_int("RANDOM_SEED")
        
        assert "integer" in str(exc_info.value)
    
    def test_get_float_parses_float(self):
        """Test that get_float correctly parses floats."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        os.environ["TEST_FLOAT"] = "3.14159"
        
        config = ProjectConfig()
        value = config.get_float("TEST_FLOAT")
        
        assert abs(value - 3.14159) < 0.0001
        assert isinstance(value, float)
    
    def test_get_str_returns_string(self):
        """Test that get_str returns a string."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        os.environ["TEST_STRING"] = "hello_world"
        
        config = ProjectConfig()
        value = config.get_str("TEST_STRING")
        
        assert value == "hello_world"
        assert isinstance(value, str)
    
    def test_get_bool_true_values(self):
        """Test that get_bool correctly identifies true values."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        
        for true_val in ["1", "true", "True", "TRUE", "yes", "on"]:
            os.environ["TEST_BOOL"] = true_val
            assert config.get_bool("TEST_BOOL") is True
    
    def test_get_bool_false_values(self):
        """Test that get_bool correctly identifies false values."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        
        for false_val in ["0", "false", "False", "no", "off", ""]:
            os.environ["TEST_BOOL"] = false_val
            assert config.get_bool("TEST_BOOL") is False
    
    def test_optional_variables(self):
        """Test that optional variables don't raise errors."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        
        # Optional variables should not raise
        assert config.get_str("OPTIONAL_VAR", required=False) == ""
        assert config.get_int("OPTIONAL_INT", required=False) == 42
    
    def test_caching(self):
        """Test that values are cached after first access."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        
        # First access
        value1 = config.get_int("RANDOM_SEED")
        
        # Change environment
        os.environ["RANDOM_SEED"] = "999"
        
        # Second access should return cached value
        value2 = config.get_int("RANDOM_SEED")
        
        assert value1 == 42
        assert value2 == 42  # Cached, not re-read
    
    def test_property_accessors(self):
        """Test that property accessors work correctly."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        
        assert config.data_raw_path == Path("/tmp/raw")
        assert config.data_processed_path == Path("/tmp/processed")
        assert config.data_results_path == Path("/tmp/results")
        assert config.data_models_path == Path("/tmp/models")
        assert config.random_seed == 42
    
    def test_ensure_directories_exist(self):
        """Test that ensure_directories_exist creates directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            os.environ["DATA_RAW_PATH"] = str(tmpdir_path / "raw")
            os.environ["DATA_PROCESSED_PATH"] = str(tmpdir_path / "processed")
            os.environ["DATA_RESULTS_PATH"] = str(tmpdir_path / "results")
            os.environ["DATA_MODELS_PATH"] = str(tmpdir_path / "models")
            os.environ["RANDOM_SEED"] = "42"
            
            config = ProjectConfig()
            config.ensure_directories_exist()
            
            # Check that directories were created
            assert (tmpdir_path / "raw").exists()
            assert (tmpdir_path / "processed").exists()
            assert (tmpdir_path / "results").exists()
            assert (tmpdir_path / "models").exists()
    
    def test_load_from_env_file(self):
        """Test loading configuration from .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            env_file = tmpdir_path / ".env"
            
            env_content = f"""
DATA_RAW_PATH={tmpdir_path}/raw
DATA_PROCESSED_PATH={tmpdir_path}/processed
DATA_RESULTS_PATH={tmpdir_path}/results
DATA_MODELS_PATH={tmpdir_path}/models
RANDOM_SEED=12345
"""
            env_file.write_text(env_content)
            
            config = ProjectConfig(env_file)
            
            assert config.data_raw_path == tmpdir_path / "raw"
            assert config.random_seed == 12345
    
    def test_global_config_singleton(self):
        """Test that get_config returns a singleton."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_reset_config(self):
        """Test that reset_config clears the singleton."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        assert config1 is not config2
    
    def test_optional_api_keys(self):
        """Test that optional API keys can be set."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        os.environ["NCBI_API_KEY"] = "test_api_key_123"
        os.environ["METABOLICS_TOKEN"] = "test_token_456"
        
        config = ProjectConfig()
        
        assert config.ncbi_api_key == "test_api_key_123"
        assert config.metabolics_workbench_token == "test_token_456"
    
    def test_optional_api_keys_none_when_missing(self):
        """Test that optional API keys are None when not set."""
        os.environ["DATA_RAW_PATH"] = "/tmp/raw"
        os.environ["DATA_PROCESSED_PATH"] = "/tmp/processed"
        os.environ["DATA_RESULTS_PATH"] = "/tmp/results"
        os.environ["DATA_MODELS_PATH"] = "/tmp/models"
        os.environ["RANDOM_SEED"] = "42"
        
        config = ProjectConfig()
        
        assert config.ncbi_api_key is None
        assert config.metabolics_workbench_token is None