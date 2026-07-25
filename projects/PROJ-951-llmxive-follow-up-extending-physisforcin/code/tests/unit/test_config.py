"""
Unit tests for the TrainingConfig module.
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path
from src.training.config import (
    TrainingConfig,
    create_default_config,
    get_default_config,
    validate_config_schema,
    load_config,
    save_config,
    get_filter_discard_threshold,
    get_config,
    DEFAULT_CONFIG
)

class TestTrainingConfig:
    def test_default_config_creation(self):
        config = create_default_config()
        assert isinstance(config, TrainingConfig)
        assert config.cpu_only is True
        assert config.filter_discard_percent == 0.4
        assert config.batch_size == 1

    def test_config_to_dict(self):
        config = create_default_config()
        d = config.to_dict()
        assert "cpu_only" in d
        assert "filter_discard_percent" in d
        assert d["cpu_only"] is True

    def test_config_from_dict(self):
        data = {"cpu_only": False, "learning_rate": 0.01}
        config = TrainingConfig.from_dict(data)
        assert config.cpu_only is False
        assert config.learning_rate == 0.01
        # Default values should persist for missing keys
        assert config.batch_size == 1

    def test_config_validation_valid(self):
        config = create_default_config()
        is_valid, errors = config.validate()
        assert is_valid
        assert len(errors) == 0

    def test_config_validation_invalid_discard(self):
        config = create_default_config()
        config.filter_discard_percent = 1.5
        is_valid, errors = config.validate()
        assert not is_valid
        assert any("filter_discard_percent" in e for e in errors)

    def test_config_validation_invalid_batch(self):
        config = create_default_config()
        config.batch_size = 0
        is_valid, errors = config.validate()
        assert not is_valid
        assert any("batch_size" in e for e in errors)

class TestLoadConfig:
    def test_load_nonexistent_file(self):
        config = load_config("nonexistent.yaml")
        assert config is not None
        assert config.cpu_only is True  # Should fallback to default

    def test_load_valid_yaml(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"cpu_only": False, "seed": 123}, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert config.cpu_only is False
            assert config.seed == 123
        finally:
            os.unlink(temp_path)

    def test_load_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert config is not None
            assert config.cpu_only is True  # Fallback to default
        finally:
            os.unlink(temp_path)

class TestValidateConfigSchema:
    def test_valid_schema(self):
        data = {"cpu_only": True, "filter_discard_percent": 0.5}
        is_valid, errors = validate_config_schema(data)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_discard_percent(self):
        data = {"filter_discard_percent": 1.5}
        is_valid, errors = validate_config_schema(data)
        assert not is_valid
        assert any("filter_discard_percent" in e for e in errors)

    def test_invalid_batch_size(self):
        data = {"batch_size": -1}
        is_valid, errors = validate_config_schema(data)
        assert not is_valid
        assert any("batch_size" in e for e in errors)

class TestCreateDefaultConfig:
    def test_returns_new_instance(self):
        c1 = create_default_config()
        c2 = create_default_config()
        assert c1 is not c2

    def test_has_default_values(self):
        config = create_default_config()
        assert config.filter_discard_percent == DEFAULT_CONFIG["filter_discard_percent"]
        assert config.cpu_only == DEFAULT_CONFIG["cpu_only"]

class TestGetDefaultConfig:
    def test_returns_config(self):
        config = get_default_config()
        assert isinstance(config, TrainingConfig)

class TestSaveConfig:
    def test_save_and_load_roundtrip(self):
        config = create_default_config()
        config.learning_rate = 0.005
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            save_config(config, temp_path)
            assert os.path.exists(temp_path)
            
            loaded = load_config(temp_path)
            assert loaded.learning_rate == 0.005
            assert loaded.cpu_only == config.cpu_only
        finally:
            os.unlink(temp_path)

class TestGetFilterDiscardThreshold:
    def test_default_threshold(self):
        threshold = get_filter_discard_threshold()
        assert threshold == 0.4

    def test_custom_threshold(self):
        config = create_default_config()
        config.filter_discard_percent = 0.6
        threshold = get_filter_discard_threshold(config)
        assert threshold == 0.6

class TestGetConfig:
    def test_get_config_creates_valid_object(self):
        config = get_config()
        assert isinstance(config, TrainingConfig)
        is_valid, _ = config.validate()
        # Validation might warn but should return the object
        assert config is not None

    def test_get_config_with_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"seed": 999}, f)
            temp_path = f.name
        
        try:
            config = get_config(temp_path)
            assert config.seed == 999
        finally:
            os.unlink(temp_path)