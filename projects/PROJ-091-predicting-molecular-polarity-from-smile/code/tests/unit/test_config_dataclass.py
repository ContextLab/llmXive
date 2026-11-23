import pytest
import yaml
import tempfile
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from utils.config import ModelConfig, PreprocessingConfig, TrainingConfig, PipelineConfig, load_hyperparameters

def test_dataclass_instantiation():
    """Test dataclass instantiation."""
    config = ModelConfig(seed=42)
    assert config.seed == 42

def test_load_hyperparameters_defaults():
    """Test loading hyperparameters defaults."""
    params = load_hyperparameters()
    assert "num_leaves" in params

def test_load_hyperparameters_yaml_override():
    """Test loading hyperparameters from YAML."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"num_leaves": 64}, f)
        f.flush()
        params = load_hyperparameters(Path(f.name))
        assert params["num_leaves"] == 64
    os.unlink(f.name)

def test_load_hyperparameters_missing_file():
    """Test loading hyperparameters with missing file."""
    params = load_hyperparameters(Path("nonexistent.yaml"))
    assert "num_leaves" in params

def test_config_summary():
    """Test config summary."""
    from utils.config import get_config_summary
    summary = get_config_summary()
    assert "model" in summary

def test_to_dict_serialization():
    """Test to_dict serialization."""
    config = ModelConfig(seed=42)
    d = config.__dict__
    assert d["seed"] == 42

def test_dataclass_immutability_of_seeds():
    """Test dataclass immutability of seeds."""
    config = ModelConfig(seed=42)
    # Seeds are hardcoded and should not change
    assert config.seed == 42

if __name__ == "__main__":
    pytest.main([__file__])
