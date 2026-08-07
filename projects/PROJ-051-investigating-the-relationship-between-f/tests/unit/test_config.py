"""
Unit tests for code/config.py
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    TurbulenceConfig, 
    PipelineConfig, 
    get_config, 
    validate_config, 
    reset_config
)

class TestTurbulenceConfig:
    def test_default_values(self):
        cfg = TurbulenceConfig()
        assert cfg.re_lambda_values == [200, 400, 600]
        assert cfg.vorticity_thresholds == [2.0, 3.0, 4.0]
        assert cfg.memory_limit_bytes == 6 * 1024**3

    def test_custom_values(self):
        cfg = TurbulenceConfig(
            re_lambda_values=[100, 200],
            vorticity_thresholds=[1.5],
            memory_limit_bytes=4 * 1024**3
        )
        assert cfg.re_lambda_values == [100, 200]
        assert cfg.vorticity_thresholds == [1.5]
        assert cfg.memory_limit_bytes == 4 * 1024**3

    def test_empty_re_lambda_raises(self):
        with pytest.raises(ValueError):
            TurbulenceConfig(re_lambda_values=[])

    def test_empty_thresholds_raises(self):
        with pytest.raises(ValueError):
            TurbulenceConfig(vorticity_thresholds=[])

    def test_negative_memory_raises(self):
        with pytest.raises(ValueError):
            TurbulenceConfig(memory_limit_bytes=-1)

class TestPipelineConfig:
    def test_default_paths(self):
        cfg = PipelineConfig()
        assert cfg.data_path == "data"
        assert cfg.output_path == "data/results"
        assert cfg.log_level == "INFO"

class TestGetConfig:
    def test_singleton_behavior(self):
        reset_config()
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_env_override_memory(self, monkeypatch):
        reset_config()
        monkeypatch.setenv("TURBULENCE_MEMORY_LIMIT_GB", "8")
        cfg = get_config()
        assert cfg.turbulence.memory_limit_bytes == 8 * 1024**3

    def test_env_override_re_lambda(self, monkeypatch):
        reset_config()
        monkeypatch.setenv("TURBULENCE_RE_LAMBDA", "300,500")
        cfg = get_config()
        assert cfg.turbulence.re_lambda_values == [300, 500]

    def test_env_override_thresholds(self, monkeypatch):
        reset_config()
        monkeypatch.setenv("TURBULENCE_THRESHOLDS", "2.5,3.5")
        cfg = get_config()
        assert cfg.turbulence.vorticity_thresholds == [2.5, 3.5]

    def test_invalid_env_values_ignored(self, monkeypatch):
        reset_config()
        monkeypatch.setenv("TURBULENCE_RE_LAMBDA", "invalid")
        cfg = get_config()
        # Should fall back to default
        assert cfg.turbulence.re_lambda_values == [200, 400, 600]

class TestValidateConfig:
    def test_valid_config(self):
        cfg = PipelineConfig()
        assert validate_config(cfg) is True

    def test_invalid_re_lambda_type(self):
        cfg = PipelineConfig(turbulence=TurbulenceConfig(re_lambda_values=["a", "b"]))
        with pytest.raises(ValueError, match="Re_λ values must be positive integers"):
            validate_config(cfg)

    def test_invalid_thresholds(self):
        cfg = PipelineConfig(turbulence=TurbulenceConfig(vorticity_thresholds=[-1.0]))
        with pytest.raises(ValueError, match="Vorticity thresholds must be positive numbers"):
            validate_config(cfg)

    def test_memory_too_low(self):
        cfg = PipelineConfig(turbulence=TurbulenceConfig(memory_limit_bytes=500))
        with pytest.raises(ValueError, match="Memory limit must be at least"):
            validate_config(cfg)