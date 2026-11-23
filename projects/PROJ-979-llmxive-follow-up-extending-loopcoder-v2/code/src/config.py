"""
Configuration management for the project.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values as per T000-config specification
DEFAULT_CONFIG = {
    # Core scientific constants
    "NON_INFERIORITY_DELTA": 0.05,
    "ENTROPY_N_SAMPLES": 10,
    "CONVERGENCE_K_RANGE": [1, 2, 3],
    "STRATA_THRESHOLD": 50,

    # Model inference parameters
    "MODEL_TEMP": 0.7,
    "MODEL_TOP_P": 0.95,
    "MODEL_NAME": "meta-llama/CodeLlama-7b-Instruct-hf",  # verified public model

    # Reproducibility
    "RANDOM_SEED": 42,

    # Directory locations (relative to project root)
    "DATA_DIR": "data",
    "OUTPUT_DIR": "data/processed"
}

# Path to the optional YAML configuration file that can override defaults
CONFIG_PATH = Path("code/src/config.yaml")


def load_config() -> Dict[str, Any]:
    """Load configuration from a YAML file if it exists, otherwise return defaults."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG.copy()


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Retrieve a configuration value.

    The function first looks in the user‑provided config file (if any) and falls back
    to the DEFAULT_CONFIG. If the key is missing from both, the supplied ``default``
    argument is returned; if ``default`` is ``None`` the value from DEFAULT_CONFIG
    (or ``None``) is returned.
    """
    config = load_config()
    if key in config:
        return config[key]
    if default is not None:
        return default
    return DEFAULT_CONFIG.get(key)


def ensure_config_file() -> None:
    """
    Ensure that a configuration file exists.

    If ``code/src/config.yaml`` does not exist, it is created with the default
    values. Existing files are left untouched.
    """
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f)


def main() -> None:
    """Convenient entry‑point for ``python -m src.config``."""
    ensure_config_file()
    config = load_config()
    print(f"Loaded configuration ({CONFIG_PATH}):")
    for k, v in config.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
