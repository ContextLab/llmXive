"""
Tests for the configuration management module.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import (
    Config,
    get_config,
    reset_config,
    get_data_path,
    get_threshold,
    get_seed,
    get_housekeeping_genes,
    get_trait_synthesis_genes,
    DEFAULT_HOUSEKEEPING_GENES
)


class TestConfigDataclass:
    def test_default_initialization(self):
        """Test that Config initializes with correct defaults."""
        reset_config()
        cfg = Config()
        assert cfg.seed == 42
        assert cfg.fdr_threshold == 0.05
        assert cfg.log2fc_threshold == 1.0
        assert cfg.min_replicates == 2
        assert cfg.cv_reduction_target == 0.20
        assert len(cfg.housekeeping_genes) > 0
        assert "ACT2" in cfg.housekeeping_genes

    def test_to_dict(self):
        """Test conversion to dictionary."""
        reset_config()
        cfg = Config()
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert d["seed"] == 42
        assert d["fdr_threshold"] == 0.05

    def test_save_and_load(self):
        """Test saving and loading configuration."""
        reset_config()
        cfg = Config()
        cfg.seed = 123
        cfg.fdr_threshold = 0.01

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_config.json"
            cfg.save(path)

            # Verify file exists
            assert path.exists()

            # Load and verify
            loaded_cfg = Config.load(path)
            assert loaded_cfg.seed == 123
            assert loaded_cfg.fdr_threshold == 0.01


class TestConfigSingleton:
    def test_singleton_instance(self):
        """Test that get_config returns a singleton."""
        reset_config()
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_reset_config(self):
        """Test resetting the singleton."""
        reset_config()
        cfg = get_config()
        cfg.seed = 999
        
        reset_config()
        new_cfg = get_config()
        assert new_cfg.seed == 42  # Should be default again
        assert cfg is not new_cfg  # Should be a new instance

    def test_get_data_path(self):
        """Test helper function for data path."""
        reset_config()
        path = get_data_path()
        assert isinstance(path, Path)
        assert path.exists() or str(path).endswith("/data")

    def test_get_threshold(self):
        """Test threshold retrieval."""
        reset_config()
        assert get_threshold("fdr") == 0.05
        assert get_threshold("log2fc") == 1.0
        assert get_threshold("cv_reduction") == 0.20
        
        with pytest.raises(ValueError):
            get_threshold("invalid_metric")

    def test_get_seed(self):
        """Test seed retrieval."""
        reset_config()
        cfg = get_config()
        cfg.seed = 555
        assert get_seed() == 555

    def test_get_housekeeping_genes(self):
        """Test housekeeping genes retrieval."""
        reset_config()
        genes = get_housekeeping_genes()
        assert isinstance(genes, list)
        assert "ACT2" in genes
        assert len(genes) > 10

    def test_get_trait_synthesis_genes(self):
        """Test trait synthesis genes retrieval."""
        reset_config()
        genes = get_trait_synthesis_genes()
        assert isinstance(genes, list)
        assert len(genes) > 0
        # CYP79D16 is listed in FR-005 as a trait synthesis gene
        assert "CYP79D16" in genes
