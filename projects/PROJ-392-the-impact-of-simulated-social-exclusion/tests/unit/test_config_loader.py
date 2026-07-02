"""
Unit tests for the configuration loader module.
"""

import pytest
import yaml
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the module under test
from utils.config_loader import (
    load_config,
    create_default_config,
    get_dataset_by_id,
    get_roi_by_name,
    get_exclusion_dataset,
    get_reward_dataset,
    get_atlas_rois,
    DatasetConfig,
    ROIConfig,
    ProjectConfig
)


class TestConfigLoader:
    """Test suite for config_loader functions."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create a temporary config file for testing."""
        config_data = {
            "version": "1.0.0",
            "datasets": [
                {
                    "id": "ds000246",
                    "name": "Test Exclusion",
                    "type": "exclusion",
                    "base_url": "https://openneuro.org/datasets"
                },
                {
                    "id": "ds004738",
                    "name": "Test Reward",
                    "type": "reward",
                    "base_url": "https://openneuro.org/datasets"
                }
            ],
            "rois": [
                {
                    "name": "Test ROI",
                    "atlas": "AAL",
                    "coordinates": [10.0, 10.0, -8.0],
                    "threshold": 25.0
                }
            ],
            "analysis": {"alpha": 0.05},
            "paths": {"raw_data": "data/raw"}
        }

        config_path = tmp_path / "test_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        return str(config_path)

    def test_load_config_success(self, temp_config_file):
        """Test that config loads successfully from a valid file."""
        config = load_config(temp_config_file)

        assert config.version == "1.0.0"
        assert len(config.datasets) == 2
        assert len(config.rois) == 1
        assert config.analysis["alpha"] == 0.05

    def test_load_config_missing_file(self):
        """Test that FileNotFoundError is raised for missing config."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_get_dataset_by_id_found(self, temp_config_file):
        """Test retrieving a dataset by ID when it exists."""
        config = load_config(temp_config_file)
        ds = get_dataset_by_id("ds000246", config)

        assert ds is not None
        assert ds.id == "ds000246"
        assert ds.name == "Test Exclusion"
        assert ds.type == "exclusion"

    def test_get_dataset_by_id_not_found(self, temp_config_file):
        """Test retrieving a dataset by ID when it doesn't exist."""
        config = load_config(temp_config_file)
        ds = get_dataset_by_id("nonexistent", config)

        assert ds is None

    def test_get_roi_by_name_found(self, temp_config_file):
        """Test retrieving an ROI by name when it exists."""
        config = load_config(temp_config_file)
        roi = get_roi_by_name("Test ROI", config)

        assert roi is not None
        assert roi.name == "Test ROI"
        assert roi.atlas == "AAL"
        assert roi.coordinates == (10.0, 10.0, -8.0)

    def test_get_roi_by_name_case_insensitive(self, temp_config_file):
        """Test that ROI name lookup is case-insensitive."""
        config = load_config(temp_config_file)
        roi = get_roi_by_name("test roi", config)

        assert roi is not None
        assert roi.name == "Test ROI"

    def test_get_exclusion_dataset(self, temp_config_file):
        """Test retrieving the exclusion dataset."""
        config = load_config(temp_config_file)
        ds = get_exclusion_dataset(config)

        assert ds is not None
        assert ds.type == "exclusion"
        assert ds.id == "ds000246"

    def test_get_reward_dataset(self, temp_config_file):
        """Test retrieving the reward dataset."""
        config = load_config(temp_config_file)
        ds = get_reward_dataset(config)

        assert ds is not None
        assert ds.type == "reward"
        assert ds.id == "ds004738"

    def test_get_atlas_rois(self, temp_config_file):
        """Test retrieving all ROIs from a specific atlas."""
        config = load_config(temp_config_file)
        rois = get_atlas_rois("AAL", config)

        assert len(rois) == 1
        assert rois[0].atlas == "AAL"

    def test_create_default_config(self, tmp_path):
        """Test that create_default_config generates a valid YAML file."""
        output_path = str(tmp_path / "default_config.yaml")
        
        created_path = create_default_config(output_path)

        assert os.path.exists(created_path)
        
        with open(created_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "version" in data
        assert "datasets" in data
        assert "rois" in data
        assert len(data["datasets"]) == 2
        assert len(data["rois"]) == 4

        # Check specific dataset IDs
        dataset_ids = [ds["id"] for ds in data["datasets"]]
        assert "ds000246" in dataset_ids
        assert "ds004738" in dataset_ids

        # Check specific ROI names
        roi_names = [roi["name"] for roi in data["rois"]]
        assert "Ventral Striatum" in roi_names
        assert "Orbitofrontal Cortex" in roi_names

    def test_dataset_config_parsing(self, temp_config_file):
        """Test that DatasetConfig objects are parsed correctly."""
        config = load_config(temp_config_file)

        for ds in config.datasets:
            assert isinstance(ds, DatasetConfig)
            assert hasattr(ds, 'id')
            assert hasattr(ds, 'name')
            assert hasattr(ds, 'type')
            assert hasattr(ds, 'base_url')

    def test_roi_config_parsing(self, temp_config_file):
        """Test that ROIConfig objects are parsed correctly."""
        config = load_config(temp_config_file)

        for roi in config.rois:
            assert isinstance(roi, ROIConfig)
            assert hasattr(roi, 'name')
            assert hasattr(roi, 'atlas')
            assert hasattr(roi, 'coordinates')
            assert hasattr(roi, 'threshold')

    def test_coordinate_parsing(self, temp_config_file):
        """Test that coordinates are parsed as tuples of floats."""
        config = load_config(temp_config_file)
        roi = get_roi_by_name("Test ROI", config)

        assert roi.coordinates is not None
        assert isinstance(roi.coordinates, tuple)
        assert len(roi.coordinates) == 3
        assert all(isinstance(c, float) for c in roi.coordinates)