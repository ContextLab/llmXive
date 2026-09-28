"""
Environment Configuration Management for llmXive.

This module centralizes all environment-specific configuration including:
- Random seeds for reproducibility
- Model paths and identifiers
- Resource limits (RAM, disk, time)
- Data paths
- Feature flags

Usage:
    from config import get_config, Config
    cfg = get_config()
    print(cfg.seed)
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from utils.logging import get_logger, log_info, log_error
from utils.errors import fail_loudly

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Default paths relative to project root
DEFAULT_DATA_RAW = "data/raw"
DEFAULT_DATA_PROCESSED = "data/processed"
DEFAULT_RESULTS = "results"
DEFAULT_CHECKSUMS = "data/checksums.json"

# Default model limits
DEFAULT_MAX_RAM_GB = 7.0
DEFAULT_MAX_ITERATIONS = 20
DEFAULT_MIN_VARIANCE = 0.05
DEFAULT_BATCH_SIZE = 1

# Default seeds
DEFAULT_SEED = 42

@dataclass
class Config:
    """Centralized configuration object."""
    # Reproducibility
    seed: int = DEFAULT_SEED
    
    # Paths
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    data_raw: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_DATA_RAW)
    data_processed: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_DATA_PROCESSED)
    results_dir: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_RESULTS)
    checksums_file: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_CHECKSUMS)
    
    # Resource Limits
    max_ram_gb: float = DEFAULT_MAX_RAM_GB
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    min_variance_threshold: float = DEFAULT_MIN_VARIANCE
    batch_size: int = DEFAULT_BATCH_SIZE
    
    # Model Configuration
    model_paths: Dict[str, str] = field(default_factory=dict)
    
    # Feature Flags
    enable_validation: bool = True
    enable_logging_json: bool = True
    strict_mode: bool = True  # Fail loudly on any missing real data
    
    # WBench Specific
    wbench_dataset_id: str = "wbench/wbench"
    wbench_subset_name: Optional[str] = None
    
    # Entropy Specific
    entropy_targets: Dict[str, float] = field(default_factory=lambda: {
        "low": 0.3,
        "medium": 0.5,
        "high": 0.7
    })
    entropy_tolerance: float = 0.05
    
    # Inference Specific
    inference_timeout_seconds: int = 3600
    
    def __post_init__(self):
        """Validate and normalize paths after initialization."""
        self.project_root = Path(self.project_root).resolve()
        self.data_raw = Path(self.data_raw).resolve()
        self.data_processed = Path(self.data_processed).resolve()
        self.results_dir = Path(self.results_dir).resolve()
        self.checksums_file = Path(self.checksums_file).resolve()
        
        # Ensure directories exist (optional, can be handled by T004/T007)
        # We do not create them here to avoid side-effects in config loading,
        # but we ensure the paths are absolute.

    def get_model_path(self, model_name: str) -> str:
        """Retrieve a registered model path or raise error if not found."""
        if model_name in self.model_paths:
            return self.model_paths[model_name]
        # Default to HuggingFace ID if no explicit path is set
        return model_name

    def validate(self) -> None:
        """Perform strict validation of configuration."""
        if self.seed < 0:
            fail_loudly("Seed must be non-negative")
        
        if self.max_ram_gb <= 0:
            fail_loudly("max_ram_gb must be positive")
        
        if self.min_variance_threshold < 0:
            fail_loudly("min_variance_threshold must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary for logging/export."""
        return {
            "seed": self.seed,
            "data_raw": str(self.data_raw),
            "data_processed": str(self.data_processed),
            "results_dir": str(self.results_dir),
            "max_ram_gb": self.max_ram_gb,
            "max_iterations": self.max_iterations,
            "model_paths": self.model_paths,
            "strict_mode": self.strict_mode
        }

# Singleton instance
_config_instance: Optional[Config] = None

def get_config(overrides: Optional[Dict[str, Any]] = None) -> Config:
    """
    Get the singleton configuration instance.
    
    Args:
        overrides: Optional dictionary of key-value pairs to override defaults.
                   Keys must match Config dataclass fields.
    
    Returns:
        Config: The active configuration instance.
    """
    global _config_instance
    if _config_instance is None:
        # Initialize from environment variables if available
        env_overrides = {}
        
        # Check for explicit env vars
        if "LLMXIVE_SEED" in os.environ:
            try:
                env_overrides["seed"] = int(os.environ["LLMXIVE_SEED"])
            except ValueError:
                log_error(f"Invalid LLMXIVE_SEED value: {os.environ['LLMXIVE_SEED']}")
        
        if "LLMXIVE_MAX_RAM_GB" in os.environ:
            try:
                env_overrides["max_ram_gb"] = float(os.environ["LLMXIVE_MAX_RAM_GB"])
            except ValueError:
                log_error(f"Invalid LLMXIVE_MAX_RAM_GB value: {os.environ['LLMXIVE_MAX_RAM_GB']}")
        
        if "LLMXIVE_STRICT_MODE" in os.environ:
            env_overrides["strict_mode"] = os.environ["LLMXIVE_STRICT_MODE"].lower() in ("true", "1", "yes")

        # Merge with passed overrides
        if overrides:
            env_overrides.update(overrides)

        _config_instance = Config(**env_overrides)
        _config_instance.validate()
        log_info(f"Configuration initialized with seed={_config_instance.seed}, strict_mode={_config_instance.strict_mode}")
    
    return _config_instance

def reset_config() -> None:
    """Reset the configuration singleton (useful for testing)."""
    global _config_instance
    _config_instance = None

def load_config_from_file(path: str) -> Config:
    """
    Load configuration from a JSON file.
    
    Args:
        path: Path to the JSON configuration file.
    
    Returns:
        Config: The loaded configuration.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        fail_loudly(f"Configuration file not found: {path}")
    
    try:
        with open(path_obj, "r") as f:
            data = json.load(f)
        
        # Map JSON keys to dataclass fields
        overrides = {}
        for key, value in data.items():
            if hasattr(Config, key):
                overrides[key] = value
            else:
                log_warning(f"Ignoring unknown config key: {key}")
        
        return get_config(overrides)
    except json.JSONDecodeError as e:
        fail_loudly(f"Invalid JSON in config file {path}: {e}")
    except Exception as e:
        fail_loudly(f"Failed to load config from {path}: {e}")

def save_config_to_file(cfg: Config, path: str) -> None:
    """
    Save the current configuration to a JSON file.
    
    Args:
        cfg: The configuration object to save.
        path: Destination path.
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, "w") as f:
        json.dump(cfg.to_dict(), f, indent=2)
    
    log_info(f"Configuration saved to {path}")

# Main entry point for CLI usage
def main() -> None:
    """CLI entry point to print or validate configuration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage llmXive configuration")
    parser.add_argument("--validate", action="store_true", help="Validate current config")
    parser.add_argument("--show", action="store_true", help="Print current config")
    parser.add_argument("--save", type=str, help="Save config to file")
    parser.add_argument("--load", type=str, help="Load config from file")
    
    args = parser.parse_args()
    
    if args.load:
        cfg = load_config_from_file(args.load)
    else:
        cfg = get_config()
    
    if args.validate:
        try:
            cfg.validate()
            print("Configuration is valid.")
        except Exception as e:
            fail_loudly(f"Configuration validation failed: {e}")
    
    if args.show:
        print(json.dumps(cfg.to_dict(), indent=2))
    
    if args.save:
        save_config_to_file(cfg, args.save)

if __name__ == "__main__":
    main()