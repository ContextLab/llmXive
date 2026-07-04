"""
Tests for the configuration manager.

These tests verify that:
1. Configuration loads correctly from environment variables
2. Defaults are applied when environment variables are missing
3. Directories are created automatically
4. Configuration values are validated
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the config manager
from code.utils.config_manager import Config, get_config


class TestConfigManager:
    """Test suite for Config class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.env_file = Path(self.test_dir) / ".env"
        
        # Save original environment variables
        self.original_env = {}
        for key in ['PROJECT_ROOT', 'DATA_ROOT', 'RANDOM_SEED']:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
        
        # Clear environment variables to test defaults
        for key in ['PROJECT_ROOT', 'DATA_ROOT', 'RANDOM_SEED', 
                    'DEFECTS4J_DIR', 'SUMMARIES_DIR']:
            if key in os.environ:
                del os.environ[key]
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            os.environ[key] = value
        
        # Remove test environment variables
        for key in ['PROJECT_ROOT', 'DATA_ROOT', 'RANDOM_SEED',
                    'DEFECTS4J_DIR', 'SUMMARIES_DIR']:
            if key in os.environ:
                del os.environ[key]
        
        # Remove temporary directory
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)
    
    def test_default_initialization(self):
        """Test that Config initializes with defaults when no env vars are set."""
        config = Config()
        
        # Check that defaults are applied
        assert config.random_seed == 42
        assert config.max_runtime_hours == 6.0
        assert config.max_memory_gb == 7.0
        assert config.latency_threshold_ms == 100.0
        assert config.cohort_size == 20
        assert config.num_conditions == 3
        
        # Check that data directories are created
        assert Path(config.data_root).exists()
        assert Path(config.defects4j_dir).exists()
        assert Path(config.summaries_dir).exists()
        assert Path(config.interaction_logs_dir).exists()
        assert Path(config.analysis_results_dir).exists()
        assert Path(config.consent_dir).exists()
    
    def test_custom_env_values(self):
        """Test that Config respects custom environment variables."""
        # Set custom environment variables
        os.environ['RANDOM_SEED'] = '123'
        os.environ['MAX_RUNTIME_HOURS'] = '3.5'
        os.environ['MAX_MEMORY_GB'] = '5.0'
        os.environ['COHORT_SIZE'] = '50'
        os.environ['NUM_CONDITIONS'] = '4'
        
        config = Config()
        
        # Check that custom values are used
        assert config.random_seed == 123
        assert config.max_runtime_hours == 3.5
        assert config.max_memory_gb == 5.0
        assert config.cohort_size == 50
        assert config.num_conditions == 4
    
    def test_custom_paths(self):
        """Test that Config uses custom paths when specified."""
        custom_data_root = Path(self.test_dir) / "custom_data"
        os.environ['DATA_ROOT'] = str(custom_data_root)
        
        config = Config()
        
        # Check that custom path is used
        assert config.data_root == str(custom_data_root)
        assert Path(config.data_root).exists()
        
        # Check that subdirectories are created under custom path
        assert Path(config.defects4j_dir).parent == custom_data_root
    
    def test_invalid_seed_raises_error(self):
        """Test that negative seed raises ValueError."""
        os.environ['RANDOM_SEED'] = '-1'
        
        with pytest.raises(ValueError, match="RANDOM_SEED must be non-negative"):
            Config()
    
    def test_invalid_runtime_raises_error(self):
        """Test that non-positive runtime raises ValueError."""
        os.environ['MAX_RUNTIME_HOURS'] = '0'
        
        with pytest.raises(ValueError, match="MAX_RUNTIME_HOURS must be positive"):
            Config()
    
    def test_invalid_memory_raises_error(self):
        """Test that non-positive memory raises ValueError."""
        os.environ['MAX_MEMORY_GB'] = '-5'
        
        with pytest.raises(ValueError, match="MAX_MEMORY_GB must be positive"):
            Config()
    
    def test_get_method(self):
        """Test the get() method for accessing config values."""
        config = Config()
        
        # Test getting existing value
        assert config.get('random_seed') == 42
        
        # Test getting non-existing value with default
        assert config.get('non_existing_key', 'default') == 'default'
        
        # Test getting non-existing value without default (returns None)
        assert config.get('non_existing_key') is None
    
    def test_attribute_access(self):
        """Test attribute-style access to config values."""
        config = Config()
        
        # Test attribute access
        assert config.random_seed == 42
        assert config.max_runtime_hours == 6.0
        
        # Test that non-existing attribute raises AttributeError
        with pytest.raises(AttributeError):
            _ = config.non_existing_attribute
    
    def test_to_dict(self):
        """Test that to_dict() returns a copy of config."""
        config = Config()
        config_dict = config.to_dict()
        
        # Check that it's a dictionary
        assert isinstance(config_dict, dict)
        
        # Check that it contains expected keys
        assert 'random_seed' in config_dict
        assert 'data_root' in config_dict
        
        # Check that it's a copy (modifying dict doesn't affect config)
        config_dict['random_seed'] = 999
        assert config.random_seed == 42
    
    def test_save_to_file(self):
        """Test that save_to_file() creates a valid JSON file."""
        config = Config()
        output_path = Path(self.test_dir) / "config.json"
        
        saved_path = config.save_to_file(str(output_path))
        
        # Check that file was created
        assert Path(saved_path).exists()
        assert saved_path == str(output_path)
        
        # Check that file contains valid JSON
        import json
        with open(saved_path, 'r') as f:
            loaded_config = json.load(f)
        
        assert 'random_seed' in loaded_config
        assert loaded_config['random_seed'] == 42
    
    def test_consent_directory_permissions(self):
        """Test that consent directory has restricted permissions."""
        config = Config()
        consent_dir = Path(config.consent_dir)
        
        # Check that directory exists
        assert consent_dir.exists()
        
        # Check permissions (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            import stat
            mode = consent_dir.stat().st_mode
            # Check that only owner has read/write/execute
            assert mode & stat.S_IRWXG == 0  # No group permissions
            assert mode & stat.S_IRWXO == 0  # No other permissions
    
    def test_get_config_singleton(self):
        """Test that get_config() returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
        assert config1.random_seed == config2.random_seed