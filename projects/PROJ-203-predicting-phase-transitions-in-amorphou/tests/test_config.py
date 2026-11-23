"""
Tests for the configuration module.

These tests verify that the configuration system correctly loads environment variables,
resolves paths, and provides default values for simulation and model parameters.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil

# Import the config module
from code.config import (
    Config, 
    PathConfig, 
    SimulationConfig, 
    ModelConfig, 
    DataConfig,
    get_config,
    get_simulation_config,
    get_model_config,
    get_data_config,
    get_paths
)

@pytest.fixture
def temp_project_root():
    """Create a temporary directory for testing path resolution."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def config_with_temp_root(temp_project_root):
    """Create a config instance with a temporary project root."""
    config = Config()
    config.paths.project_root = temp_project_root
    config.paths.__post_init__()
    return config

class TestPathConfig:
    """Tests for PathConfig class."""

    def test_default_paths(self, config_with_temp_root):
        """Test that default paths are correctly derived from project_root."""
        config = config_with_temp_root
        project_root = config.paths.project_root
        
        assert config.paths.data_raw == project_root / "data" / "raw"
        assert config.paths.data_processed == project_root / "data" / "processed"
        assert config.paths.data_logs == project_root / "data" / "logs"
        assert config.paths.artifacts_dir == project_root / "artifacts"
        assert config.paths.models_dir == project_root / "models"
        assert config.paths.docs_reports == project_root / "docs" / "reports"
        assert config.paths.figures_dir == project_root / "figures"

    def test_directories_created(self, config_with_temp_root):
        """Test that directories are created on initialization."""
        config = config_with_temp_root
        
        # Check that all directories exist
        assert config.paths.data_raw.exists()
        assert config.paths.data_processed.exists()
        assert config.paths.data_logs.exists()
        assert config.paths.artifacts_dir.exists()
        assert config.paths.models_dir.exists()
        assert config.paths.docs_reports.exists()
        assert config.paths.figures_dir.exists()

    def test_validate_paths(self, config_with_temp_root):
        """Test that validate_paths returns True for existing directories."""
        config = config_with_temp_root
        
        assert config.validate_paths() is True

    def test_validate_paths_missing(self, config_with_temp_root):
        """Test that validate_paths raises error for missing directories."""
        config = config_with_temp_root
        
        # Remove a directory
        test_dir = config.paths.data_raw
        test_dir.rmdir()  # This should work since it's empty
        
        with pytest.raises(FileNotFoundError):
            config.validate_paths()

class TestSimulationConfig:
    """Tests for SimulationConfig class."""

    def test_default_values(self):
        """Test default simulation parameters."""
        config = SimulationConfig()
        
        assert config.cooling_rate == 1.0e10
        assert config.time_step == 1.0e-15
        assert config.total_steps == 100000
        assert config.cutoff_distance == 10.0
        assert config.temperature_start == 3000.0
        assert config.temperature_end == 100.0
        assert config.pressure == 1.0
        assert config.cpu_time_cap == 3600

    def test_kim_potentials(self):
        """Test that KIM potential identifiers are set."""
        config = SimulationConfig()
        
        assert config.kim_potential_oxide is not None
        assert config.kim_potential_sulfide is not None
        assert config.kim_potential_organic is not None

class TestModelConfig:
    """Tests for ModelConfig class."""

    def test_default_values(self):
        """Test default model parameters."""
        config = ModelConfig()
        
        assert config.rf_n_estimators == 100
        assert config.rf_max_depth == 10
        assert config.rf_min_samples_split == 2
        assert config.rf_min_samples_leaf == 1
        assert config.cv_folds == 5
        assert config.grid_search_max_iter == 50
        assert config.target_rmse == 15.0
        assert config.target_roc_auc == 0.7
        assert config.crystallization_threshold == 50.0

class TestDataConfig:
    """Tests for DataConfig class."""

    def test_default_values(self):
        """Test default data configuration."""
        config = DataConfig()
        
        assert config.pilot_sample_size == 24
        assert "oxide" in config.chemical_families
        assert "sulfide" in config.chemical_families
        assert "organic" in config.chemical_families
        assert config.exclude_missing_labels is True
        assert config.input_csv == "literature_subset.csv"
        assert config.output_parquet == "merged_dataset.parquet"
        assert config.nan_tolerance == 0.0

class TestConfig:
    """Tests for the main Config class."""

    def test_global_config(self, config_with_temp_root):
        """Test that global config instance is accessible."""
        config = get_config()
        assert config is not None
        assert isinstance(config, Config)

    def test_get_simulation_config(self, config_with_temp_root):
        """Test getting simulation config."""
        sim_config = get_simulation_config()
        assert isinstance(sim_config, SimulationConfig)

    def test_get_model_config(self, config_with_temp_root):
        """Test getting model config."""
        model_config = get_model_config()
        assert isinstance(model_config, ModelConfig)

    def test_get_data_config(self, config_with_temp_root):
        """Test getting data config."""
        data_config = get_data_config()
        assert isinstance(data_config, DataConfig)

    def test_get_paths(self, config_with_temp_root):
        """Test getting paths."""
        paths = get_paths()
        assert isinstance(paths, PathConfig)

    @patch.dict(os.environ, {"COOLING_RATE": "5.0e9", "TARGET_RMSE": "10.0"})
    def test_env_overrides(self, temp_project_root):
        """Test that environment variables override defaults."""
        config = Config()
        config.paths.project_root = temp_project_root
        config.paths.__post_init__()
        
        assert config.simulation.cooling_rate == 5.0e9
        assert config.model.target_rmse == 10.0

    def test_get_simulation_params(self, config_with_temp_root):
        """Test getting simulation parameters as dict."""
        config = config_with_temp_root
        params = config.get_simulation_params()
        
        assert "cooling_rate" in params
        assert "time_step" in params
        assert "total_steps" in params
        assert params["cooling_rate"] == 1.0e10

    def test_get_model_params(self, config_with_temp_root):
        """Test getting model parameters as dict."""
        config = config_with_temp_root
        params = config.get_model_params()
        
        assert "n_estimators" in params
        assert "max_depth" in params
        assert params["n_estimators"] == 100

    def test_get_data_paths(self, config_with_temp_root):
        """Test getting data paths as dict."""
        config = config_with_temp_root
        paths = config.get_data_paths()
        
        assert "raw" in paths
        assert "processed" in paths
        assert "logs" in paths
        assert paths["raw"] == config.paths.data_raw