"""
Unit tests for the statistical configuration module.
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stats_config import (
    load_config,
    get_glm_params,
    get_fdr_threshold,
    get_cluster_threshold,
    get_roi_path,
    get_global_p_threshold,
    validate_config,
    _create_default_config
)


class TestStatsConfigLoading:
    """Test configuration loading and parsing."""

    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        config = load_config()
        assert isinstance(config, dict)
        assert "glm" in config
        assert "thresholding" in config
        assert "roi" in config

    def test_fdr_threshold_is_correct(self):
        """Test that FDR threshold is set to 0.05."""
        config = load_config()
        fdr_q = config["thresholding"]["fdr_q"]
        assert fdr_q == 0.05

    def test_global_p_threshold_is_correct(self):
        """Test that global p-threshold is 0.10 (per SC-002)."""
        config = load_config()
        global_p = config["thresholding"]["global_p_uncorrected"]
        assert global_p == 0.10

    def test_cluster_threshold_is_correct(self):
        """Test that cluster extent threshold is 10 voxels."""
        config = load_config()
        k = config["thresholding"]["cluster_extent_k"]
        assert k == 10

    def test_glm_first_level_params(self):
        """Test that GLM first-level parameters are present."""
        params = get_glm_params()["first_level"]
        assert "high_pass_filter" in params
        assert "smoothing_fwhm" in params
        assert params["high_pass_filter"] == 128.0
        assert params["smoothing_fwhm"] == 6.0

    def test_roi_definitions_present(self):
        """Test that ROI definitions are present."""
        config = load_config()
        rois = config["roi"]
        assert "auditory_cortex" in rois
        assert "motor_cortex" in rois
        assert rois["auditory_cortex"]["atlas"] == "Harvard-Oxford"

    def test_auditory_cortex_path(self):
        """Test that auditory cortex ROI path is correct."""
        path = get_roi_path("auditory_cortex")
        assert "roi_masks" in str(path)
        assert "auditory_cortex.nii.gz" in str(path)

    def test_validate_config(self):
        """Test configuration validation."""
        assert validate_config() is True

    def test_default_config_creation(self):
        """Test that default config is created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override CONFIG_PATH
            import stats_config
            original_path = stats_config.CONFIG_PATH
            
            # Create a non-existent path
            temp_config_path = Path(tmpdir) / "nonexistent" / "stats_config.yaml"
            stats_config.CONFIG_PATH = temp_config_path
            
            # This should create the default config
            config = load_config()
            
            # Verify it was created
            assert temp_config_path.exists()
            assert "glm" in config
            
            # Restore original path
            stats_config.CONFIG_PATH = original_path


class TestConfigAccessors:
    """Test the accessor functions."""

    def test_get_fdr_threshold(self):
        """Test FDR threshold accessor."""
        assert get_fdr_threshold() == 0.05

    def test_get_cluster_threshold(self):
        """Test cluster threshold accessor."""
        assert get_cluster_threshold() == 10

    def test_get_global_p_threshold(self):
        """Test global p-threshold accessor."""
        assert get_global_p_threshold() == 0.10

    def test_get_glm_params_structure(self):
        """Test GLM params structure."""
        params = get_glm_params()
        assert "first_level" in params
        assert "group_level" in params