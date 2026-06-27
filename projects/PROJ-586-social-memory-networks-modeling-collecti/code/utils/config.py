"""Environment management and configuration for social memory networks experiments.

This module provides centralized configuration management with support for:
- YAML configuration files
- Environment variable overrides
- Default values with validation
- Reproducibility settings (random seeds)
- Device configuration (CPU/GPU)
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field

# Try to import yaml, fall back to json if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    import json

from .logging import get_logger


@dataclass
class Config:
    """Centralized configuration container for experiment settings.

    Attributes:
        seed: Random seed for reproducibility (default: 42)
        device: Computing device ('cpu' or 'cuda') (default: 'cpu')
        log_level: Logging level (default: 'INFO')
        experiment_name: Name for the current experiment run
        output_dir: Directory for experiment outputs
        num_agents: Number of agents in simulation (default: 2)
        context_window: Context window size in tokens (default: 512)
        batch_size: Batch size for processing (default: 1)
        max_games: Maximum number of games per condition (default: 1000)
    """
    seed: int = 42
    device: str = 'cpu'
    log_level: str = 'INFO'
    experiment_name: str = 'social_memory_experiment'
    output_dir: str = 'data/'
    num_agents: int = 2
    context_window: int = 512
    batch_size: int = 1
    max_games: int = 1000
    # Additional settings for memory buffer
    memory_capacity: int = 100
    memory_action_timeout: float = 5.0
    # Model settings
    model_name: str = 'facebook/opt-125m'
    model_dtype: str = 'float32'
    # Analysis settings
    alpha: float = 0.05  # Significance level for statistical tests
    power_threshold: float = 0.70  # Minimum acceptable statistical power
    # Scaling analysis (per Geoffrey West feedback)
    agent_counts: list = field(default_factory=lambda: [3, 5, 7])
    games_per_agent_count: int = 800

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'seed': self.seed,
            'device': self.device,
            'log_level': self.log_level,
            'experiment_name': self.experiment_name,
            'output_dir': self.output_dir,
            'num_agents': self.num_agents,
            'context_window': self.context_window,
            'batch_size': self.batch_size,
            'max_games': self.max_games,
            'memory_capacity': self.memory_capacity,
            'memory_action_timeout': self.memory_action_timeout,
            'model_name': self.model_name,
            'model_dtype': self.model_dtype,
            'alpha': self.alpha,
            'power_threshold': self.power_threshold,
            'agent_counts': self.agent_counts,
            'games_per_agent_count': self.games_per_agent_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config instance from dictionary."""
        return cls(
            seed=int(data.get('seed', 42)),
            device=str(data.get('device', 'cpu')),
            log_level=str(data.get('log_level', 'INFO')),
            experiment_name=str(data.get('experiment_name', 'social_memory_experiment')),
            output_dir=str(data.get('output_dir', 'data/')),
            num_agents=int(data.get('num_agents', 2)),
            context_window=int(data.get('context_window', 512)),
            batch_size=int(data.get('batch_size', 1)),
            max_games=int(data.get('max_games', 1000)),
            memory_capacity=int(data.get('memory_capacity', 100)),
            memory_action_timeout=float(data.get('memory_action_timeout', 5.0)),
            model_name=str(data.get('model_name', 'facebook/opt-125m')),
            model_dtype=str(data.get('model_dtype', 'float32')),
            alpha=float(data.get('alpha', 0.05)),
            power_threshold=float(data.get('power_threshold', 0.70)),
            agent_counts=list(data.get('agent_counts', [3, 5, 7])),
            games_per_agent_count=int(data.get('games_per_agent_count', 800)),
        )

    def validate(self) -> None:
        """Validate configuration values and raise errors for invalid settings."""
        if self.seed < 0:
            raise ValueError(f"Seed must be non-negative, got {self.seed}")
        if self.device not in ('cpu', 'cuda', 'mps'):
            raise ValueError(f"Device must be 'cpu', 'cuda', or 'mps', got {self.device}")
        if self.log_level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            raise ValueError(f"Invalid log level: {self.log_level}")
        if self.num_agents < 1:
            raise ValueError(f"num_agents must be >= 1, got {self.num_agents}")
        if self.context_window < 1:
            raise ValueError(f"context_window must be >= 1, got {self.context_window}")
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        if self.max_games < 1:
            raise ValueError(f"max_games must be >= 1, got {self.max_games}")
        if self.alpha <= 0 or self.alpha >= 1:
            raise ValueError(f"alpha must be in (0, 1), got {self.alpha}")
        if self.power_threshold <= 0 or self.power_threshold >= 1:
            raise ValueError(f"power_threshold must be in (0, 1), got {self.power_threshold}")

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()


