"""
Configuration management for the project.
Implements T004a, T004b: Constants for seeding, generation counts, and exposure calculation.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import random
import hashlib

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

# Constants for T004a
VALIDITY_THRESHOLD = 0.95  # High confidence level for validity checks
RULE_EVALUATION_BUDGET = 10000  # Total rule evaluations allowed
RULES_PER_GENERATION = 100  # Number of rules to evaluate per generation
TRAIN_SEED_START = 0
TEST_SEED_START = 10000  # Disjoint seed range for test instances

class Config:
    """Configuration manager."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
        # Apply defaults
        self._apply_defaults()

    def _apply_defaults(self):
        """Apply default configuration values."""
        defaults = {
            "seeds": {
                "train_start": TRAIN_SEED_START,
                "test_start": TEST_SEED_START
            },
            "generation": {
                "validity_threshold": VALIDITY_THRESHOLD,
                "rule_evaluation_budget": RULE_EVALUATION_BUDGET,
                "rules_per_generation": RULES_PER_GENERATION
            },
            "paths": {
                "generated_proofs": "data/generated_proofs.json",
                "generated_grids": "data/generated_grids.json",
                "test_instances": "data/test_instances.json",
                "checksums": "data/checksums.json",
                "validation_report": "data/validation_report.json",
                "batch_config": "data/batch_config.json",
                "results_dir": "data/results/"
            }
        }
        self._config = _deep_merge(defaults, self._config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by dot-notation key."""
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def calculate_total_exposure(self, num_generations: int) -> int:
        """
        Calculate total target exposure based on generations.
        Implements T004b.

        Args:
            num_generations: Number of generations.

        Returns:
            Total target exposure (integer).
        """
        return RULES_PER_GENERATION * num_generations

def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def get_default_config() -> Dict[str, Any]:
    """Get the default configuration dictionary."""
    return Config().get._config if hasattr(Config().get, '_config') else Config()._config

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    config_dict = {}
    # Example: LLMXIVE_CONFIG_PATH=/path/to/config.json
    config_path = os.environ.get('LLMXIVE_CONFIG_PATH')
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
    return Config(config_dict)

def load_config() -> Config:
    """Load configuration (environment or defaults)."""
    return load_config_from_env()

def save_config(config: Config, path: str) -> None:
    """Save configuration to a JSON file."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, 'w') as f:
        json.dump(config._config, f, indent=2)

def main():
    """CLI entry point for config operations."""
    import argparse
    parser = argparse.ArgumentParser(description="Manage configuration")
    parser.add_argument('--show', action='store_true', help='Show current config')
    parser.add_argument('--save', type=str, help='Save config to file')
    args = parser.parse_args()

    config = load_config()
    if args.show:
        print(json.dumps(config._config, indent=2))
    if args.save:
        save_config(config, args.save)
        print(f"Config saved to {args.save}")

if __name__ == "__main__":
    main()
