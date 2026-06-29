"""Unit tests for configuration management in src/config/settings.py."""

import json
import tempfile
from pathlib import Path

import pytest

from src.config.settings import (
    Config,
    DatasetPaths,
    PreprocessingParams,
    MotionThresholds,
    StatisticalThresholds,
    get_default_config,
    load_config,
    save_config,
    validate_config,
)


class TestDatasetPaths:
    """Tests for DatasetPaths dataclass."""

    def test_default_values(self):
        """Test default path values."""
        paths = DatasetPaths()
        assert paths.raw == "data/raw"
        assert paths.processed == "data/processed"
        assert paths.result == "data/results"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        paths = DatasetPaths(raw="custom/raw", processed="custom/proc", result="custom/res")
        data = paths.to_dict()
        assert data == {
            "raw": "custom/raw",
            "processed": "custom/proc",
            "result": "custom/res",
        }

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"raw": "test/raw", "processed": "test/proc", "result": "test/res"}
        paths = DatasetPaths.from_dict(data)
        assert paths.raw == "test/raw"
        assert paths.processed == "test/proc"
        assert paths.result == "test/res"

    def test_validate_empty_raw(self):
        """Test validation fails for empty raw path."""
        paths = DatasetPaths(raw="", processed="data/processed", result="data/results")
        with pytest.raises(ValueError, match="dataset_paths.raw must be a non-empty string"):
            paths.validate()

    def test_validate_invalid_types(self):
        """Test validation fails for non-string types."""
        paths = DatasetPaths(raw=123, processed="data/processed", result="data/results")
        with pytest.raises(ValueError):
            paths.validate()


class TestPreprocessingParams:
    """Tests for PreprocessingParams dataclass."""

    def test_default_values(self):
        """Test default preprocessing values."""
        params = PreprocessingParams()
        assert params.motion_correction is True
        assert params.slice_timing is True
        assert params.normalization is True
        assert params.smoothing_mm == 6
        assert params.bandpass_range == (0.01, 0.1)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        params = PreprocessingParams(smoothing_mm=8, bandpass_range=(0.008, 0.09))
        data = params.to_dict()
        assert data["smoothing_mm"] == 8
        assert data["bandpass_range"] == (0.008, 0.09)

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "motion_correction": False,
            "slice_timing": True,
            "normalization": True,
            "smoothing_mm": 4,
            "bandpass_range": (0.01, 0.15),
        }
        params = PreprocessingParams.from_dict(data)
        assert params.motion_correction is False
        assert params.smoothing_mm == 4

    def test_validate_negative_smoothing(self):
        """Test validation fails for negative smoothing."""
        params = PreprocessingParams(smoothing_mm=-1)
        with pytest.raises(ValueError, match="smoothing_mm must be non-negative int"):
            params.validate()

    def test_validate_invalid_bandpass(self):
        """Test validation fails for invalid bandpass range."""
        params = PreprocessingParams(bandpass_range=(0.1, 0.01))  # low > high
        with pytest.raises(ValueError, match="bandpass_range must be"):
            params.validate()


class TestMotionThresholds:
    """Tests for MotionThresholds dataclass."""

    def test_default_values(self):
        """Test default motion threshold values."""
        thresholds = MotionThresholds()
        assert thresholds.translation_mm == 3.0
        assert thresholds.rotation_deg == 3.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        thresholds = MotionThresholds(translation_mm=2.5, rotation_deg=2.0)
        data = thresholds.to_dict()
        assert data == {"translation_mm": 2.5, "rotation_deg": 2.0}

    def test_validate_negative_threshold(self):
        """Test validation fails for negative threshold."""
        thresholds = MotionThresholds(translation_mm=-1.0)
        with pytest.raises(ValueError, match="translation_mm must be positive float"):
            thresholds.validate()


