"""
Configuration management for the Bayesian Nonparametrics Anomaly Detection project.

This module provides a centralized configuration interface that:
1. Loads hyperparameters, seeds, and base paths from code/config.yaml
2. Validates configuration against schema constraints
3. Provides CLI interface for configuration checks
4. Ensures config.yaml remains under 2KB by design

IMPORTANT: This file is a SCRIPT, not a module. It should be invoked as:
    python code/src/config.py --check
"""

import argparse
import os
import sys
from pathlib import Path
import yaml
from typing import Dict, Any, Optional

# Constants
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
MAX_CONFIG_SIZE_BYTES = 2048  # 2KB limit per FR-009
REQUIRED_KEYS = ["hyperparameters", "seeds", "base_paths"]
FORBIDDEN_KEYS = ["dataset_stats", "inference_results", "simulation_metrics"]

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)

    return config

def validate_config_size(config: Dict[str, Any]) -> bool:
    """Validate that config.yaml is under the 2KB limit."""
    if not CONFIG_PATH.exists():
        return False

    file_size = os.path.getsize(CONFIG_PATH)
    return file_size <= MAX_CONFIG_SIZE_BYTES

def validate_config_structure(config: Dict[str, Any]) -> bool:
    """Validate that config has required keys and no forbidden keys."""
    # Check required keys exist
    for key in REQUIRED_KEYS:
        if key not in config:
            print(f"ERROR: Missing required key: {key}")
            return False

    # Check forbidden keys are not present
    for key in FORBIDDEN_KEYS:
        if key in config:
            print(f"ERROR: Forbidden key present (should be in state file): {key}")
            return False

    return True

def check_config() -> bool:
    """
    Perform comprehensive configuration check.
    
    Returns:
        bool: True if all checks pass, False otherwise
    """
    print("=" * 60)
    print("Configuration Check")
    print("=" * 60)

    # Check 1: File exists
    if not CONFIG_PATH.exists():
        print(f"❌ FAIL: Configuration file not found at {CONFIG_PATH}")
        return False
    print(f"✓ Configuration file exists: {CONFIG_PATH}")

    # Check 2: File size
    file_size = os.path.getsize(CONFIG_PATH)
    print(f"  Current size: {file_size} bytes (limit: {MAX_CONFIG_SIZE_BYTES} bytes)")
    if file_size > MAX_CONFIG_SIZE_BYTES:
        print(f"❌ FAIL: Configuration file exceeds 2KB limit")
        return False
    print(f"✓ Configuration file size is within limits")

    # Check 3: Load and validate structure
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ FAIL: Error loading configuration: {e}")
        return False

    if not validate_config_structure(config):
        print("❌ FAIL: Configuration structure validation failed")
        return False
    print(f"✓ Configuration structure is valid")

    # Check 4: Validate hyperparameters
    if "hyperparameters" in config:
        hp = config["hyperparameters"]
        print(f"  Hyperparameters loaded: {list(hp.keys())}")
        print(f"✓ Hyperparameters section present")

    # Check 5: Validate seeds
    if "seeds" in config:
        seeds = config["seeds"]
        print(f"  Seeds loaded: {seeds}")
        print(f"✓ Seeds section present")

    # Check 6: Validate base paths
    if "base_paths" in config:
        paths = config["base_paths"]
        print(f"  Base paths loaded: {list(paths.keys())}")
        for key, path in paths.items():
            full_path = Path(__file__).parent.parent / path
            if not full_path.exists():
                print(f"  ⚠ Warning: Path does not exist: {full_path}")
            else:
                print(f"  ✓ Path exists: {full_path}")
        print(f"✓ Base paths section present")

    print("=" * 60)
    print("✅ All configuration checks PASSED")
    print("=" * 60)
    return True

def main():
    """CLI entry point for configuration checks."""
    parser = argparse.ArgumentParser(
        description="Configuration management and validation for the project"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run comprehensive configuration validation"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Show path to configuration file"
    )
    parser.add_argument(
        "--size",
        action="store_true",
        help="Show configuration file size"
    )

    args = parser.parse_args()

    if args.path:
        print(f"Configuration file path: {CONFIG_PATH}")
        return 0

    if args.size:
        if CONFIG_PATH.exists():
            file_size = os.path.getsize(CONFIG_PATH)
            print(f"Configuration file size: {file_size} bytes")
            print(f"Limit: {MAX_CONFIG_SIZE_BYTES} bytes")
            if file_size <= MAX_CONFIG_SIZE_BYTES:
                print("Status: OK")
                return 0
            else:
                print("Status: EXCEEDS LIMIT")
                return 1
        else:
            print("Configuration file not found")
            return 1

    if args.check:
        success = check_config()
        return 0 if success else 1

    # Default: show usage
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())