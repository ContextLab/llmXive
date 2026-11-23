"""
Unit tests for the configuration management module.
"""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.utils.config import (
    get_config, reset_config, set_seed, get_project_root,
    get_data_processed_path, get_data_results_path, get_data_logs_path,
    get_candidate_models, get_runtime_limits, get_inference_params,
    save_config_to_json, load_config_from_json,
    RuntimeConfig, InferenceConfig, AnalysisConfig, ProjectConfig
)


class TestConfigPaths:
    """Test configuration path resolution."""

    def test_get_project_root_default(self):
        """Test that project root defaults correctly."""
        reset_config()
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_processed_path(self):
        """Test processed data path construction."""
        reset_config()
        path = get_data_processed_path()
        assert 'data' in str(path)
        assert 'processed' in str(path)

    def test_get_data_results_path(self):
        """Test results path construction."""
        reset_config()
        path = get_data_results_path()
        assert 'data' in str(path)
        assert 'results' in str(path)

    def test_get_data_logs_path(self):
        """Test logs path construction."""
        reset_config()
        path = get_data_logs_path()
        assert 'data' in str(path)
        assert 'logs' in str(path)


class TestConfigSingletonBehavior:
    """Test singleton behavior of configuration."""

    def test_get_config_returns_same_instance(self):
        """Test that get_config returns the same instance."""
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config_clears_instance(self):
        """Test that reset_config clears the singleton."""
        reset_config()
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2


class TestConfigSerialization:
    """Test configuration serialization."""

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all expected fields."""
        reset_config()
        config = get_config()
        data = config.to_dict()

        assert 'project_root' in data
        assert 'runtime' in data
        assert 'inference' in data
        assert 'analysis' in data
        assert 'candidate_models' in data
        assert 'seed' in data

    def test_from_dict_round_trip(self):
        """Test that from_dict reverses to_dict correctly."""
        reset_config()
        config = get_config()
        data = config.to_dict()
        config2 = ProjectConfig.from_dict(data)

        assert config.seed == config2.seed
        assert config.candidate_models == config2.candidate_models
        assert config.runtime.max_runtime_hours == config2.runtime.max_runtime_hours

    def test_save_and_load_config_json(self):
        """Test saving and loading config from JSON file."""
        reset_config()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'config.json')
            save_config_to_json(filepath)
            assert os.path.exists(filepath)

            config = load_config_from_json(filepath)
            assert config.seed == 42
            assert len(config.candidate_models) > 0

    def test_load_config_from_nonexistent_file(self):
        """Test that loading from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_config_from_json('/nonexistent/path/config.json')


class TestConfigRuntime:
    """Test runtime configuration."""

    def test_runtime_limits_default(self):
        """Test default runtime limits."""
        reset_config()
        limits = get_runtime_limits()
        assert limits['max_runtime_hours'] == 6.0
        assert limits['max_memory_gb'] == 14.0
        assert limits['batch_size'] == 32
        assert limits['timeout_risk_threshold'] == 0.90

    def test_runtime_config_dataclass(self):
        """Test RuntimeConfig dataclass instantiation."""
        runtime = RuntimeConfig(max_runtime_hours=4.0, max_memory_gb=8.0)
        assert runtime.max_runtime_hours == 4.0
        assert runtime.max_memory_gb == 8.0


class TestConfigInference:
    """Test inference configuration."""

    def test_inference_params_default(self):
        """Test default inference parameters."""
        reset_config()
        params = get_inference_params()
        assert 'model_name' in params
        assert 'quantization_bits' in params
        assert params['temperature'] == 0.0
        assert params['zero_shot_prompt_template'] is not None

    def test_inference_config_dataclass(self):
        """Test InferenceConfig dataclass instantiation."""
        inference = InferenceConfig(model_name="test-model", temperature=0.7)
        assert inference.model_name == "test-model"
        assert inference.temperature == 0.7


class TestConfigAnalysis:
    """Test analysis configuration."""

    def test_analysis_defaults(self):
        """Test default analysis parameters."""
        reset_config()
        config = get_config()
        assert config.analysis.significance_level == 0.05
        assert config.analysis.bonferroni_correction is True
        assert config.analysis.random_state == 42


class TestCandidateModels:
    """Test candidate model list."""

    def test_get_candidate_models_returns_list(self):
        """Test that get_candidate_models returns a list."""
        reset_config()
        models = get_candidate_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_candidate_models_not_modified(self):
        """Test that returned list is a copy."""
        reset_config()
        models1 = get_candidate_models()
        original_len = len(models1)
        models1.append("fake-model")
        models2 = get_candidate_models()
        assert len(models2) == original_len


class TestSeedSetting:
    """Test seed setting functionality."""

    def test_set_seed_updates_config(self):
        """Test that set_seed updates the config seed."""
        reset_config()
        set_seed(12345)
        config = get_config()
        assert config.seed == 12345

    def test_set_seed_affects_random(self):
        """Test that set_seed affects random module."""
        import random
        reset_config()
        set_seed(42)
        val1 = random.random()
        set_seed(42)
        val2 = random.random()
        assert val1 == val2