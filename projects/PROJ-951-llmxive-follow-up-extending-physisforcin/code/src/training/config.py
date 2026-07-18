"""
Configuration management for the llmXive training pipeline.
Handles hyperparameters, CPU-only flags, and validation.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field, asdict, fields
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "experiment_name": "llmxive-physis-forcing",
    "seed": 42,
    "cpu_only": True,
    "max_memory_gb": 6.0,
    "batch_size": 16,
    "num_workers": 4,
    "learning_rate": 1e-4,
    "weight_decay": 1e-2,
    "epochs": 50,
    "warmup_epochs": 5,
    "filter_discard_percent": 0.4,
    "model_capacity_millions": 50,
    "timeout_hours": 4,
    "data_root": "data",
    "raw_data_dir": "data/raw",
    "curated_data_dir": "data/curated",
    "eval_data_dir": "data/eval",
    "output_dir": "data/eval",
    "checkpoint_dir": "data/checkpoints",
    "log_dir": "logs",
}

REQUIRED_KEYS = [
    "experiment_name",
    "seed",
    "cpu_only",
    "max_memory_gb",
    "batch_size",
    "learning_rate",
    "epochs",
    "filter_discard_percent",
    "data_root",
]

@dataclass
class TrainingConfig:
    """Dataclass representation of the training configuration."""
    experiment_name: str = DEFAULT_CONFIG["experiment_name"]
    seed: int = DEFAULT_CONFIG["seed"]
    cpu_only: bool = DEFAULT_CONFIG["cpu_only"]
    max_memory_gb: float = DEFAULT_CONFIG["max_memory_gb"]
    batch_size: int = DEFAULT_CONFIG["batch_size"]
    num_workers: int = DEFAULT_CONFIG["num_workers"]
    learning_rate: float = DEFAULT_CONFIG["learning_rate"]
    weight_decay: float = DEFAULT_CONFIG["weight_decay"]
    epochs: int = DEFAULT_CONFIG["epochs"]
    warmup_epochs: int = DEFAULT_CONFIG["warmup_epochs"]
    filter_discard_percent: float = DEFAULT_CONFIG["filter_discard_percent"]
    model_capacity_millions: int = DEFAULT_CONFIG["model_capacity_millions"]
    timeout_hours: int = DEFAULT_CONFIG["timeout_hours"]
    data_root: str = DEFAULT_CONFIG["data_root"]
    raw_data_dir: str = DEFAULT_CONFIG["raw_data_dir"]
    curated_data_dir: str = DEFAULT_CONFIG["curated_data_dir"]
    eval_data_dir: str = DEFAULT_CONFIG["eval_data_dir"]
    output_dir: str = DEFAULT_CONFIG["output_dir"]
    checkpoint_dir: str = DEFAULT_CONFIG["checkpoint_dir"]
    log_dir: str = DEFAULT_CONFIG["log_dir"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in fields(cls)})

def create_default_config() -> TrainingConfig:
    """Create a new default configuration."""
    logger.info("Creating default training configuration")
    return TrainingConfig()

def get_default_config() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()

def validate_config_schema(config: Dict[str, Any]) -> List[str]:
    """
    Validate that the configuration has all required keys and valid types.
    Returns a list of validation error messages (empty if valid).
    """
    errors = []

    # Check required keys
    for key in REQUIRED_KEYS:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    # Type validations
    type_checks = [
        ("experiment_name", str),
        ("seed", int),
        ("cpu_only", bool),
        ("max_memory_gb", (int, float)),
        ("batch_size", int),
        ("num_workers", int),
        ("learning_rate", (int, float)),
        ("weight_decay", (int, float)),
        ("epochs", int),
        ("warmup_epochs", int),
        ("filter_discard_percent", (int, float)),
        ("model_capacity_millions", int),
        ("timeout_hours", int),
        ("data_root", str),
        ("raw_data_dir", str),
        ("curated_data_dir", str),
        ("eval_data_dir", str),
        ("output_dir", str),
        ("checkpoint_dir", str),
        ("log_dir", str),
    ]

    for key, expected_type in type_checks:
        if key in config:
            if not isinstance(config[key], expected_type):
                errors.append(
                    f"Invalid type for {key}: expected {expected_type}, got {type(config[key]).__name__}"
                )

    # Value range validations
    if "filter_discard_percent" in config:
        val = config["filter_discard_percent"]
        if not 0.0 <= val <= 1.0:
            errors.append(
                f"filter_discard_percent must be between 0.0 and 1.0, got {val}"
            )

    if "max_memory_gb" in config:
        if config["max_memory_gb"] <= 0:
            errors.append(f"max_memory_gb must be positive, got {config['max_memory_gb']}")

    if "batch_size" in config:
        if config["batch_size"] <= 0:
            errors.append(f"batch_size must be positive, got {config['batch_size']}")

    if "epochs" in config:
        if config["epochs"] <= 0:
            errors.append(f"epochs must be positive, got {config['epochs']}")

    return errors

def load_config(config_path: Optional[Path] = None) -> TrainingConfig:
    """
    Load configuration from a YAML file.
    If no path is provided, looks for config.yaml in the project root.
    """
    if config_path is None:
        # Try to find config.yaml in standard locations
        possible_paths = [
            Path("config.yaml"),
            Path("code/config.yaml"),
            Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/config.yaml"),
        ]
        for p in possible_paths:
            if p.exists():
                config_path = p
                break

    if config_path is None or not Path(config_path).exists():
        logger.warning(
            f"No config file found at {config_path}, using defaults. "
            "Create a config.yaml to customize settings."
        )
        return create_default_config()

    logger.info(f"Loading configuration from {config_path}")
    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)

    # Merge with defaults
    full_config = {**DEFAULT_CONFIG, **config_dict}

    # Validate
    errors = validate_config_schema(full_config)
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    return TrainingConfig.from_dict(full_config)

def save_config(config: TrainingConfig, config_path: Path) -> None:
    """Save configuration to a YAML file."""
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

    logger.info(f"Saved configuration to {config_path}")

def get_filter_discard_threshold(config: Optional[TrainingConfig] = None) -> float:
    """
    Get the filter discard threshold as a percentile.
    Returns the value from config or default (0.4 -> 40th percentile).
    """
    if config is None:
        config = load_config()
    return config.filter_discard_percent

def get_config(config_path: Optional[Path] = None) -> TrainingConfig:
    """
    Convenience function to get the training configuration.
    Loads from file if available, otherwise returns defaults.
    """
    return load_config(config_path)

def main():
    """Main entry point for testing configuration management."""
    print("Testing configuration management...")

    # Test default config
    default_cfg = create_default_config()
    print(f"Default config created: {default_cfg.experiment_name}")
    print(f"  Filter discard percent: {default_cfg.filter_discard_percent}")
    print(f"  CPU only: {default_cfg.cpu_only}")
    print(f"  Max memory: {default_cfg.max_memory_gb} GB")

    # Test validation
    errors = validate_config_schema(default_cfg.to_dict())
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("Default config validation passed")

    # Test save/load
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "test_config.yaml"
        save_config(default_cfg, test_path)
        loaded_cfg = load_config(test_path)
        assert loaded_cfg.experiment_name == default_cfg.experiment_name
        assert loaded_cfg.filter_discard_percent == default_cfg.filter_discard_percent
        print(f"Save/load test passed: {test_path}")

    print("Configuration management tests completed successfully.")

if __name__ == "__main__":
    main()
