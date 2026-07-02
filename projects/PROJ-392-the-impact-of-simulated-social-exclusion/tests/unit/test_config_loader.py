"""
Unit tests for the configuration loader (T007).
"""
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config.loader import (
    get_config,
    get_dataset_id,
    get_roi_definition,
    get_roi_coordinates,
    get_path,
    get_analysis_params,
    get_all_roi_names,
    get_all_dataset_ids,
    ensure_paths_exist,
)


class TestDatasetIds:
    """Tests for dataset ID retrieval."""

    def test_get_exclusion_dataset_id(self):
        """Verify exclusion dataset ID is ds000246."""
        assert get_dataset_id("exclusion") == "ds000246"

    def test_get_reward_dataset_id(self):
        """Verify reward dataset ID is ds004738."""
        assert get_dataset_id("reward") == "ds004738"

    def test_invalid_dataset_id(self):
        """Verify KeyError is raised for unknown dataset type."""
        with pytest.raises(KeyError):
            get_dataset_id("invalid_type")

    def test_get_all_dataset_ids(self):
        """Verify list of all dataset IDs."""
        ids = get_all_dataset_ids()
        assert "ds000246" in ids
        assert "ds004738" in ids
        assert len(ids) == 2


class TestROICoordinates:
    """Tests for ROI coordinate retrieval."""

    def test_get_ventral_striatum_coords(self):
        """Verify Ventral Striatum MNI coordinates."""
        coords = get_roi_coordinates("ventral_striatum")
        assert "x" in coords
        assert "y" in coords
        assert "z" in coords
        assert isinstance(coords["x"], int)
        assert isinstance(coords["y"], int)
        assert isinstance(coords["z"], int)

    def test_get_oifc_coords(self):
        """Verify Orbitofrontal Cortex MNI coordinates."""
        coords = get_roi_coordinates("orbitofrontal_cortex")
        assert "x" in coords
        assert "y" in coords
        assert "z" in coords

    def test_invalid_roi_coords(self):
        """Verify KeyError for unknown ROI."""
        with pytest.raises(KeyError):
            get_roi_coordinates("unknown_roi")

    def test_get_all_roi_names(self):
        """Verify list of ROI names."""
        names = get_all_roi_names()
        assert "ventral_striatum" in names
        assert "orbitofrontal_cortex" in names
        assert len(names) == 2

    def test_get_roi_definition_full(self):
        """Verify full ROI definition includes atlas and threshold."""
        vs_def = get_roi_definition("ventral_striatum")
        assert vs_def["atlas"] == "AAL"
        assert "coordinates" in vs_def
        assert "mask_file" in vs_def

        ofc_def = get_roi_definition("orbitofrontal_cortex")
        assert ofc_def["atlas"] == "HarvardOxford"
        assert "threshold" in ofc_def
        assert ofc_def["threshold"] == 0.25


class TestPaths:
    """Tests for project path retrieval."""

    def test_get_root_path(self):
        """Verify root path is a Path object."""
        root = get_path("root")
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_paths(self):
        """Verify data subdirectories are configured."""
        paths = ["data_raw", "data_processed", "data_behavioral", "data_results"]
        for p in paths:
            path = get_path(p)
            assert isinstance(path, Path)
            # Should be under root
            assert path.is_relative_to(get_path("root"))

    def test_invalid_path_key(self):
        """Verify KeyError for unknown path key."""
        with pytest.raises(KeyError):
            get_path("nonexistent_path")


class TestAnalysisParams:
    """Tests for analysis parameter retrieval."""

    def test_get_analysis_params(self):
        """Verify analysis parameters are returned."""
        params = get_analysis_params()
        assert "alpha_level" in params
        assert "smoothing_kernels_mm" in params
        assert "min_subjects_per_group" in params
        assert params["alpha_level"] == 0.05
        assert params["min_subjects_per_group"] == 20

    def test_smoothing_kernels(self):
        """Verify smoothing kernel values."""
        params = get_analysis_params()
        assert 4 in params["smoothing_kernels_mm"]
        assert 6 in params["smoothing_kernels_mm"]
        assert 8 in params["smoothing_kernels_mm"]


class TestConfigIntegrity:
    """Tests for overall configuration integrity."""

    def test_get_config_returns_dict(self):
        """Verify get_config returns a dictionary."""
        cfg = get_config()
        assert isinstance(cfg, dict)
        assert "datasets" in cfg
        assert "rois" in cfg
        assert "paths" in cfg
        assert "analysis" in cfg

    def test_ensure_paths_exist_creates_dirs(self):
        """Verify ensure_paths_exist creates missing directories."""
        # This should not raise and should ensure dirs exist
        ensure_paths_exist()
        for key in ["data_raw", "data_processed", "data_behavioral", "data_results"]:
            assert get_path(key).exists()

    def test_config_is_immutable_copy(self):
        """Verify modifying returned config doesn't affect original."""
        cfg1 = get_config()
        cfg1["test_key"] = "test_value"
        cfg2 = get_config()
        assert "test_key" not in cfg2