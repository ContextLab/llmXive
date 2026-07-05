"""
Unit tests for the configuration module.

Tests cover:
- Environment variable loading
- Validation of parameters
- Helper functions
- Directory creation
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.config import (
    Config,
    ConfigError,
    get_config,
    reset_config,
    get_target_countries,
    get_target_years,
    get_max_ram_gb,
    get_data_dir,
    get_processed_data_dir,
    get_raw_data_dir,
    get_state_dir,
    get_memory_limit_bytes,
)


class TestConfigInitialization:
    """Tests for Config class initialization."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        # Clear any existing config
        reset_config()
        
        # Unset environment variables to ensure defaults are used
        with patch.dict(os.environ, {}, clear=False):
            # Remove specific variables if they exist
            for key in ["TARGET_COUNTRIES", "TARGET_YEARS", "MAX_RAM_GB", "DATA_DIR", "LOG_LEVEL"]:
                os.environ.pop(key, None)
            
            config = Config()
            
            assert config.target_countries == ["KEN", "IND", "VNM"]
            assert config.target_years == [2020, 2021, 2022, 2023]
            assert config.max_ram_gb == 7.0
            assert config.data_dir == Path("data")
            assert config.log_level == "INFO"
    
    def test_custom_environment_variables(self):
        """Test loading from custom environment variables."""
        reset_config()
        
        with patch.dict(os.environ, {
            "TARGET_COUNTRIES": "USA,CAN,MEX",
            "TARGET_YEARS": "2019,2020,2021",
            "MAX_RAM_GB": "10.5",
            "DATA_DIR": "custom_data",
            "LOG_LEVEL": "DEBUG"
        }):
            config = Config()
            
            assert config.target_countries == ["USA", "CAN", "MEX"]
            assert config.target_years == [2019, 2020, 2021]
            assert config.max_ram_gb == 10.5
            assert config.data_dir == Path("custom_data")
            assert config.log_level == "DEBUG"
    
    def test_invalid_year_format(self):
        """Test error handling for invalid year format."""
        reset_config()
        
        with patch.dict(os.environ, {"TARGET_YEARS": "2020,abc,2022"}):
            with pytest.raises(ConfigError, match="Invalid year format"):
                Config()
    
    def test_invalid_ram_format(self):
        """Test error handling for invalid RAM format."""
        reset_config()
        
        with patch.dict(os.environ, {"MAX_RAM_GB": "not_a_number"}):
            with pytest.raises(ConfigError, match="Invalid RAM limit format"):
                Config()
    
    def test_negative_ram_limit(self):
        """Test error handling for negative RAM limit."""
        reset_config()
        
        with patch.dict(os.environ, {"MAX_RAM_GB": "-5.0"}):
            with pytest.raises(ConfigError, match="MAX_RAM_GB must be positive"):
                Config()
    
    def test_empty_countries(self):
        """Test error handling for empty country list."""
        reset_config()
        
        with patch.dict(os.environ, {"TARGET_COUNTRIES": ""}):
            with pytest.raises(ConfigError, match="TARGET_COUNTRIES cannot be empty"):
                Config()
    
    def test_year_out_of_range(self):
        """Test error handling for year out of valid range."""
        reset_config()
        
        with patch.dict(os.environ, {"TARGET_YEARS": "1990,2020"}):
            with pytest.raises(ConfigError, match="Year 1990 out of valid range"):
                Config()
    
    def test_ram_too_low(self):
        """Test error handling for RAM limit too low."""
        reset_config()
        
        with patch.dict(os.environ, {"MAX_RAM_GB": "0.5"}):
            with pytest.raises(ConfigError, match="is too low"):
                Config()
    
    def test_ram_too_high(self):
        """Test error handling for RAM limit too high."""
        reset_config()
        
        with patch.dict(os.environ, {"MAX_RAM_GB": "100.0"}):
            with pytest.raises(ConfigError, match="is suspiciously high"):
                Config()

