"""
Unit tests for configuration management.
"""
import pytest
from pathlib import Path
import tempfile
import os
import random
import numpy as np

from utils.config import (
    ProjectConfig,
    ConfigManager,
    get_config,
    set_random_seed,
    get_path,
    get_data_path,
    get_processed_data_path,
    get_log_path,
    save_config
)


class TestProjectConfig:
    """Tests for ProjectConfig dataclass."""

    def test_default_initialization(self):
        """Test default initialization with project_root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ProjectConfig(project_root=project_root)
            
            assert config.project_root == project_root
            assert config.random_seed == 42
            assert config.environment == "development"
            assert config.verbose is True
            
            # Check derived paths
            assert config.data_dir == project_root / "data"
            assert config.data_raw_dir == project_root / "data" / "raw"
            assert config.data_processed_dir == project_root / "data" / "processed"
            assert config.data_logs_dir == project_root / "data" / "logs"
            assert config.state_dir == project_root / "state"
            assert config.config_dir == project_root / "config"

    def test_directories_created(self):
        """Test that all directories are created on initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ProjectConfig(project_root=project_root)
            
            assert config.data_dir.exists()
            assert config.data_raw_dir.exists()
            assert config.data_processed_dir.exists()
            assert config.data_logs_dir.exists()
            assert config.state_dir.exists()
            assert config.config_dir.exists()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ProjectConfig(project_root=project_root)
            
            config_dict = config.to_dict()
            
            assert "project_root" in config_dict
            assert "random_seed" in config_dict
            assert config_dict["random_seed"] == 42
            assert config_dict["environment"] == "development"

    def test_save_to_yaml(self):
        """Test saving configuration to YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = ProjectConfig(project_root=project_root)
            
            yaml_path = project_root / "test_config.yaml"
            config.save_to_yaml(yaml_path)
            
            assert yaml_path.exists()


class TestConfigManager:
    """Tests for ConfigManager singleton."""

    def test_singleton_pattern(self):
        """Test that ConfigManager returns the same instance."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        
        assert manager1 is manager2

    def test_get_config(self):
        """Test getting configuration."""
        config = ConfigManager.get_config()
        
        assert isinstance(config, ProjectConfig)
        assert config.random_seed == 42

    def test_set_random_seed(self):
        """Test setting random seed."""
        set_random_seed(123)
        
        # Test Python random
        val1 = random.random()
        set_random_seed(123)
        val2 = random.random()
        
        assert val1 == val2
        
        # Test numpy random
        val1 = np.random.rand()
        set_random_seed(123)
        val2 = np.random.rand()
        
        assert val1 == val2

    def test_get_path(self):
        """Test getting paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change the project root for testing
            original_root = ConfigManager.get_config().project_root
            
            # Reset singleton to force reinitialization
            ConfigManager._instance = None
            ConfigManager._config = None
            
            # Create new config with temp directory
            ConfigManager()
            ConfigManager.update_config(project_root=Path(tmpdir))
            
            test_path = get_path("test", "subdir")
            assert str(test_path).startswith(tmpdir)
            assert test_path.name == "subdir"
            
            # Restore original
            ConfigManager._instance = None
            ConfigManager._config = None
            ConfigManager()

    def test_get_data_path(self):
        """Test getting data paths."""
        data_path = get_data_path("raw", "test.csv")
        
        assert "data" in str(data_path)
        assert "raw" in str(data_path)

    def test_get_processed_data_path(self):
        """Test getting processed data paths."""
        processed_path = get_processed_data_path("test.parquet")
        
        assert "processed" in str(processed_path)

    def test_get_log_path(self):
        """Test getting log paths."""
        log_path = get_log_path("pipeline.log")
        
        assert "logs" in str(log_path)

    def test_update_config(self):
        """Test updating configuration."""
        original_seed = ConfigManager.get_config().random_seed
        
        set_random_seed(999)
        
        assert ConfigManager.get_config().random_seed == 999
        
        # Restore
        set_random_seed(original_seed)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_config_function(self):
        """Test get_config function."""
        config = get_config()
        assert isinstance(config, ProjectConfig)

    def test_set_random_seed_function(self):
        """Test set_random_seed function."""
        set_random_seed(456)
        assert random.random() >= 0  # Just verify it runs

    def test_save_config_function(self):
        """Test save_config function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test_save.yaml"
            save_config(test_path)
            
            assert test_path.exists()
            assert test_path.stat().st_size > 0