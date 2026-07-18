"""
Configuration management for llmXive research pipeline.
Provides a unified interface for loading settings from YAML and environment variables.
"""
import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

class Config:
    """
    Central configuration class.
    Loads settings from code/config.yaml and overrides with environment variables.
    """

    _instance: Optional['Config'] = None

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config.yaml. Defaults to 'code/config.yaml'.
        """
        if config_path is None:
            # Determine project root relative to this file
            current_dir = Path(__file__).parent
            config_path = current_dir / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._load_env_overrides()

    def _load_config(self) -> None:
        """Load base configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

    def _load_env_overrides(self) -> None:
        """Override configuration with environment variables."""
        # Map environment variables to config keys
        env_mappings = {
            'RANDOM_SEED': ('project', 'seed'),
            'DATA_RAW': ('paths', 'data_raw'),
            'DATA_PROCESSED': ('paths', 'data_processed'),
            'DATA_HELD_OUT': ('paths', 'data_held_out'),
            'CONTRACTS_ROOT': ('paths', 'contracts'),
            'RULE_INDUCTION_MAX_DEPTH': ('rule_induction', 'max_depth'),
            'COMPRESSION_FIDELITY_THRESHOLD': ('rule_induction', 'fidelity_threshold'),
            'SENTENCE_TRANSFORMER_MODEL': ('metrics', 'sentence_transformer_model'),
            'EMBEDDING_BATCH_SIZE': ('metrics', 'embedding_batch_size'),
            'EMBEDDING_DEVICE': ('metrics', 'embedding_device'),
            'LOG_LEVEL': ('logging', 'level'),
        }

        for env_var, config_keys in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert types if necessary
                if config_keys[-1] == 'seed' or config_keys[-1] == 'max_depth' or config_keys[-1] == 'embedding_batch_size':
                    value = int(value)
                elif config_keys[-1] == 'fidelity_threshold':
                    value = float(value)
                
                self._set_nested_value(self._config, config_keys, value)

    def _set_nested_value(self, d: Dict, keys: tuple, value: Any) -> None:
        """Set a value in a nested dictionary using a tuple of keys."""
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value by nested key path.
        
        Args:
            *keys: Nested keys (e.g., 'project', 'seed')
            default: Default value if key not found
        
        Returns:
            The configuration value or default
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def get_paths(self) -> Dict[str, Path]:
        """
        Get all configured paths as Path objects.
        
        Returns:
            Dictionary of path names to Path objects
        """
        paths = {}
        path_keys = ['data_raw', 'data_processed', 'data_held_out', 'contracts']
        
        for key in path_keys:
            raw_path = self.get('paths', key)
            if raw_path:
                # Resolve relative to project root (parent of code/)
                project_root = self.config_path.parent.parent
                paths[key] = project_root / raw_path
            else:
                paths[key] = None
        
        return paths

    def get_seed(self) -> int:
        """Get the random seed for reproducibility."""
        return self.get('project', 'seed', default=42)

    def get_rule_induction_params(self) -> Dict[str, Any]:
        """Get rule induction model parameters."""
        return {
            'max_depth': self.get('rule_induction', 'max_depth', default=3),
            'min_samples_split': self.get('rule_induction', 'min_samples_split', default=2),
            'min_samples_leaf': self.get('rule_induction', 'min_samples_leaf', default=1),
            'fidelity_threshold': self.get('rule_induction', 'fidelity_threshold', default=0.90),
        }

    def get_embedding_config(self) -> Dict[str, Any]:
        """Get sentence transformer embedding configuration."""
        return {
            'model': self.get('metrics', 'sentence_transformer_model', default='all-MiniLM-L6-v2'),
            'batch_size': self.get('metrics', 'embedding_batch_size', default=32),
            'device': self.get('metrics', 'embedding_device', default='cpu'),
        }

    def __repr__(self) -> str:
        return f"Config(config_path={self.config_path})"

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get or create the global Config instance.
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Config instance
    """
    if Config._instance is None:
        Config._instance = Config(config_path)
    return Config._instance