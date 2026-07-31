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

    def __getattr__(self, name):
        """Permissive fallback for any unknown logger-style attributes."""
        def _noop(*args, **kwargs):
            return None
        return _noop

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
        # Map schema keys to dataclass keys
        model_data = data['model']
        config.model = ModelConfig(
            model_path=model_data.get('path', model_data.get('model_path', "")),
            quantization=model_data.get('quantization', "Q4_K_M"),
            context_window=model_data.get('max_context_length', model_data.get('context_window', 4096)),
            max_tokens=model_data.get('max_tokens', 512)
        )
    if 'checkpoint' in data:
        ckpt_data = data['checkpoint']
        config.checkpoint = CheckpointConfig(
            interval=ckpt_data.get('interval_n', ckpt_data.get('interval', 3)),
            compression=ckpt_data.get('compression_method', ckpt_data.get('compression', "truncation")),
            max_size=ckpt_data.get('max_size', 1024)
        )
    if 'logging' in data:
        log_data = data['logging']
        config.logging = LoggingConfig(
            level=log_data.get('level', "INFO"),
            file=log_data.get('file'),
            format=log_data.get('format', "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    if 'data_paths' in data:
        paths_data = data['data_paths']
        config.paths = DataPathsConfig(
            raw_data=paths_data.get('raw', paths_data.get('raw_data', "data/raw")),
            processed_data=paths_data.get('processed', paths_data.get('processed_data', "data/processed")),
            figures=paths_data.get('figures', "figures")
        )
    if 'normalization' in data:
        norm_data = data['normalization']
        config.normalization = NormalizationConfig(
            tolerance=norm_data.get('float_tolerance', norm_data.get('tolerance', 1e-6)),
            strip_timestamps=norm_data.get('timestamp_stripping', norm_data.get('strip_timestamps', True)),
            canonicalize_ids=norm_data.get('id_canonicalization', norm_data.get('canonicalize_ids', True))
        )
    if 'stats' in data:
        stats_data = data['stats']
        config.stats = StatsConfig(
            test=stats_data.get('test', "mcnemar"),
            alpha=stats_data.get('alpha', 0.05),
            correction=stats_data.get('correction', "bonferroni")
        )
    if 'runner' in data:
        runner_data = data['runner']
        config.runner = RunnerConfig(
            checkpoint_interval=runner_data.get('checkpoint_interval', 0),
            memory_limit=runner_data.get('max_memory_gb', runner_data.get('memory_limit', 7)) * 1000,
            timeout=runner_data.get('timeout_hours', runner_data.get('timeout', 6)) * 3600,
            model_path=runner_data.get('model_path', "")
        )
    
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