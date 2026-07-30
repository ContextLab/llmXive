import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.config import (
    get_config, reset_config, get_project_root, get_data_processed_path,
    get_data_results_path, get_candidate_models, get_runtime_limits, 
    get_inference_params, RuntimeConfig, InferenceConfig, AnalysisConfig, ProjectConfig
)

class TestConfigRAMDetection:
    def test_runtime_config_defaults(self):
        cfg = RuntimeConfig()
        assert cfg.hourly_limit == 3600
        assert cfg.total_runtime_limit == 21600
        assert cfg.ram_cap_gb == 14.0
        assert cfg.seed == 42

    def test_runtime_config_custom(self):
        cfg = RuntimeConfig(hourly_limit=7200, ram_cap_gb=8.0, seed=123)
        assert cfg.hourly_limit == 7200
        assert cfg.ram_cap_gb == 8.0
        assert cfg.seed == 123

class TestDynamicModelSelection:
    def test_candidate_models_list(self):
        reset_config()
        models = get_candidate_models()
        assert isinstance(models, list)
        assert len(models) > 0
        # Check for expected model patterns
        assert any("codegen" in m for m in models) or any("phi" in m for m in models)

    def test_inference_params_structure(self):
        params = get_inference_params()
        assert "candidate_models" in params
        assert "max_new_tokens" in params
        assert "temperature" in params
        assert params["temperature"] == 0.0  # Deterministic

class TestRuntimeConfig:
    def test_singleton_behavior(self):
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_reset_config(self):
        reset_config()
        cfg1 = get_config()
        reset_config()
        cfg2 = get_config()
        assert cfg1 is not cfg2

class TestConfigPaths:
    def test_get_project_root(self):
        root = get_project_root()
        assert isinstance(root, Path)
        # Should be an absolute path
        assert root.is_absolute()

    def test_data_processed_path(self):
        path = get_data_processed_path()
        assert isinstance(path, Path)
        assert "processed" in str(path)

    def test_data_results_path(self):
        path = get_data_results_path()
        assert isinstance(path, Path)
        assert "results" in str(path)

    def test_directory_creation(self):
        reset_config()
        cfg = get_config()
        # Verify directories exist (created in __post_init__)
        assert cfg.data_raw_dir.exists()
        assert cfg.data_processed_dir.exists()
        assert cfg.data_results_dir.exists()
        assert cfg.state_dir.exists()
        assert cfg.logs_dir.exists()

class TestConfigSerialization:
    def test_runtime_config_dict(self):
        cfg = RuntimeConfig()
        d = asdict(cfg)
        assert "hourly_limit" in d
        assert "seed" in d

    def test_project_config_dict(self):
        cfg = get_config()
        d = asdict(cfg)
        assert "runtime" in d
        assert "inference" in d
        assert "analysis" in d

class TestConfigInference:
    def test_inference_config_defaults(self):
        cfg = InferenceConfig()
        assert cfg.temperature == 0.0
        assert cfg.low_bit_mode == "4bit"
        assert cfg.device == "cpu"
        assert "max_new_tokens" in cfg.__dict__

    def test_inference_params_output(self):
        params = get_inference_params()
        assert params["device"] == "cpu"
        assert params["low_bit_mode"] == "4bit"

class TestConfigAnalysis:
    def test_analysis_config_defaults(self):
        cfg = AnalysisConfig()
        assert cfg.significance_level == 0.05
        assert cfg.correction_method == "benjamini_hochberg"
        assert cfg.sensitivity_sample_size == 100

class TestSingletonBehavior:
    def test_config_persistence(self):
        cfg = get_config()
        cfg.runtime.seed = 999
        cfg2 = get_config()
        assert cfg2.runtime.seed == 999

    def test_reset_clears_singleton(self):
        cfg = get_config()
        cfg.runtime.seed = 888
        reset_config()
        cfg_new = get_config()
        assert cfg_new.runtime.seed == 42  # Default value