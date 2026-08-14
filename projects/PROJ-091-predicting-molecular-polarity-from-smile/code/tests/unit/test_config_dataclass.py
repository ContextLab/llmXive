"""
Unit tests for the refactored config.py dataclass implementation (T039a).
Verifies that the config module correctly uses dataclasses and maintains
backward compatibility for public API functions.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import (
    load_hyperparameters,
    get_config_summary,
    PipelineConfig,
    ModelConfig,
    PreprocessingConfig,
    TrainingConfig,
    RANDOM_SEED,
    LIGHTGBM_SEED,
)

def test_dataclass_instantiation():
    """Test that dataclasses can be instantiated correctly."""
    model = ModelConfig()
    assert model.n_estimators == 1000
    assert model.learning_rate == 0.05
    assert model.random_state == LIGHTGBM_SEED

    preproc = PreprocessingConfig()
    assert preproc.nan_threshold_drop == 0.05

    train = TrainingConfig()
    assert train.test_size == 0.2

    pipeline = PipelineConfig()
    assert isinstance(pipeline.model, ModelConfig)
    assert isinstance(pipeline.preprocessing, PreprocessingConfig)

def test_load_hyperparameters_defaults():
    """Test loading hyperparameters returns a PipelineConfig dataclass."""
    config = load_hyperparameters()
    assert isinstance(config, PipelineConfig)
    assert isinstance(config.model, ModelConfig)
    assert config.model.n_estimators == 1000
    assert config.training.random_state == RANDOM_SEED

def test_load_hyperparameters_yaml_override(tmp_path):
    """Test that YAML config overrides defaults correctly."""
    yaml_content = {
        "model": {
            "n_estimators": 500,
            "learning_rate": 0.1
        },
        "preprocessing": {
            "nan_threshold_drop": 0.1
        }
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(yaml_content, f)

    config = load_hyperparameters(config_file)
    
    assert isinstance(config, PipelineConfig)
    assert config.model.n_estimators == 500
    assert config.model.learning_rate == 0.1
    assert config.preprocessing.nan_threshold_drop == 0.1
    
    # Verify seeds are still hardcoded and not overridden
    assert config.model.random_state == LIGHTGBM_SEED
    assert config.training.random_state == RANDOM_SEED

def test_load_hyperparameters_missing_file():
    """Test that missing config file returns defaults."""
    config = load_hyperparameters(Path("/nonexistent/path/config.yaml"))
    assert isinstance(config, PipelineConfig)
    assert config.model.n_estimators == 1000

def test_config_summary():
    """Test that config summary returns a valid string."""
    summary = get_config_summary()
    assert "Config Summary" in summary
    assert str(PROJECT_ROOT) in summary or str(RANDOM_SEED) in summary
    
def test_to_dict_serialization():
    """Test that PipelineConfig can be converted to dict."""
    config = PipelineConfig()
    config_dict = config.to_dict()
    
    assert isinstance(config_dict, dict)
    assert "model" in config_dict
    assert "preprocessing" in config_dict
    assert "training" in config_dict
    assert config_dict["model"]["n_estimators"] == 1000

def test_dataclass_immutability_of_seeds():
    """Verify that seeds in the loaded config are always the hardcoded constants."""
    # Create a YAML that tries to override seeds
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "model": {"random_state": 999},
            "training": {"random_state": 999}
        }, f)
        temp_path = Path(f.name)

    try:
        config = load_hyperparameters(temp_path)
        # Seeds must be the hardcoded ones, not 999
        assert config.model.random_state == LIGHTGBM_SEED
        assert config.model.random_state != 999
        assert config.training.random_state == RANDOM_SEED
    finally:
        temp_path.unlink()
