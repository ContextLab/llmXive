"""
Environment configuration management for the Memory Load-Adaptive Text project.

Handles data paths, random seeds, CLI thresholds, and other hyperparameters.
Supports loading from environment variables and a local config file.
"""

import os
import json
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field, asdict

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default Paths
DEFAULT_DATA_RAW = PROJECT_ROOT / "data" / "raw"
DEFAULT_DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
DEFAULT_DATA_METADATA = PROJECT_ROOT / "data" / "metadata.yaml"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_LOGS_DIR = PROJECT_ROOT / "logs"

# Default Hyperparameters
DEFAULT_RANDOM_SEED = 42
DEFAULT_CLI_THRESHOLD_SD = 0.5  # Standard deviations for high-load window identification
DEFAULT_OUTLIER_THRESHOLD_SD = 3.0  # Standard deviations for outlier exclusion
DEFAULT_LUMINANCE_NORMALIZATION_METHOD = "zscore"
DEFAULT_LOW_PASS_CUTOFF_HZ = 4.0
DEFAULT_BLINK_THRESHOLD_MS = 100  # Minimum duration to consider a blink

@dataclass
class Config:
    """
    Central configuration object holding all project settings.
    """
    # Paths
    data_raw: Path = field(default_factory=lambda: DEFAULT_DATA_RAW)
    data_derived: Path = field(default_factory=lambda: DEFAULT_DATA_DERIVED)
    data_metadata: Path = field(default_factory=lambda: DEFAULT_DATA_METADATA)
    results_dir: Path = field(default_factory=lambda: DEFAULT_RESULTS_DIR)
    logs_dir: Path = field(default_factory=lambda: DEFAULT_LOGS_DIR)

    # Randomness
    random_seed: int = DEFAULT_RANDOM_SEED

    # CLI & Thresholds
    cli_threshold_sd: float = DEFAULT_CLI_THRESHOLD_SD
    outlier_threshold_sd: float = DEFAULT_OUTLIER_THRESHOLD_SD

    # Preprocessing
    luminance_normalization_method: str = DEFAULT_LUMINANCE_NORMALIZATION_METHOD
    low_pass_cutoff_hz: float = DEFAULT_LOW_PASS_CUTOFF_HZ
    blink_threshold_ms: int = DEFAULT_BLINK_THRESHOLD_MS

    # Dataset Specifics
    openneuro_dataset_id: str = "ds004041"
    dataset_version: str = "1.0.0" # Default, often overridden by metadata.yaml

    def __post_init__(self):
        # Ensure paths are Path objects if they were passed as strings
        self.data_raw = Path(self.data_raw)
        self.data_derived = Path(self.data_derived)
        self.data_metadata = Path(self.data_metadata)
        self.results_dir = Path(self.results_dir)
        self.logs_dir = Path(self.logs_dir)

        # Ensure directories exist
        self.data_raw.mkdir(parents=True, exist_ok=True)
        self.data_derived.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        if not self.logs_dir.exists():
            self.logs_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary for logging or serialization."""
        # Convert Path objects to strings for JSON compatibility
        d = asdict(self)
        for k, v in d.items():
            if isinstance(v, Path):
                d[k] = str(v)
        return d

    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """Save the current configuration to a JSON file."""
        if path is None:
            path = self.data_derived / "config_snapshot.json"
        else:
            path = Path(path)
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load(cls, path: Optional[Union[str, Path]] = None) -> 'Config':
        """Load configuration from a JSON file, overriding defaults."""
        if path is None:
            path = cls().data_derived / "config_snapshot.json"
        else:
            path = Path(path)
        
        if not path.exists():
            return cls() # Return default config if file doesn't exist

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Map string paths back to Path objects
        for key in ['data_raw', 'data_derived', 'data_metadata', 'results_dir', 'logs_dir']:
            if key in data and isinstance(data[key], str):
                data[key] = Path(data[key])
        
        return cls(**data)

def get_config() -> Config:
    """
    Factory function to initialize the global configuration.
    Prioritizes: 1. Environment Variables -> 2. Local Config File -> 3. Defaults.
    """
    config = Config()

    # Override from Environment Variables if present
    if os.getenv("PROJECT_DATA_RAW"):
        config.data_raw = Path(os.getenv("PROJECT_DATA_RAW"))
    if os.getenv("PROJECT_DATA_DERIVED"):
        config.data_derived = Path(os.getenv("PROJECT_DATA_DERIVED"))
    if os.getenv("PROJECT_RANDOM_SEED"):
        try:
            config.random_seed = int(os.getenv("PROJECT_RANDOM_SEED"))
        except ValueError:
            pass # Ignore invalid seed env var
    if os.getenv("PROJECT_CLI_THRESHOLD_SD"):
        try:
            config.cli_threshold_sd = float(os.getenv("PROJECT_CLI_THRESHOLD_SD"))
        except ValueError:
            pass
    if os.getenv("PROJECT_DATASET_ID"):
        config.openneuro_dataset_id = os.getenv("PROJECT_DATASET_ID")

    # Try to load from local file if it exists
    local_config_path = config.data_derived / "config_snapshot.json"
    if local_config_path.exists():
        loaded_config = Config.load(local_config_path)
        # Merge loaded config with env overrides (env takes precedence if set above)
        # Since we already applied env vars to the base config, we just use the base if env wasn't set,
        # or we could do a deep merge. For simplicity, if env vars were set, they override.
        # If no env vars were set for a specific key, use the loaded value.
        
        # Re-apply env logic specifically for the loaded config to ensure precedence
        # Actually, simpler: Start with loaded, then override with env.
        config = loaded_config
        if os.getenv("PROJECT_DATA_RAW"):
            config.data_raw = Path(os.getenv("PROJECT_DATA_RAW"))
        if os.getenv("PROJECT_DATA_DERIVED"):
            config.data_derived = Path(os.getenv("PROJECT_DATA_DERIVED"))
        if os.getenv("PROJECT_RANDOM_SEED"):
            try:
                config.random_seed = int(os.getenv("PROJECT_RANDOM_SEED"))
            except ValueError:
                pass
        if os.getenv("PROJECT_CLI_THRESHOLD_SD"):
            try:
                config.cli_threshold_sd = float(os.getenv("PROJECT_CLI_THRESHOLD_SD"))
            except ValueError:
                pass
        if os.getenv("PROJECT_DATASET_ID"):
            config.openneuro_dataset_id = os.getenv("PROJECT_DATASET_ID")

    return config

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and torch (if available).
    Uses the seed from the global config if not explicitly provided.
    """
    if seed is None:
        config = get_config()
        seed = config.random_seed
    
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# Global config instance (lazy initialization)
_global_config: Optional[Config] = None

