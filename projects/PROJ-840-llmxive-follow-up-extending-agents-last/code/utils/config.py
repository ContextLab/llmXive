import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import logging

@dataclass
class ModelConfig:
    model_path: str = ""
    quantization: str = "Q4_K_M"
    context_window: int = 4096
    max_tokens: int = 512

@dataclass
class CheckpointConfig:
    interval: int = 3
    compression: str = "truncation"
    max_size: int = 1024

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: Optional[str] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

@dataclass
class DataPathsConfig:
    raw_data: str = "data/raw"
    processed_data: str = "data/processed"
    figures: str = "figures"

@dataclass
class NormalizationConfig:
    tolerance: float = 1e-6
    strip_timestamps: bool = True
    canonicalize_ids: bool = True

@dataclass
class StatsConfig:
    test: str = "mcnemar"
    alpha: float = 0.05
    correction: str = "bonferroni"

@dataclass
class RunnerConfig:
    """Configuration for the execution runner."""
    checkpoint_interval: int = 0
    memory_limit: float = 7000.0  # MB
    timeout: int = 21600  # seconds
    model_path: str = ""
    
    # Additional attributes for compatibility with logging_config
    def info(self, *args, **kwargs):
        """No-op for logging compatibility."""
        pass

    def debug(self, *args, **kwargs):
        """No-op for logging compatibility."""
        pass

    def warning(self, *args, **kwargs):
        """No-op for logging compatibility."""
        pass

    def error(self, *args, **kwargs):
        """No-op for logging compatibility."""
        pass

    def critical(self, *args, **kwargs):
        """No-op for logging compatibility."""
        pass

@dataclass
class PipelineConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    paths: DataPathsConfig = field(default_factory=DataPathsConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    stats: StatsConfig = field(default_factory=StatsConfig)
    runner: RunnerConfig = field(default_factory=RunnerConfig)

class PipelineConfigWrapper:
    """Wrapper to provide backward compatibility."""
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

def load_config(config_path: str = "code/utils/config.yaml") -> PipelineConfig:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        # Return default config
        return PipelineConfig()
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    config = PipelineConfig()
    if 'model' in data:
        config.model = ModelConfig(**data['model'])
    if 'checkpoint' in data:
        config.checkpoint = CheckpointConfig(**data['checkpoint'])
    if 'logging' in data:
        config.logging = LoggingConfig(**data['logging'])
    if 'paths' in data:
        config.paths = DataPathsConfig(**data['paths'])
    if 'normalization' in data:
        config.normalization = NormalizationConfig(**data['normalization'])
    if 'stats' in data:
        config.stats = StatsConfig(**data['stats'])
    if 'runner' in data:
        config.runner = RunnerConfig(**data['runner'])
    
    return config

def validate_config(config: PipelineConfig) -> bool:
    """Validate configuration values."""
    if not config.model.model_path:
        raise ValueError("Model path is required")
    if config.runner.memory_limit <= 0:
        raise ValueError("Memory limit must be positive")
    if config.runner.timeout <= 0:
        raise ValueError("Timeout must be positive")
    return True

def main():
    """Main entry point for config module."""
    config = load_config()
    print(f"Loaded config: {config}")

if __name__ == "__main__":
    main()