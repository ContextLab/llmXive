"""
Unit tests for the configuration module (src/config.py).

These tests verify:
- Constant values (seeds, resolutions)
- Directory creation functionality
- Path resolution functions
- Configuration validation
"""

import pytest
from pathlib import Path
import sys
import tempfile
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.config import (
    RANDOM_SEED,
    NUMPY_SEED,
    TORCH_SEED,
    RESOLUTION_TARGETS,
    BASE_RESOLUTION,
    DETECTION_THRESHOLD,
    MIN_INJECTION_SEPARATION,
    POWER_ANALYSIS_PILOT_N,
    POWER_ANALYSIS_TARGET_POWER,
    POWER_ANALYSIS_MAX_N,
    POWER_ANALYSIS_SIGMA_REL,
    CHI_SQUARE_DF,
    INJECTION_SCHEMA_PATH,
    DETECTION_METRIC_SCHEMA_PATH,
    DATA_DIR,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_FIGURES_DIR,
    CONTRACTS_DIR,
    ensure_directories,
    get_contract_path,
    get_data_path,
    get_processed_path,
    get_figure_path,
    validate_config,
)


class TestConfigConstants:
    """Test that configuration constants have expected values."""

    def test_random_seed_is_integer(self):
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED >= 0

    def test_numpy_seed_is_integer(self):
        assert isinstance(NUMPY_SEED, int)
        assert NUMPY_SEED >= 0

    def test_torch_seed_is_integer(self):
        assert isinstance(TORCH_SEED, int)
        assert TORCH_SEED >= 0

    def test_resolution_targets_is_list(self):
        assert isinstance(RESOLUTION_TARGETS, list)
        assert len(RESOLUTION_TARGETS) > 0

    def test_resolution_targets_contains_expected_values(self):
        expected = [4096, 2048, 1024, 512, 256]
        assert RESOLUTION_TARGETS == expected

    def test_base_resolution_is_in_targets(self):
        assert BASE_RESOLUTION in RESOLUTION_TARGETS

    def test_base_resolution_is_highest(self):
        assert BASE_RESOLUTION == max(RESOLUTION_TARGETS)

    def test_detection_threshold_is_positive(self):
        assert DETECTION_THRESHOLD > 0

    def test_min_injection_separation_is_positive(self):
        assert MIN_INJECTION_SEPARATION > 0

    def test_power_analysis_parameters(self):
        assert POWER_ANALYSIS_PILOT_N > 0
        assert POWER_ANALYSIS_TARGET_POWER > 0 and POWER_ANALYSIS_TARGET_POWER <= 1.0
        assert POWER_ANALYSIS_MAX_N > 0
        assert POWER_ANALYSIS_SIGMA_REL > 0

    def test_chi_square_df_is_positive(self):
        assert CHI_SQUARE_DF > 0

    def test_paths_are_pathlib_objects(self):
        assert isinstance(DATA_DIR, Path)
        assert isinstance(DATA_RAW_DIR, Path)
        assert isinstance(DATA_PROCESSED_DIR, Path)
        assert isinstance(DATA_FIGURES_DIR, Path)
        assert isinstance(CONTRACTS_DIR, Path)

    def test_injection_schema_path_is_pathlib(self):
        assert isinstance(INJECTION_SCHEMA_PATH, Path)

    def test_detection_metric_schema_path_is_pathlib(self):
        assert isinstance(DETECTION_METRIC_SCHEMA_PATH, Path)


class TestEnsureDirectories:
    """Test directory creation functionality."""

    def test_ensure_directories_creates_required_dirs(self, tmp_path):
        """Test that ensure_directories creates all required directories."""
        # Temporarily override the global paths for testing
        import src.config as config_module
        
        original_data_dir = config_module.DATA_DIR
        original_raw_dir = config_module.DATA_RAW_DIR
        original_processed_dir = config_module.DATA_PROCESSED_DIR
        original_figures_dir = config_module.DATA_FIGURES_DIR
        original_contracts_dir = config_module.CONTRACTS_DIR
        original_specs_dir = config_module.SPECS_DIR
        
        try:
            # Set up temporary paths
            config_module.DATA_DIR = tmp_path / "data"
            config_module.DATA_RAW_DIR = config_module.DATA_DIR / "raw"
            config_module.DATA_PROCESSED_DIR = config_module.DATA_DIR / "processed"
            config_module.DATA_FIGURES_DIR = config_module.DATA_DIR / "figures"
            config_module.CONTRACTS_DIR = tmp_path / "contracts"
            config_module.SPECS_DIR = tmp_path / "specs"
            
            # Call the function
            ensure_directories()
            
            # Verify directories were created
            assert config_module.DATA_DIR.exists()
            assert config_module.DATA_RAW_DIR.exists()
            assert config_module.DATA_PROCESSED_DIR.exists()
            assert config_module.DATA_FIGURES_DIR.exists()
            assert config_module.CONTRACTS_DIR.exists()
            assert config_module.SPECS_DIR.exists()
        
        finally:
            # Restore original paths
            config_module.DATA_DIR = original_data_dir
            config_module.DATA_RAW_DIR = original_raw_dir
            config_module.DATA_PROCESSED_DIR = original_processed_dir
            config_module.DATA_FIGURES_DIR = original_figures_dir
            config_module.CONTRACTS_DIR = original_contracts_dir
            config_module.SPECS_DIR = original_specs_dir

    def test_ensure_directories_is_idempotent(self, tmp_path):
        """Test that calling ensure_directories multiple times is safe."""
        import src.config as config_module
        
        original_data_dir = config_module.DATA_DIR
        
        try:
            config_module.DATA_DIR = tmp_path / "data"
            config_module.DATA_RAW_DIR = config_module.DATA_DIR / "raw"
            config_module.DATA_PROCESSED_DIR = config_module.DATA_DIR / "processed"
            config_module.DATA_FIGURES_DIR = config_module.DATA_DIR / "figures"
            config_module.CONTRACTS_DIR = tmp_path / "contracts"
            config_module.SPECS_DIR = tmp_path / "specs"
            
            # Call multiple times
            ensure_directories()
            ensure_directories()
            ensure_directories()
            
            # Should still exist
            assert config_module.DATA_DIR.exists()
            assert config_module.DATA_RAW_DIR.exists()
        
        finally:
            config_module.DATA_DIR = original_data_dir

