import os
import tempfile
import pytest
from pathlib import Path
from code.config import (
    Config, DatasetConfig, ModelConfig, SweepConfig, 
    FeatureConfig, TrainingConfig, PathsConfig,
    load_config, validate_config, save_config, get_config_or_default
)

class TestDatasetConfig:
    def test_default_values(self):
        config = DatasetConfig()
        assert config.name == "gsm8k"
        assert config.split == "train"
        assert config.streaming is True
        assert config.hf_dataset_id == "gsm8k"

    def test_get_hf_args(self):
        config = DatasetConfig(name="gsm8k", split="test", streaming=False)
        args = config.get_hf_args()
        assert args["name"] == "gsm8k"
        assert args["split"] == "test"
        assert args["streaming"] is False

class TestModelConfig:
    def test_default_values(self):
        config = ModelConfig()
        assert config.model_name == "Qwen/Qwen2.5-0.5B-Instruct"
        assert config.torch_dtype == "float32"

    def test_get_model_args_float16(self):
        config = ModelConfig(torch_dtype="float16")
        args = config.get_model_args()
        assert args["torch_dtype"] == "float16"

class TestSweepConfig:
    def test_default_block_sizes(self):
        config = SweepConfig()
        assert config.block_sizes == [1, 2, 4, 8, 16, 32]

    def test_empty_block_sizes_raises(self):
        with pytest.raises(ValueError):
            SweepConfig(block_sizes=[])

    def test_sorted_block_sizes(self):
        config = SweepConfig(block_sizes=[32, 1, 8])
        assert config.block_sizes == [1, 8, 32]

class TestTrainingConfig:
    def test_valid_split_ratio(self):
        config = TrainingConfig(test_split_ratio=0.2)
        assert config.test_split_ratio == 0.2

    def test_invalid_split_ratio(self):
        with pytest.raises(ValueError):
            config = TrainingConfig(test_split_ratio=1.5)
            validate_config(Config(training=config))

class TestConfig:
    def test_to_dict_roundtrip(self):
        config = Config()
        config_dict = config.to_dict()
        restored = Config.from_dict(config_dict)
        
        assert restored.dataset.name == config.dataset.name
        assert restored.sweep.block_sizes == config.sweep.block_sizes

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = Config()
            config.sweep.block_sizes = [1, 4, 16]
            
            save_config(config, str(config_path))
            assert config_path.exists()
            
            loaded = load_config(str(config_path))
            assert loaded.sweep.block_sizes == [1, 4, 16]

class TestConfigValidation:
    def test_valid_config(self):
        config = Config()
        assert validate_config(config) is True

    def test_invalid_block_sizes(self):
        config = Config()
        config.sweep.block_sizes = [-1, 2]
        with pytest.raises(ValueError):
            validate_config(config)

class TestGetConfigOrDefault:
    def test_existing_key(self):
        config = Config()
        value = get_config_or_default(config, "sweep", "block_sizes")
        assert value == [1, 2, 4, 8, 16, 32]

    def test_missing_key(self):
        config = Config()
        value = get_config_or_default(config, "sweep", "nonexistent", default=999)
        assert value == 999

    def test_invalid_section(self):
        config = Config()
        value = get_config_or_default(config, "invalid_section", "key", default=0)
        assert value == 0
