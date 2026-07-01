"""
Tests for the configuration management module.
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add code root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.config import (
    StudyPaths, Thresholds, ModelSelection, StudyConfig,
    get_config, update_config
)

class TestStudyPaths:
    def test_default_paths(self):
        paths = StudyPaths()
        assert paths.root == "."
        assert paths.data_raw == "data/raw"
        assert paths.data_processed == "data/processed"

    def test_get_path_resolution(self, tmp_path):
        paths = StudyPaths(root=str(tmp_path))
        resolved = paths.get_path("data_raw")
        assert resolved == tmp_path / "data/raw"

    def test_invalid_key(self, tmp_path):
        paths = StudyPaths(root=str(tmp_path))
        with pytest.raises(ValueError):
            paths.get_path("invalid_key")

    def test_ensure_directories(self, tmp_path):
        paths = StudyPaths(root=str(tmp_path))
        paths.ensure_directories()
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "data/processed").exists()
        assert (tmp_path / "figures").exists()
        assert (tmp_path / "logs").exists()

class TestThresholds:
    def test_default_values(self):
        t = Thresholds()
        assert t.alpha == 0.01
        assert t.power == 0.80
        assert t.inconclusive_failure_rate == 0.10
        assert t.auc_threshold == 0.70

class TestModelSelection:
    def test_default_values(self):
        m = ModelSelection()
        assert m.saliency_model_name == "resnet18"
        assert m.use_cpu is True
        assert m.use_cuda is False
        assert len(m.alternative_saliency_models) == 1

class TestStudyConfig:
    def test_default_config_creation(self):
        config = StudyConfig()
        assert config.paths is not None
        assert config.thresholds is not None
        assert config.model is not None

    def test_to_dict_serialization(self):
        config = StudyConfig()
        data = config.to_dict()
        assert "paths" in data
        assert "thresholds" in data
        assert "model" in data
        assert "metadata" in data

    def test_save_and_load(self, tmp_path):
        config = StudyConfig()
        config.metadata["test"] = "value"
        save_path = tmp_path / "config.json"
        
        config.save(str(save_path))
        assert save_path.exists()

        loaded = StudyConfig.load(str(save_path))
        assert loaded.metadata["test"] == "value"
        assert loaded.paths.data_raw == config.paths.data_raw

    def test_update_config(self):
        config = StudyConfig()
        original_alpha = config.thresholds.alpha
        
        update_config({"thresholds.alpha": 0.05})
        updated_config = get_config()
        
        assert updated_config.thresholds.alpha == 0.05
        assert updated_config.thresholds.alpha != original_alpha

    def test_invalid_config_key(self):
        with pytest.raises(KeyError):
            update_config({"nonexistent.key": "value"})

def test_directory_structure_creation(tmp_path):
    config = StudyConfig()
    config.paths = StudyPaths(root=str(tmp_path))
    config.paths.ensure_directories()
    
    assert (tmp_path / "data").exists()
    assert (tmp_path / "data/raw").exists()
    assert (tmp_path / "data/processed").exists()
    assert (tmp_path / "figures").exists()
    assert (tmp_path / "logs").exists()

def test_path_properties(tmp_path):
    config = StudyConfig()
    config.paths = StudyPaths(root=str(tmp_path))
    
    raw_path = config.paths.get_path("data_raw")
    assert raw_path.is_absolute()
    assert raw_path.parent == tmp_path / "data"

def test_frozen_defaults_unchanged():
    # Verify that dataclass frozen=True prevents accidental modification
    paths = StudyPaths()
    with pytest.raises(dataclasses.FrozenInstanceError):
        paths.root = "new_root"

import dataclasses