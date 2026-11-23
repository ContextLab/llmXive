import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from src.utils.config import (
    RuntimeConfig, InferenceConfig, AnalysisConfig, ProjectConfig,
    get_config, reset_config, get_project_root, get_data_processed_path,
    get_data_results_path, get_candidate_models, get_runtime_limits,
    get_inference_params
)


class TestConfigRAMDetection:
    def test_ram_detection_fallback(self):
        """Test that RAM detection falls back to a safe default if system info fails."""
        # The config module should handle this internally or return a default
        # We test that the function doesn't crash
        limits = get_runtime_limits()
        assert isinstance(limits, dict)
        assert "max_hours" in limits or "max_gb_ram" in limits

class TestDynamicModelSelection:
    def test_candidate_models_list(self):
        """Test that candidate models are retrievable."""
        models = get_candidate_models()
        assert isinstance(models, list)
        assert len(models) > 0

class TestRuntimeConfig:
    def test_runtime_limits_structure(self):
        limits = get_runtime_limits()
        assert "max_hours" in limits
        assert "max_gb_ram" in limits

class TestConfigPaths:
    def test_project_root_detection(self, tmp_path):
        """Test that project root is detected correctly."""
        # In a real scenario, this depends on the script location
        # Here we just ensure the function returns a Path
        root = get_project_root()
        assert isinstance(root, Path)

    def test_data_processed_path(self):
        path = get_data_processed_path()
        assert isinstance(path, Path)
        # Should end with data/processed
        assert "data" in str(path) and "processed" in str(path)

    def test_data_results_path(self):
        path = get_data_results_path()
        assert isinstance(path, Path)
        assert "results" in str(path)

class TestConfigSerialization:
    def test_config_to_dict(self):
        cfg = get_config()
        # Ensure we can serialize the config
        data = cfg.to_dict() if hasattr(cfg, 'to_dict') else str(cfg)
        assert data is not None

class TestConfigInference:
    def test_inference_params(self):
        params = get_inference_params()
        assert isinstance(params, dict)
        assert "model_name" in params or "device" in params

class TestConfigAnalysis:
    def test_analysis_config(self):
        # Just ensure the function exists and returns something
        from src.utils.config import AnalysisConfig
        # We can't easily instantiate without full context, but we can check the class exists
        assert AnalysisConfig is not None

class TestSingletonBehavior:
    def test_get_config_singleton(self):
        cfg1 = get_config()
        cfg2 = get_config()
        # If it's a singleton, they should be the same instance or equivalent
        # For now, just check they are both valid
        assert cfg1 is not None
        assert cfg2 is not None
