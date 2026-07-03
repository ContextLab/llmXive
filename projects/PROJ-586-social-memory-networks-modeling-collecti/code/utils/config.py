"""
Environment management configuration.

This module handles loading and saving of configuration from a YAML file,
ensuring that default values (seed=42, device=cpu) are applied when the
file is missing or incomplete. It also ensures the config.yaml file exists
on disk with the required defaults.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

# Try to import yaml, but handle missing dependency gracefully
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


@dataclass
class Config:
    """Global experiment configuration."""
    seed: int = 42
    device: str = "cpu"
    model_name: str = "facebook/opt-125m"
    dtype: str = "float32"
    log_file: str = "experiment.log"
    output_dir: str = "results"
    data_dir: str = "data"
    num_games_full: int = 1000
    num_games_limited: int = 1000
    agent_counts: list = field(default_factory=lambda: [3, 5, 7])
    context_windows: list = field(default_factory=lambda: [128, 256, 512])


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a YAML file.

    If the file does not exist, returns the default configuration.
    Missing keys in the file are filled with defaults.

    Parameters
    ----------
    config_path : str, optional
        Path to the configuration file. Defaults to 'config.yaml' in the
        project root.

    Returns
    -------
    Config
        The loaded configuration object.
    """
    if config_path is None:
        config_path = "config.yaml"

    config_path = Path(config_path)
    defaults = asdict(Config())

    if config_path.exists():
        if yaml is not None:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}
        else:
            # Fallback parser for simple YAML
            file_config = {}
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key = key.strip()
                        val = val.strip()
                        # Basic type conversion
                        if val.isdigit():
                            file_config[key] = int(val)
                        elif val.replace('.', '', 1).replace('-', '', 1).replace('e', '').replace('+', '').replace('-', '').isdigit():
                            try:
                                file_config[key] = float(val)
                            except ValueError:
                                file_config[key] = val
                        elif val.lower() in ('true', 'false'):
                            file_config[key] = val.lower() == 'true'
                        elif val.startswith('[') and val.endswith(']'):
                            # Simple list parsing
                            items = val[1:-1].split(',')
                            file_config[key] = [item.strip() for item in items if item.strip()]
                        else:
                            file_config[key] = val

        # Merge with defaults
        merged = {**defaults, **file_config}
    else:
        merged = defaults

    return Config(**merged)


def save_config(config: Config, config_path: Optional[str] = None) -> None:
    """
    Save configuration to a YAML file.

    Parameters
    ----------
    config : Config
        The configuration object to save.
    config_path : str, optional
        Path to the configuration file. Defaults to 'config.yaml' in the
        project root.
    """
    if config_path is None:
        config_path = "config.yaml"

    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if yaml is not None:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(asdict(config), f, default_flow_style=False)
    else:
        # Fallback: simple key-value writing
        with open(config_path, "w", encoding="utf-8") as f:
            for key, val in asdict(config).items():
                if isinstance(val, list):
                    val_str = "[" + ", ".join(str(v) for v in val) + "]"
                elif isinstance(val, bool):
                    val_str = "true" if val else "false"
                else:
                    val_str = str(val)
                f.write(f"{key}: {val_str}\n")


def ensure_config_file() -> Path:
    """
    Ensure that a config.yaml file exists with the required defaults (seed=42, device=cpu).
    If the file does not exist, it creates it with the default configuration.

    Returns
    -------
    Path
        The path to the configuration file.
    """
    config_path = Path("config.yaml")
    if not config_path.exists():
        default_config = Config()
        save_config(default_config, str(config_path))
    return config_path


def get_config() -> Config:
    """
    Get the global configuration, ensuring the config file exists on disk first.

    Returns
    -------
    Config
        The global configuration object.
    """
    ensure_config_file()
    return load_config()


def main() -> None:
    """
    CLI entry point to ensure config.yaml exists and print its contents.
    This script writes the real config.yaml file to disk if missing.
    """
    config_path = ensure_config_file()
    config = load_config(str(config_path))

    print(f"Configuration loaded from: {config_path}")
    print(f"Seed: {config.seed}")
    print(f"Device: {config.device}")
    print(f"Model: {config.model_name}")
    print(f"Agent counts: {config.agent_counts}")
    print(f"Config file verified on disk: {config_path.exists()}")


if __name__ == "__main__":
    main()