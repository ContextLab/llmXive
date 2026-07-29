"""
Unit tests for src/utils/config.py (Task T004).
Verifies configuration loading, saving, and default values.
"""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path to import from code/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from utils.config import (
    ProjectConfig,
    RuntimeConfig,
    InferenceConfig,
    AnalysisConfig,
    get_config,
    reset_config,
    get_project_root,
    get_data_processed_path,
    get_candidate_models,
    get_runtime_limits,
    CANDIDATE_MODELS,
    DEFAULT_SEED
)

class TestConfigRAMDetection:
    def test_default_ram_cap(self):
        cfg = ProjectConfig()
        assert cfg.runtime.ram_cap_gb == 14.0

    def test_custom_ram_cap(self):
        cfg = ProjectConfig(runtime=RuntimeConfig(ram_cap_gb=8.0))
        assert cfg.runtime.ram_cap_gb == 8.0

class TestDynamicModelSelection:
    def test_candidate_models_default(self):
        cfg = ProjectConfig()
        assert len(cfg.candidate_models) > 0
        assert "stabilityai/stable-code-3b" in cfg.candidate_models

    def test_get_candidate_models_function(self):
        models = get_candidate_models()
        assert isinstance(models, list)
        assert len(models) > 0

class TestRuntimeConfig:
    def test_default_hourly_limit(self):
        cfg = ProjectConfig()
        assert cfg.runtime.hourly_limit_hours == 6.0

    def test_custom_batch_size(self):
        cfg = ProjectConfig(runtime=RuntimeConfig(batch_size=16))
        assert cfg.runtime.batch_size == 16

    def test_get_runtime_limits(self):
        limits = get_runtime_limits()
        assert "hourly_limit_hours" in limits
        assert "ram_cap_gb" in limits
        assert "batch_size" in limits

class TestConfigPaths:
    def test_paths_exist_on_init(self):
        cfg = ProjectConfig()
        # Verify paths are set
        assert "root" in cfg.paths
        assert "data_processed" in cfg.paths
        # Verify directories are created
        root = Path(cfg.paths["root"])
        assert root.exists()

    def test_get_project_root(self):
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_processed_path(self):
        path = get_data_processed_path()
        assert isinstance(path, Path)
        assert path.exists()

class TestConfigSerialization:
    def test_save_and_load_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "config.json"
            original = ProjectConfig(seed=123)
            original.save(save_path)

            assert save_path.exists()

            loaded = ProjectConfig.load(save_path)
            assert loaded.seed == 123
            assert loaded.runtime.ram_cap_gb == original.runtime.ram_cap_gb

    def test_load_nonexistent_returns_default(self):
        fake_path = Path("/tmp/this_file_does_not_exist_12345.json")
        cfg = ProjectConfig.load(fake_path)
        assert cfg.seed == DEFAULT_SEED

    def test_to_dict(self):
        cfg = ProjectConfig()
        d = cfg.to_dict()
        assert "seed" in d
        assert "runtime" in d
        assert "inference" in d
        assert "analysis" in d
        assert "paths" in d

class TestConfigInference:
    def test_default_model(self):
        cfg = ProjectConfig()
        assert cfg.inference.model_name == "stabilityai/stable-code-3b"
        assert cfg.inference.quantization_bits == 4
        assert cfg.inference.device == "cpu"

    def test_prompt_template(self):
        cfg = ProjectConfig()
        assert "{code}" in cfg.inference.prompt_template

    def test_get_inference_params(self):
        params = get_inference_params()
        assert "model_name" in params
        assert "temperature" in params
        assert params["temperature"] == 0.0  # Deterministic

class TestConfigAnalysis:
    def test_default_analysis_config(self):
        cfg = ProjectConfig()
        assert cfg.analysis.correlation_method == "pearson"
        assert cfg.analysis.correction_method == "benjamini_hochberg"

class TestSingletonBehavior:
    def test_get_config_singleton(self):
        reset_config()
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_reset_config(self):
        reset_config()
        cfg1 = get_config()
        reset_config()
        cfg2 = get_config()
        assert cfg1 is not cfg2
        assert cfg2.seed == DEFAULT_SEED