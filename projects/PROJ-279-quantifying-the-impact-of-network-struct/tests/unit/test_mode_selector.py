import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.mode_selector import ModeSelector, check_mode_selector
from code.logging_config import setup_logging

# Setup logging for tests
setup_logging()

class TestModeSelector:
    """
    Unit tests for the ModeSelector logic.
    These tests verify the logic of mode selection without requiring
    the full dataset to be present.
    """

    @pytest.fixture
    def mock_data_dir(self, tmp_path):
        """Create a temporary directory structure simulating data."""
        vdos_dir = tmp_path / "vdos"
        vdos_dir.mkdir()
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir()

        # Create some fake VDOS files
        (vdos_dir / "vdos_config_1.json").write_text("{}")
        (vdos_dir / "vdos_config_2.json").write_text("{}")
        # config_3 is missing

        # Create a fake thermal conductivity manifest
        manifest = {
            "config_1": 1.5,
            "config_2": 1.6,
            "config_3": 1.7
        }
        (metadata_dir / "thermal_conductivity_manifest.json").write_text(json.dumps(manifest))

        return tmp_path

    def test_check_mode_selector_importable(self):
        """Verify the helper function works."""
        assert check_mode_selector() is True

    def test_init_defaults(self):
        """Test initialization with default paths."""
        with patch('code.mode_selector.get_data_dir') as mock_get_data, \
             patch('code.mode_selector.get_processed_dir') as mock_get_proc:
            mock_get_data.return_value = Path("/fake/data")
            mock_get_proc.return_value = Path("/fake/processed")

            selector = ModeSelector()
            assert selector.data_dir == Path("/fake/data")
            assert selector.processed_dir == Path("/fake/processed")

    def test_check_vdos_availability_partial(self, mock_data_dir):
        """Test VDOS availability check with partial data."""
        selector = ModeSelector(data_dir=mock_data_dir)
        config_ids = ["config_1", "config_2", "config_3"]

        avail_map, ratio = selector.check_vdos_availability(config_ids)

        assert avail_map["config_1"] is True
        assert avail_map["config_2"] is True
        assert avail_map["config_3"] is False
        assert ratio == pytest.approx(2/3)

    def test_check_vdos_availability_missing_dir(self, tmp_path):
        """Test VDOS check when directory does not exist."""
        selector = ModeSelector(data_dir=tmp_path)
        config_ids = ["config_1"]

        avail_map, ratio = selector.check_vdos_availability(config_ids)

        assert avail_map["config_1"] is False
        assert ratio == 0.0

    def test_check_k_availability_manifest(self, mock_data_dir):
        """Test k availability check via manifest."""
        selector = ModeSelector(data_dir=mock_data_dir)
        config_ids = ["config_1", "config_2", "config_3"]

        avail_map, ratio = selector.check_k_availability(config_ids)

        assert avail_map["config_1"] is True
        assert avail_map["config_2"] is True
        assert avail_map["config_3"] is True
        assert ratio == 1.0

    def test_determine_mode_full(self, mock_data_dir):
        """Test determination of Full mode when coverage is high."""
        # In mock_data_dir: VDOS 2/3 (66%), k 3/3 (100%)
        # This should trigger Structure-Only because VDOS < 80%
        # Let's adjust the mock to have 4 configs, 4 VDOS, 4 k
        vdos_dir = mock_data_dir / "vdos"
        (vdos_dir / "vdos_config_4.json").write_text("{}")
        (mock_data_dir / "metadata" / "thermal_conductivity_manifest.json").write_text(
            json.dumps({"config_1": 1, "config_2": 1, "config_3": 1, "config_4": 1})
        )

        selector = ModeSelector(data_dir=mock_data_dir)
        config_ids = ["config_1", "config_2", "config_3", "config_4"]

        mode = selector.determine_mode(config_ids)
        assert mode == ModeSelector.FULL_MODE

    def test_determine_mode_structure_only(self, mock_data_dir):
        """Test determination of Structure-Only mode when coverage is low."""
        # Current mock: VDOS 2/3 (66%), k 3/3 (100%) -> Should be Structure-Only
        selector = ModeSelector(data_dir=mock_data_dir)
        config_ids = ["config_1", "config_2", "config_3"]

        mode = selector.determine_mode(config_ids)
        assert mode == ModeSelector.STRUCTURE_ONLY_MODE

    def test_get_mode_config(self, mock_data_dir):
        """Test the full configuration generation."""
        selector = ModeSelector(data_dir=mock_data_dir)
        config_ids = ["config_1", "config_2", "config_3"]

        config = selector.get_mode_config(config_ids)

        assert "mode" in config
        assert "vdos_availability_ratio" in config
        assert "k_availability_ratio" in config
        assert "reason" in config
        assert config["mode"] == ModeSelector.STRUCTURE_ONLY_MODE

    def test_empty_config_ids(self):
        """Test behavior with empty list of config IDs."""
        selector = ModeSelector()
        mode = selector.determine_mode([])
        assert mode == ModeSelector.STRUCTURE_ONLY_MODE
