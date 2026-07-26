"""
Configuration management for llmXive pipeline.
Handles seeds, paths, timeout limits, and other project settings.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from secrets_manager import SecretsManager, init_secrets, validate_secrets, get_hf_token, get_prolific_api_key

# Default configuration values
DEFAULT_CONFIG = {
    "seeds": {
        "random_seed": 42,
        "torch_seed": 42,
        "numpy_seed": 42,
    },
    "paths": {
        "project_root": Path.cwd(),
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_interim": "data/interim",
        "data_results": "data/results",
        "code_dir": "code",
        "tests_dir": "tests",
        "figures_dir": "figures",
        "state_dir": "state",
    },
    "timeouts": {
        "inference_timeout_seconds": 300,  # 5 minutes per prompt
        "pipeline_max_runtime_seconds": 3600,  # 1 hour total
        "dataset_download_timeout_seconds": 600,  # 10 minutes
    },
    "model": {
        "model_name": "TinyLlama-1.1B-Chat",
        "quantization_bits": 4,
        "max_tokens": 512,
        "temperature": 0.7,
    },
    "analysis": {
        "correlation_threshold": 0.3,
        "p_value_threshold": 0.05,
        "kappa_threshold": 0.7,
    },
}


class Config:
    """
    Central configuration manager for the llmXive pipeline.
    Loads configuration from YAML files and environment variables.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to config.yaml. If None, looks in project root.
        """
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._config_path = config_path or Path.cwd() / "config.yaml"
        self._secrets_manager: Optional[SecretsManager] = None

        # Load configuration from file if it exists
        if self._config_path.exists():
            self._load_config_file()

        # Initialize secrets manager
        self._init_secrets()

    def _load_config_file(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self._config_path, 'r') as f:
                file_config = yaml.safe_load(f) or {}

            # Deep merge with defaults
            self._deep_merge(self._config, file_config)
            print(f"Loaded configuration from {self._config_path}")
        except Exception as e:
            print(f"Warning: Could not load config file: {e}. Using defaults.")

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _init_secrets(self) -> None:
        """Initialize secrets manager and inject tokens into config."""
        try:
            self._secrets_manager = init_secrets()
            # Inject tokens into config for easy access
            self._config["secrets"] = {
                "hf_token": get_hf_token(),
                "prolific_api_key": get_prolific_api_key(),
            }
        except ValueError as e:
            print(f"Warning: {e}")
            self._config["secrets"] = {}

    @property
    def seeds(self) -> Dict[str, int]:
        """Get seed configuration."""
        return self._config["seeds"]

    @property
    def paths(self) -> Dict[str, Path]:
        """Get path configuration as Path objects."""
        paths = {}
        for key, value in self._config["paths"].items():
            if isinstance(value, str):
                paths[key] = Path(value)
            else:
                paths[key] = value
        return paths

    @property
    def timeouts(self) -> Dict[str, int]:
        """Get timeout configuration."""
        return self._config["timeouts"]

    @property
    def model(self) -> Dict[str, Any]:
        """Get model configuration."""
        return self._config["model"]

    @property
    def analysis(self) -> Dict[str, Any]:
        """Get analysis configuration."""
        return self._config["analysis"]

    @property
    def secrets(self) -> Dict[str, str]:
        """Get secrets configuration."""
        return self._config.get("secrets", {})

    def get_path(self, key: str) -> Path:
        """Get a specific path by key."""
        return self.paths.get(key, Path.cwd())

    def get_timeout(self, key: str) -> int:
        """Get a specific timeout by key."""
        return self.timeouts.get(key, 300)

    def save_config(self, path: Optional[Path] = None) -> None:
        """Save current configuration to YAML file."""
        save_path = path or self._config_path
        with open(save_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
        print(f"Configuration saved to {save_path}")

    def validate(self) -> bool:
        """Validate configuration and required secrets."""
        # Check paths exist or can be created
        for key, path in self.paths.items():
            full_path = Path(path)
            if not full_path.exists():
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {full_path}")
                except Exception as e:
                    print(f"Error creating directory {full_path}: {e}")
                    return False

        # Validate secrets
        if not validate_secrets():
            return False

        return True


def get_config(config_path: Optional[Path] = None) -> Config:
    """
    Get or create a singleton Config instance.

    Args:
        config_path: Optional path to config file.

    Returns:
        Config instance.
    """
    return Config(config_path)