class ConfigManager:
    """Manages configuration loading, merging, and access.

    This class handles:
    - Loading configuration from YAML files
    - Merging configuration sources (file, env vars, defaults)
    - Caching loaded configuration
    - Providing configuration to other modules
    """

    _instance: Optional['ConfigManager'] = None
    _config: Optional[Config] = None
    _logger = None

    def __new__(cls):
        """Singleton pattern to ensure single config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize config manager."""
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._logger = get_logger(__name__)

    @property
    def config(self) -> Config:
        """Get the current configuration, loading if necessary."""
        if self._config is None:
            self._config = self.load()
        return self._config

    def load(self, config_path: Optional[Union[str, Path]] = None) -> Config:
        """Load configuration from file, environment, and defaults.

        Args:
            config_path: Path to config.yaml. If None, searches common locations.

        Returns:
            Config instance with merged settings.
        """
        if config_path is None:
            config_path = self._find_config_path()

        config_dict = self._load_from_file(config_path)
        config_dict = self._apply_env_overrides(config_dict)
        config = Config.from_dict(config_dict)

        self._logger.info(f"Configuration loaded from {config_path}")
        self._logger.info(f"  seed={config.seed}, device={config.device}")
        self._logger.info(f"  num_agents={config.num_agents}, max_games={config.max_games}")

        return config

    def reload(self, config_path: Optional[Union[str, Path]] = None) -> Config:
        """Reload configuration, clearing cache."""
        self._config = None
        return self.load(config_path)

    def _find_config_path(self) -> Path:
        """Find config.yaml in common locations."""
        search_paths = [
            Path('config.yaml'),
            Path('code/config.yaml'),
            Path('code/utils/config.yaml'),
            Path(__file__).parent / 'config.yaml',
            Path(__file__).parent.parent / 'config.yaml',
            Path(__file__).parent.parent.parent / 'config.yaml',
        ]

        for path in search_paths:
            if path.exists():
                self._logger.debug(f"Found config at {path}")
                return path

        self._logger.warning("No config.yaml found, using defaults")
        return search_paths[0]

    def _load_from_file(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        config_path = Path(config_path)

        if not config_path.exists():
            self._logger.warning(f"Config file not found: {config_path}")
            return {}

        try:
            if YAML_AVAILABLE:
                with open(config_path, 'r') as f:
                    data = yaml.safe_load(f)
            else:
                with open(config_path, 'r') as f:
                    data = json.load(f)

            if data is None:
                return {}
            return data

        except Exception as e:
            self._logger.error(f"Failed to load config from {config_path}: {e}")
            return {}

    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            'SEED': 'seed',
            'DEVICE': 'device',
            'LOG_LEVEL': 'log_level',
            'EXPERIMENT_NAME': 'experiment_name',
            'OUTPUT_DIR': 'output_dir',
            'NUM_AGENTS': 'num_agents',
            'CONTEXT_WINDOW': 'context_window',
            'BATCH_SIZE': 'batch_size',
            'MAX_GAMES': 'max_games',
            'MODEL_NAME': 'model_name',
            'ALPHA': 'alpha',
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.environ.get(f'SOCIAL_MEMORY_{env_var}')
            if env_value is not None:
                config_dict[config_key] = self._parse_env_value(config_key, env_value)
                self._logger.debug(f"Overrode {config_key} from env var SOCIAL_MEMORY_{env_var}")

        return config_dict

    def _parse_env_value(self, key: str, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        if key in ('seed', 'num_agents', 'context_window', 'batch_size', 'max_games'):
            return int(value)
        elif key in ('alpha', 'power_threshold', 'memory_action_timeout'):
            return float(value)
        else:
            return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self.config.to_dict().get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (updates in-memory config)."""
        config_dict = self.config.to_dict()
        config_dict[key] = value
        self._config = Config.from_dict(config_dict)


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create the global config manager singleton."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> Config:
    """Get the current configuration (convenience function)."""
    return get_config_manager().config


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from file (convenience function)."""
    return get_config_manager().load(config_path)


def reload_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Reload configuration from file (convenience function)."""
    return get_config_manager().reload(config_path)


def get(key: str, default: Any = None) -> Any:
    """Get a configuration value by key (convenience function)."""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> None:
    """Set a configuration value (convenience function)."""
    get_config_manager().set(key, value)


# Default configuration file content
DEFAULT_CONFIG_YAML = """# Social Memory Networks Experiment Configuration
# Generated by code/utils/config.py

# Reproducibility
seed: 42

# Computing device (cpu, cuda, mps)
device: cpu

# Logging
log_level: INFO
experiment_name: social_memory_experiment

# Output paths
output_dir: data/

# Simulation parameters
num_agents: 2
context_window: 512
batch_size: 1
max_games: 1000

# Memory buffer settings
memory_capacity: 100
memory_action_timeout: 5.0

# Model settings
model_name: facebook/opt-125m
model_dtype: float32

# Statistical analysis settings
alpha: 0.05
power_threshold: 0.70

# Scaling analysis (per Geoffrey West feedback on power-law relationships)
agent_counts: [3, 5, 7]
games_per_agent_count: 800
"""


def create_default_config(output_path: Optional[Union[str, Path]] = None) -> Path:
    """Create a default config.yaml file.

    Args:
        output_path: Path where to write the config file.
                    If None, writes to code/config.yaml.

    Returns:
        Path to the created config file.
    """
    if output_path is None:
        output_path = Path('code/config.yaml')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(DEFAULT_CONFIG_YAML)

    return output_path


# Convenience function to ensure config exists
def ensure_config_exists() -> Path:
    """Ensure config.yaml exists, creating it with defaults if necessary.

    Returns:
        Path to the config file.
    """
    search_paths = [
        Path('code/config.yaml'),
        Path('config.yaml'),
    ]

    for path in search_paths:
        if path.exists():
            return path

    return create_default_config(search_paths[0])