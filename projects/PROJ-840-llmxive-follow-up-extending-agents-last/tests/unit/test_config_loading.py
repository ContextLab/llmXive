import pytest
import yaml
import os
import tempfile
from pathlib import Path

# Import from the project's utils module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from utils.config import load_config, validate_config, PipelineConfig, ModelConfig, CheckpointConfig

def test_load_config_from_schema():
    """Test that load_config correctly parses the YAML schema defined in config_schema.yaml."""
    # Create a temporary YAML file matching the schema
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_content = """
model:
  path: "models/test-model.gguf"
  quantization: "Q4_K_M"
  max_context_length: 8192
  n_gpu_layers: 0

checkpoint:
  interval_n: 10
  enabled: true
  compression_method: "abstraction"

logging:
  level: "DEBUG"
  file: "test.log"
  max_file_size_mb: 50
  backup_count: 3

data_paths:
  raw: "data/raw_test"
  processed: "data/processed_test"
  figures: "figures_test"

normalization:
  float_tolerance: 1e-5
  timestamp_stripping: false
  id_canonicalization: false

stats:
  test: "mcnemar"
  correction: "fdr"
  alpha: 0.01

runner:
  max_memory_gb: 16
  timeout_hours: 12
  cpu_only: true
"""
        f.write(yaml_content)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        
        # Verify ModelConfig mapping
        assert config.model.model_path == "models/test-model.gguf"
        assert config.model.quantization == "Q4_K_M"
        assert config.model.context_window == 8192
        
        # Verify CheckpointConfig mapping
        assert config.checkpoint.interval == 10
        assert config.checkpoint.compression == "abstraction"
        
        # Verify DataPathsConfig mapping
        assert config.paths.raw_data == "data/raw_test"
        assert config.paths.processed_data == "data/processed_test"
        assert config.paths.figures == "figures_test"
        
        # Verify RunnerConfig mapping (with unit conversion)
        assert config.runner.memory_limit == 16000.0
        assert config.runner.timeout == 12 * 3600
        
        # Verify StatsConfig mapping
        assert config.stats.correction == "fdr"
        assert config.stats.alpha == 0.01

    finally:
        os.unlink(temp_path)

def test_load_config_missing_file():
    """Test that load_config returns default config when file is missing."""
    config = load_config("nonexistent/path/config.yaml")
    assert isinstance(config, PipelineConfig)
    assert config.model.model_path == ""
    assert config.checkpoint.interval == 3

def test_validate_config_success():
    """Test validation with a valid config."""
    config = PipelineConfig()
    config.model.model_path = "models/test.gguf"
    config.runner.memory_limit = 7000.0
    config.runner.timeout = 3600
    
    assert validate_config(config) is True

def test_validate_config_missing_model_path():
    """Test validation fails without model path."""
    config = PipelineConfig()
    config.runner.memory_limit = 7000.0
    config.runner.timeout = 3600
    
    with pytest.raises(ValueError, match="Model path is required"):
        validate_config(config)

def test_validate_config_invalid_memory():
    """Test validation fails with invalid memory limit."""
    config = PipelineConfig()
    config.model.model_path = "models/test.gguf"
    config.runner.memory_limit = 0
    config.runner.timeout = 3600
    
    with pytest.raises(ValueError, match="Memory limit must be positive"):
        validate_config(config)

def test_runner_config_logger_compatibility():
    """Test that RunnerConfig tolerates logger-style method calls."""
    config = PipelineConfig().runner
    
    # These should not raise AttributeError
    config.info("Test info")
    config.debug("Test debug")
    config.warning("Test warning")
    config.error("Test error")
    config.critical("Test critical")
    
    # Unknown method should return a callable that does nothing
    unknown = config.some_unknown_method
    assert callable(unknown)
    assert unknown("arg1", kw="arg2") is None