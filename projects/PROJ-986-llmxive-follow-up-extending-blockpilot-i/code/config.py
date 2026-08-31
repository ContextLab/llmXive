import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

@dataclass
class DatasetConfig:
    name: str = "gsm8k"
    split: str = "train"
    streaming: bool = True
    num_samples: int = 1000
    path: Optional[str] = None

@dataclass
class ModelConfig:
    model_name: str = "HuggingFaceTB/SmolLM-135M"  # Small model for feasibility
    device: str = "cpu"
    dtype: str = "float32"
    max_new_tokens: int = 32

@dataclass
class SweepConfig:
    block_sizes: list = field(default_factory=lambda: [1, 2, 4, 8, 16, 32])
    num_samples: int = 5
    timeout_seconds: int = 21600  # 6 hours

@dataclass
class FeatureConfig:
    prompt_length: bool = True
    attention_entropy: bool = True
    hidden_state_norm: bool = True

@dataclass
class TrainingConfig:
    models: list = field(default_factory=lambda: ["xgboost", "random_forest", "decision_tree"])
    test_split: float = 0.2
    seed: int = 42

@dataclass
class PathsConfig:
    data_raw: str = "data/raw"
    data_processed: str = "data/processed"
    data_models: str = "data/models"
    code: str = "code"
    tests: str = "tests"

@dataclass
class Config:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    sweep: SweepConfig = field(default_factory=SweepConfig)
    feature: FeatureConfig = field(default_factory=FeatureConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file or environment variables."""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        return Config(
            dataset=DatasetConfig(**data.get('dataset', {})),
            model=ModelConfig(**data.get('model', {})),
            sweep=SweepConfig(**data.get('sweep', {})),
            feature=FeatureConfig(**data.get('feature', {})),
            training=TrainingConfig(**data.get('training', {})),
            paths=PathsConfig(**data.get('paths', {}))
        )
    return Config()

def get_config_or_default(key: str, default: Any = None) -> Any:
    config = load_config()
    # Simple lookup for top-level or nested keys
    parts = key.split('.')
    obj = config
    for part in parts:
        if hasattr(obj, part):
            obj = getattr(obj, part)
        else:
            return default
    return obj

def validate_config(config: Config) -> bool:
    # Basic validation
    if not config.model.model_name:
        raise ValueError("Model name must be specified")
    return True

def save_config(config: Config, path: str):
    data = {
        'dataset': vars(config.dataset),
        'model': vars(config.model),
        'sweep': vars(config.sweep),
        'feature': vars(config.feature),
        'training': vars(config.training),
        'paths': vars(config.paths)
    }
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def get_config_from_env() -> Config:
    # Override config with environment variables if present
    config = load_config()
    if os.getenv('MODEL_NAME'):
        config.model.model_name = os.getenv('MODEL_NAME')
    if os.getenv('DEVICE'):
        config.model.device = os.getenv('DEVICE')
    return config

def get_config() -> Config:
    return get_config_from_env()