class TestPathResolution:
    """Test path resolution functions."""

    def test_get_data_path(self, tmp_path):
        """Test get_data_path with and without subdirectory."""
        import src.config as config_module
        
        original_data_dir = config_module.DATA_DIR
        
        try:
            config_module.DATA_DIR = tmp_path / "data"
            
            # Without subdirectory
            result = get_data_path("test.csv")
            assert result == config_module.DATA_DIR / "test.csv"
            
            # With subdirectory
            result = get_data_path("test.csv", "raw")
            assert result == config_module.DATA_DIR / "raw" / "test.csv"
        
        finally:
            config_module.DATA_DIR = original_data_dir

    def test_get_processed_path(self, tmp_path):
        """Test get_processed_path function."""
        import src.config as config_module
        
        original_processed_dir = config_module.DATA_PROCESSED_DIR
        
        try:
            config_module.DATA_PROCESSED_DIR = tmp_path / "processed"
            
            result = get_processed_path("injections.csv")
            assert result == config_module.DATA_PROCESSED_DIR / "injections.csv"
        
        finally:
            config_module.DATA_PROCESSED_DIR = original_processed_dir

    def test_get_figure_path(self, tmp_path):
        """Test get_figure_path function."""
        import src.config as config_module
        
        original_figures_dir = config_module.DATA_FIGURES_DIR
        
        try:
            config_module.DATA_FIGURES_DIR = tmp_path / "figures"
            
            result = get_figure_path("snr_distribution.png")
            assert result == config_module.DATA_FIGURES_DIR / "snr_distribution.png"
        
        finally:
            config_module.DATA_FIGURES_DIR = original_figures_dir

    def test_get_contract_path_existing(self, tmp_path):
        """Test get_contract_path with an existing file."""
        import src.config as config_module
        
        original_contracts_dir = config_module.CONTRACTS_DIR
        
        try:
            config_module.CONTRACTS_DIR = tmp_path / "contracts"
            config_module.CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Create a test schema file
            test_schema = config_module.CONTRACTS_DIR / "test.schema.yaml"
            test_schema.write_text("test: schema")
            
            result = get_contract_path("test.schema.yaml")
            assert result == test_schema
            assert result.exists()
        
        finally:
            config_module.CONTRACTS_DIR = original_contracts_dir

    def test_get_contract_path_missing(self, tmp_path):
        """Test get_contract_path with a missing file raises error."""
        import src.config as config_module
        
        original_contracts_dir = config_module.CONTRACTS_DIR
        
        try:
            config_module.CONTRACTS_DIR = tmp_path / "contracts"
            config_module.CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
            
            with pytest.raises(FileNotFoundError):
                get_contract_path("nonexistent.schema.yaml")
        
        finally:
            config_module.CONTRACTS_DIR = original_contracts_dir

class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_config_success(self):
        """Test that validate_config passes with valid configuration."""
        # This should not raise any exceptions
        try:
            validate_config()
        except Exception as e:
            pytest.fail(f"validate_config raised an unexpected exception: {e}")

    def test_validate_config_with_invalid_base_resolution(self):
        """Test validation fails when base resolution is not in targets."""
        import src.config as config_module
        
        original_base = config_module.BASE_RESOLUTION
        original_targets = config_module.RESOLUTION_TARGETS
        
        try:
            config_module.BASE_RESOLUTION = 9999
            # Don't modify targets to keep the list valid
            
            with pytest.raises(ValueError, match="must be in RESOLUTION_TARGETS"):
                validate_config()
        
        finally:
            config_module.BASE_RESOLUTION = original_base
            config_module.RESOLUTION_TARGETS = original_targets

    def test_validate_config_with_empty_targets(self):
        """Test validation fails when resolution targets is empty."""
        import src.config as config_module
        
        original_targets = config_module.RESOLUTION_TARGETS
        
        try:
            config_module.RESOLUTION_TARGETS = []
            
            with pytest.raises(ValueError, match="cannot be empty"):
                validate_config()
        
        finally:
            config_module.RESOLUTION_TARGETS = original_targets

    def test_validate_config_with_unsorted_targets(self):
        """Test validation fails when resolution targets are not sorted descending."""
        import src.config as config_module
        
        original_targets = config_module.RESOLUTION_TARGETS
        
        try:
            # Set unsorted targets
            config_module.RESOLUTION_TARGETS = [256, 512, 1024, 2048, 4096]
            
            with pytest.raises(ValueError, match="sorted in descending order"):
                validate_config()
        
        finally:
            config_module.RESOLUTION_TARGETS = original_targets