def get_global_config() -> Config:
    """Returns the singleton global config instance."""
    global _global_config
    if _global_config is None:
        _global_config = get_config()
    return _global_config

def reset_config() -> None:
    """Resets the global config instance, forcing re-initialization."""
    global _global_config
    _global_config = None

# CLI Thresholds (convenience accessors)
def get_cli_threshold() -> float:
    """Returns the CLI threshold in standard deviations."""
    return get_global_config().cli_threshold_sd

def get_outlier_threshold() -> float:
    """Returns the outlier threshold in standard deviations."""
    return get_global_config().outlier_threshold_sd

# Main entry point for CLI usage
def main():
    """
    CLI entry point to display or manage configuration.
    Usage:
      python code/config.py show       # Print current config
      python code/config.py save       # Save current config to disk
      python code/config.py reset_seed # Reset random seed to default
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code/config.py [show|save|reset_seed]")
        sys.exit(1)

    command = sys.argv[1].lower()
    cfg = get_global_config()

    if command == "show":
        print(json.dumps(cfg.to_dict(), indent=2))
    elif command == "save":
        cfg.save()
        print(f"Configuration saved to {cfg.data_derived / 'config_snapshot.json'}")
    elif command == "reset_seed":
        cfg.random_seed = DEFAULT_RANDOM_SEED
        cfg.save()
        print(f"Random seed reset to {DEFAULT_RANDOM_SEED} and saved.")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()