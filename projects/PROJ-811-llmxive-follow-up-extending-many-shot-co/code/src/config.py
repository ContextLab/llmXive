import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root is the parent of the 'code' directory
# Assuming the project structure is:
# projects/PROJ-811-.../
#   code/
#     src/
#       config.py
#   .env
#   config.yaml
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Config:
    """
    Centralized configuration management.
    Loads settings from .env (environment variables) and config.yaml (YAML file).
    Environment variables take precedence over YAML defaults.
    """
    _instance: Optional['Config'] = None

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()

    @classmethod
    def get_instance(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton for testing purposes."""
        cls._instance = None

    def _load_config(self):
        """
        Load configuration from .env and config.yaml.
        Priority: .env > config.yaml > defaults
        """
        # Load .env file if it exists
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(f".env file not found at {env_path}. Using defaults or YAML.")

        # Load YAML config if it exists
        yaml_path = PROJECT_ROOT / "config.yaml"
        yaml_config = {}
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded YAML config from {yaml_path}")
        else:
            logger.warning(f"config.yaml not found at {yaml_path}. Using defaults.")

        # Merge configurations
        # Defaults
        defaults = {
            "seeds": [42, 123, 456],
            "model_paths": {
                "reasoning": "models/reasoning_model.gguf",
                "non_reasoning": "models/non_reasoning_model.gguf"
            },
            "inference_params": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            },
            "parser_params": {
                "max_cycle_length": 5,
                "max_incoming_edges": 3
            },
            "dataset": {
                "name": "aaabiao/DAG_sft",
                "split": "train"
            },
            "data_dirs": {
                "raw": "data/raw",
                "processed": "data/processed",
                "results": "data/results",
                "artifacts": "artifacts"
            }
        }

        # Merge YAML into defaults
        merged = self._deep_merge(defaults, yaml_config)

        # Override with environment variables
        self._apply_env_overrides(merged)

        self._config = merged

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, config: Dict, prefix: str = ""):
        """
        Apply environment variable overrides to the config dictionary.
        Supports dot notation in env vars (e.g., SEEDS, MODEL_PATHS_REASONING).
        """
        for key, value in config.items():
            env_key = f"{prefix}{key.upper()}" if prefix else key.upper()
            env_value = os.getenv(env_key)

            if env_value is not None:
                if isinstance(value, dict):
                    # Try to parse as nested config or specific type
                    if env_value.startswith('{'):
                        try:
                            import json
                            config[key] = json.loads(env_value)
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse JSON for env var {env_key}")
                    else:
                        # Treat as a string override for the whole dict or specific keys if flattened
                        # For simplicity in this implementation, we assume nested dicts are overridden by JSON strings
                        # or we look for specific nested env vars like MODEL_PATHS_REASONING
                        pass
                else:
                    # Convert string to appropriate type
                    if isinstance(value, bool):
                        config[key] = env_value.lower() in ('true', '1', 't', 'yes')
                    elif isinstance(value, int):
                        config[key] = int(env_value)
                    elif isinstance(value, float):
                        config[key] = float(env_value)
                    else:
                        config[key] = env_value
            elif isinstance(value, dict):
                # Recursively check nested dicts for env vars
                self._apply_env_overrides(value, f"{env_key}_")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation (e.g., 'model_paths.reasoning').
        """
        keys = key.split('.')
        current = self._config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def get_seeds(self) -> list:
        """Get list of random seeds."""
        return self.get('seeds', [42])

    def get_model_path(self, model_type: str = "reasoning") -> str:
        """Get model path for a specific type."""
        return self.get(f'model_paths.{model_type}', f'models/{model_type}_model.gguf')

    def get_inference_params(self) -> dict:
        """Get inference parameters."""
        return self.get('inference_params', {})

    def get_parser_params(self) -> dict:
        """Get parser parameters."""
        return self.get('parser_params', {})

    def get_dataset_info(self) -> dict:
        """Get dataset configuration."""
        return self.get('dataset', {})

    def get_processed_dir(self) -> Path:
        """Get the processed data directory path."""
        relative_path = self.get('data_dirs.processed', 'data/processed')
        return PROJECT_ROOT / relative_path

    def get_raw_dir(self) -> Path:
        """Get the raw data directory path."""
        relative_path = self.get('data_dirs.raw', 'data/raw')
        return PROJECT_ROOT / relative_path

    def get_results_dir(self) -> Path:
        """Get the results directory path."""
        relative_path = self.get('data_dirs.results', 'data/results')
        return PROJECT_ROOT / relative_path

    def get_artifacts_dir(self) -> Path:
        """Get the artifacts directory path."""
        relative_path = self.get('data_dirs.artifacts', 'artifacts')
        return PROJECT_ROOT / relative_path

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()

def get_config() -> Config:
    """Convenience function to get the config singleton."""
    return Config.get_instance()
