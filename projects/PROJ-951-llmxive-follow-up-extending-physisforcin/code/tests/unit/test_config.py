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
)

class TestTrainingConfig:
    def test_default_values(self):
        cfg = TrainingConfig()
        assert cfg.filter_discard_percent == 0.4
        assert cfg.cpu_only is True
        assert cfg.model_channels == 64
        assert cfg.model_down_blocks == 4
        assert cfg.model_up_blocks == 4
        assert cfg.model_attention_heads == 8

    def test_validation_success(self):
        cfg = TrainingConfig()
        is_valid, errors = cfg.validate()
        assert is_valid is True
        assert len(errors) == 0

    def test_validation_cpu_only_fail(self):
        cfg = TrainingConfig(cpu_only=False)
        is_valid, errors = cfg.validate()
        assert is_valid is False
        assert any("CPU-only" in e for e in errors)

    def test_validation_discard_percent_invalid(self):
        cfg = TrainingConfig(filter_discard_percent=1.5)
        is_valid, errors = cfg.validate()
        assert is_valid is False
        assert any("filter_discard_percent" in e for e in errors)

class TestLoadConfig:
    def test_load_missing_file(self):
        # Should return defaults and log warning
        cfg = load_config("nonexistent/path/config.yaml")
        assert cfg.filter_discard_percent == 0.4

    def test_load_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"filter_discard_percent": 0.5, "seed": 123}, f)
            temp_path = f.name
        
        try:
            cfg = load_config(temp_path)
            assert cfg.filter_discard_percent == 0.5
            assert cfg.seed == 123
        finally:
            os.unlink(temp_path)

    def test_load_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            cfg = load_config(temp_path)
            # Should fallback to defaults
            assert cfg.filter_discard_percent == 0.4
        finally:
            os.unlink(temp_path)

    def test_load_missing_schema_keys(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"random_key": 123}, f) # Missing required keys
            temp_path = f.name
        
        try:
            cfg = load_config(temp_path)
            # Should fallback to defaults
            assert cfg.filter_discard_percent == 0.4
        finally:
            os.unlink(temp_path)

class TestValidateConfigSchema:
    def test_schema_valid(self):
        data = {
            "filter_discard_percent": 0.4,
            "seed": 42,
            "batch_size": 4,
            "num_epochs": 10,
            "learning_rate": 0.0001,
            "cpu_only": True,
            "max_ram_gb": 6.0,
            "model_channels": 64,
            "model_down_blocks": 4,
            "model_up_blocks": 4,
            "model_attention_heads": 8,
            "target_param_count_m": 50.0
        }
        is_valid, missing = validate_config_schema(data)
        assert is_valid is True
        assert len(missing) == 0

    def test_schema_missing_keys(self):
        data = {"filter_discard_percent": 0.4}
        is_valid, missing = validate_config_schema(data)
        assert is_valid is False
        assert "seed" in missing

class TestCreateDefaultConfig:
    def test_returns_config(self):
        cfg = create_default_config()
        assert isinstance(cfg, TrainingConfig)
        assert cfg.cpu_only is True

class TestGetDefaultConfig:
    def test_returns_new_instance(self):
        cfg1 = get_default_config()
        cfg2 = get_default_config()
        assert cfg1 is not cfg2

class TestSaveConfig:
    def test_save_and_load(self):
        cfg = TrainingConfig(filter_discard_percent=0.6, seed=999)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            success = save_config(cfg, temp_path)
            assert success is True
            
            loaded_cfg = load_config(temp_path)
            assert loaded_cfg.filter_discard_percent == 0.6
            assert loaded_cfg.seed == 999
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestGetFilterDiscardThreshold:
    def test_default_threshold(self):
        threshold = get_filter_discard_threshold()
        assert threshold == 0.4

    def test_custom_threshold(self):
        cfg = TrainingConfig(filter_discard_percent=0.25)
        threshold = get_filter_discard_threshold(cfg)
        assert threshold == 0.25

class TestGetConfig:
    def test_force_cpu_only(self):
        # Create a config file that explicitly sets cpu_only=False
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"cpu_only": False, "filter_discard_percent": 0.4}, f)
            temp_path = f.name
        
        try:
            cfg = get_config(temp_path)
            # The get_config function should force cpu_only=True
            assert cfg.cpu_only is True
        finally:
            os.unlink(temp_path)