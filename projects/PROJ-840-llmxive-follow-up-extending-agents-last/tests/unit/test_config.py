import os
import pytest
import yaml
from pathlib import Path

from utils.config import (
    ModelConfig,
    CheckpointConfig,
    LoggingConfig,
    DataPathsConfig,
    NormalizationConfig,
    StatsConfig,
    PipelineConfig,
    load_config,
    validate_config
)

@pytest.fixture
def sample_config_file(tmp_path):
    """Create a sample YAML config file for testing."""
    config_data = {
        "model": {
            "path": "/models/llama-7b.gguf",
            "quantization": "Q4_K_M"
        },
        "checkpoint": {
            "interval_n": 5,
            "enabled": True
        },
        "logging": {
            "level": "INFO",
            "file": "logs/pipeline.log"
        },
        "data_paths": {
            "raw": "data/raw",
            "processed": "data/processed",
            "output": "data/output"
        },
        "normalization": {
            "float_tolerance": 1e-6
        },
        "stats": {
            "test_method": "mcnemar",
            "correction": "bonferroni"
        }
    }
    
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    
    return str(config_path)

class TestConfigDataClasses:
    def test_model_config_creation(self):
        """Verify ModelConfig dataclass creation."""
        config = ModelConfig(path="/test/model.gguf", quantization="Q4_K_M")
        assert config.path == "/test/model.gguf"
        assert config.quantization == "Q4_K_M"

    def test_checkpoint_config_creation(self):
        """Verify CheckpointConfig dataclass creation."""
        config = CheckpointConfig(interval_n=5, enabled=True)
        assert config.interval_n == 5
        assert config.enabled is True

    def test_normalization_config_creation(self):
        """Verify NormalizationConfig dataclass creation."""
        config = NormalizationConfig(float_tolerance=1e-6)
        assert config.float_tolerance == 1e-6

class TestLoadConfig:
    def test_load_config_success(self, sample_config_file):
        """Verify successful config loading."""
        config = load_config(sample_config_file)
        
        assert config is not None
        assert config.model.path == "/models/llama-7b.gguf"
        assert config.checkpoint.interval_n == 5
        assert config.normalization.float_tolerance == 1e-6

    def test_load_config_missing_file(self):
        """Verify error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_invalid_yaml(self, tmp_path):
        """Verify error handling for invalid YAML."""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            load_config(str(invalid_file))

class TestValidateConfig:
    def test_validate_config_valid(self, sample_config_file):
        """Verify validation passes for valid config."""
        config = load_config(sample_config_file)
        is_valid = validate_config(config)
        assert is_valid is True

    def test_validate_config_missing_required(self, tmp_path):
        """Verify validation fails for missing required fields."""
        config_data = {
            "model": {
                "path": "/test/model.gguf"
                # Missing quantization
            }
        }
        
        config_file = tmp_path / "partial.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(str(config_file))
        is_valid = validate_config(config)
        assert is_valid is False

class TestCheckpointConfig:
    def test_checkpoint_interval_parsing(self, sample_config_file):
        """Verify checkpoint interval is correctly parsed."""
        config = load_config(sample_config_file)
        assert config.checkpoint.interval_n == 5
        assert isinstance(config.checkpoint.interval_n, int)

    def test_checkpoint_enabled_flag(self, sample_config_file):
        """Verify checkpoint enabled flag is correctly parsed."""
        config = load_config(sample_config_file)
        assert config.checkpoint.enabled is True

class TestNormalizationConfig:
    def test_float_tolerance_precision(self, sample_config_file):
        """Verify float tolerance is set to 1e-6 as per FR-001."""
        config = load_config(sample_config_file)
        assert config.normalization.float_tolerance == 1e-6
        assert isinstance(config.normalization.float_tolerance, float)