class TestConfigMethods:
    """Tests for Config class methods."""
    
    @pytest.fixture
    def config(self):
        """Create a fresh config instance for testing."""
        reset_config()
        with patch.dict(os.environ, {}, clear=False):
            for key in ["TARGET_COUNTRIES", "TARGET_YEARS", "MAX_RAM_GB", "DATA_DIR", "LOG_LEVEL"]:
                os.environ.pop(key, None)
            return Config()
    
    def test_get_memory_limit_bytes(self, config):
        """Test memory limit conversion to bytes."""
        expected_bytes = int(7.0 * 1024**3)
        assert config.get_memory_limit_bytes() == expected_bytes
    
    def test_is_country_in_scope(self, config):
        """Test country scope checking."""
        assert config.is_country_in_scope("KEN")
        assert config.is_country_in_scope("ken")  # Case insensitive
        assert not config.is_country_in_scope("USA")
    
    def test_is_year_in_scope(self, config):
        """Test year scope checking."""
        assert config.is_year_in_scope(2020)
        assert config.is_year_in_scope(2023)
        assert not config.is_year_in_scope(2019)
    
    def test_to_dict(self, config):
        """Test configuration export to dictionary."""
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "target_countries" in config_dict
        assert "target_years" in config_dict
        assert "max_ram_gb" in config_dict
        assert "data_dir" in config_dict
        assert "log_level" in config_dict
        assert "memory_limit_bytes" in config_dict
    
    def test_repr(self, config):
        """Test string representation."""
        repr_str = repr(config)
        assert "Config" in repr_str
        assert "KEN" in repr_str
        assert "7.0" in repr_str

class TestGlobalFunctions:
    """Tests for global convenience functions."""
    
    def test_get_config(self):
        """Test getting global config instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        
        # Should return the same instance
        assert config1 is config2
    
    def test_reset_config(self):
        """Test resetting global config instance."""
        reset_config()
        get_config()  # Initialize
        
        reset_config()
        
        # Next call should create new instance
        config = get_config()
        assert isinstance(config, Config)
    
    def test_get_target_countries(self):
        """Test getting target countries."""
        reset_config()
        countries = get_target_countries()
        assert isinstance(countries, list)
        assert len(countries) > 0
    
    def test_get_target_years(self):
        """Test getting target years."""
        reset_config()
        years = get_target_years()
        assert isinstance(years, list)
        assert len(years) > 0
    
    def test_get_max_ram_gb(self):
        """Test getting max RAM."""
        reset_config()
        ram = get_max_ram_gb()
        assert isinstance(ram, float)
        assert ram > 0
    
    def test_get_data_dir(self):
        """Test getting data directory."""
        reset_config()
        data_dir = get_data_dir()
        assert isinstance(data_dir, Path)
    
    def test_get_memory_limit_bytes(self):
        """Test getting memory limit in bytes."""
        reset_config()
        limit = get_memory_limit_bytes()
        assert isinstance(limit, int)
        assert limit > 0

class TestDirectoryCreation:
    """Tests for automatic directory creation."""
    
    def test_directories_created(self):
        """Test that necessary directories are created on initialization."""
        reset_config()
        
        # Create a temporary directory for testing
        with patch.dict(os.environ, {"DATA_DIR": "/tmp/test_csa_config"}):
            config = Config()
            
            # Check that directories exist
            assert config.data_raw_dir.exists()
            assert config.data_processed_dir.exists()
            assert config.state_dir.exists()
    
    def test_directories_persist(self):
        """Test that existing directories are not recreated."""
        reset_config()
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "test_data"
            data_dir.mkdir()
            
            with patch.dict(os.environ, {"DATA_DIR": str(data_dir)}):
                config = Config()
                
                # Directories should exist
                assert config.data_raw_dir.exists()
                assert config.data_processed_dir.exists()