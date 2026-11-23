"""
Unit tests for the configuration management module.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Add project root to path if needed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.settings import Config, PROJECT_ROOT, DEFAULT_DATA_DIR


class TestConfig:
    """Test cases for the Config class."""

    def test_config_initialization(self):
        """Test that Config initializes with default values."""
        cfg = Config()
        assert cfg.project_root == PROJECT_ROOT
        assert cfg.data_dir == DEFAULT_DATA_DIR
        assert isinstance(cfg.seed, int)
        assert cfg.max_ram_gb == 7
        assert cfg.cpu_cores == 2

    def test_config_ensures_directories(self, tmp_path):
        """Test that ensure_directories creates the necessary folders."""
        # Temporarily override paths for testing
        with patch.object(Config, '__init__', lambda self: None):
            cfg = Config()
            cfg.project_root = tmp_path
            cfg.data_dir = tmp_path / "data"
            cfg.data_raw = cfg.data_dir / "raw"
            cfg.data_processed = cfg.data_dir / "processed"
            cfg.data_interim = cfg.data_dir / "interim"
            cfg.logs_dir = cfg.data_dir / "logs"
            cfg.figures_dir = cfg.data_dir / "figures"
            cfg.results_dir = cfg.data_dir / "results"
            
            created_dirs = cfg.ensure_directories()
            
            for d in created_dirs:
                assert d.exists()
                assert d.is_dir()

    def test_chembl_url_construction(self):
        """Test ChEMBL URL construction."""
        cfg = Config()
        url = cfg.get_chembl_url("molecule")
        assert "chembl/api/data/molecule.json" in url

    def test_alpha_fold_url_construction(self):
        """Test AlphaFold URL construction."""
        cfg = Config()
        url = cfg.get_alpha_fold_url("P12345")
        assert "P12345" in url

    def test_env_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            "MAX_RAM_GB": "16",
            "CPU_CORES": "4",
            "RANDOM_SEED": "123"
        }):
            # Need to reload the module to pick up new env vars
            import importlib
            import config.settings
            importlib.reload(config.settings)
            
            cfg = config.settings.Config()
            assert cfg.max_ram_gb == 16
            assert cfg.cpu_cores == 4
            assert cfg.seed == 123

    def test_sensitivity_thresholds(self):
        """Test that sensitivity thresholds are correctly set."""
        cfg = Config()
        expected = [0.4, 0.5, 0.6]
        assert cfg.sensitivity_thresholds == expected

    def test_dataset_limits(self):
        """Test dataset limits for CPU feasibility."""
        cfg = Config()
        assert cfg.max_enantiomer_pairs == 10
        assert cfg.max_receptors == 3