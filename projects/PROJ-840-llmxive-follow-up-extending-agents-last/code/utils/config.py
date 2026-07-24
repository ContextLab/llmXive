import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import logging
import sys

@dataclass
class ModelConfig:
    path: str = "models/llama-3-8b-instruct.Q4_K_M.gguf"
    quantization: str = "Q4_K_M"
    max_tokens: int = 4096

@dataclass
class CheckpointConfig:
    interval: int = 3
    max_tokens: int = 2048

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/llmxive.log"

@dataclass
class DataPathsConfig:
    raw_data: str = "data/raw"
    processed_data: str = "data/processed"
    models: str = "models"

@dataclass
class NormalizationConfig:
    float_tolerance: float = 1e-6

@dataclass
class StatsConfig:
    alpha: float = 0.05
    method: str = "mcnemar"

@dataclass
class RunnerConfig:
    timeout_seconds: int = 21600
    memory_limit_mb: int = 7000
    checkpoint_interval: int = 0  # Added to satisfy runner.py contract

    def __init__(self, timeout_seconds: int = 21600, memory_limit_mb: int = 7000, checkpoint_interval: int = 0):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.checkpoint_interval = checkpoint_interval

@dataclass
class PipelineConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    data_paths: DataPathsConfig = field(default_factory=DataPathsConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    stats: StatsConfig = field(default_factory=StatsConfig)
    runner: RunnerConfig = field(default_factory=lambda: RunnerConfig())

class PipelineConfigWrapper:
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = PipelineConfig()
        self._update_from_dict(config_dict)
    
    def _update_from_dict(self, config_dict: Dict[str, Any]):
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                attr = getattr(self.config, key)
                if hasattr(attr, '__dataclass_fields__'):
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if hasattr(attr, sub_key):
                                setattr(attr, sub_key, sub_value)
                else:
                    setattr(self.config, key, value)

def load_config(config_path: Path) -> PipelineConfigWrapper:
    """
    Loads configuration from a YAML file.
    """
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    return PipelineConfigWrapper(config_dict)

def validate_config(config: PipelineConfigWrapper) -> bool:
    """
    Validates the configuration.
    """
    if not config.config.model.path:
        return False
    if config.config.runner.memory_limit_mb <= 0:
        return False
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test configuration loading")
    parser.add_argument("--config", type=str, default="code/utils/config_schema.yaml", help="Config file path")
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    
    config = load_config(config_path)
    print(f"Config loaded successfully:")
    print(f"  Model path: {config.config.model.path}")
    print(f"  Checkpoint interval: {config.config.checkpoint.interval}")
    print(f"  Runner memory limit: {config.config.runner.memory_limit_mb} MB")

if __name__ == "__main__":
    main()