class TestStatisticalThresholds:
    """Tests for StatisticalThresholds dataclass."""

    def test_default_values(self):
        """Test default statistical threshold values."""
        thresholds = StatisticalThresholds()
        assert thresholds.nbs_t == 3.1
        assert thresholds.nbs_alpha == 0.05
        assert thresholds.power_target == 0.80

    def test_to_dict(self):
        """Test conversion to dictionary."""
        thresholds = StatisticalThresholds(nbs_t=3.5, nbs_alpha=0.01, power_target=0.90)
        data = thresholds.to_dict()
        assert data == {"nbs_t": 3.5, "nbs_alpha": 0.01, "power_target": 0.90}

    def test_validate_alpha_out_of_range(self):
        """Test validation fails for alpha outside (0, 1)."""
        thresholds = StatisticalThresholds(nbs_alpha=1.5)
        with pytest.raises(ValueError, match="nbs_alpha must be in"):
            thresholds.validate()

    def test_validate_power_out_of_range(self):
        """Test validation fails for power outside (0, 1]."""
        thresholds = StatisticalThresholds(power_target=0.0)
        with pytest.raises(ValueError, match="power_target must be in"):
            thresholds.validate()


class TestConfig:
    """Tests for main Config dataclass."""

    def test_default_config(self):
        """Test Config has correct default values."""
        config = get_default_config()
        assert config.atlas_choice == "AAL"
        assert config.dataset_paths.raw == "data/raw"
        assert config.preprocessing_params.smoothing_mm == 6
        assert config.motion_thresholds.translation_mm == 3.0
        assert config.statistical_thresholds.power_target == 0.80

    def test_to_dict(self):
        """Test Config converts to dictionary correctly."""
        config = get_default_config()
        data = config.to_dict()
        assert "dataset_paths" in data
        assert "preprocessing_params" in data
        assert "atlas_choice" in data
        assert "motion_thresholds" in data
        assert "statistical_thresholds" in data
        assert data["atlas_choice"] == "AAL"

    def test_from_dict(self):
        """Test Config creates from dictionary correctly."""
        data = {
            "dataset_paths": {"raw": "test/raw", "processed": "test/proc", "result": "test/res"},
            "preprocessing_params": {"smoothing_mm": 8},
            "atlas_choice": "HarvardOxford",
            "motion_thresholds": {"translation_mm": 2.0},
            "statistical_thresholds": {"power_target": 0.90},
        }
        config = Config.from_dict(data)
        assert config.dataset_paths.raw == "test/raw"
        assert config.preprocessing_params.smoothing_mm == 8
        assert config.atlas_choice == "HarvardOxford"

    def test_validate_invalid_atlas(self):
        """Test validation fails for invalid atlas choice."""
        config = get_default_config()
        config.atlas_choice = "InvalidAtlas"
        with pytest.raises(ValueError, match="atlas_choice must be one of"):
            config.validate()

    def test_save_and_load(self):
        """Test saving and loading config to/from JSON file."""
        config = get_default_config()
        config.preprocessing_params.smoothing_mm = 10

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_config.json"
            save_config(config, path)

            # Verify file exists
            assert path.exists()

            # Load and verify
            loaded = load_config(path)
            assert loaded.preprocessing_params.smoothing_mm == 10
            assert loaded.atlas_choice == "AAL"

    def test_save_creates_parent_dirs(self):
        """Test save creates parent directories if needed."""
        config = get_default_config()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dir" / "config.json"
            save_config(config, path)
            assert path.exists()

    def test_load_nonexistent_file(self):
        """Test load raises FileNotFoundError for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.json"
            with pytest.raises(FileNotFoundError):
                load_config(path)

    def test_json_serializable(self):
        """Test entire config is JSON serializable."""
        config = get_default_config()
        data = config.to_dict()

        # This should not raise
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed["atlas_choice"] == "AAL"


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config(self):
        """Test validate_config passes for valid config."""
        config = get_default_config()
        # Should not raise
        validate_config(config)

    def test_invalid_config_raises(self):
        """Test validate_config raises for invalid config."""
        config = get_default_config()
        config.atlas_choice = "Invalid"
        with pytest.raises(ValueError):
            validate_config(config)