"""
Configuration loader for the Residue Distribution of Euler's Totient Function project.

This module provides a centralized configuration system that supports:
- Default values defined in code
- Override via environment variables
- Override via command-line arguments

All configuration keys match the specification requirements exactly.
"""

import os
import argparse
import json
from typing import Dict, Any, List, Optional


# Default configuration values as specified in T005
DEFAULTS: Dict[str, Any] = {
    'N': 1000000,
    'primes': [3, 5, 7, 11],
    'memory_limit_mb': 6000,
    'seed': 42,
    'memory_check_interval': 10000,
}

# Environment variable mapping (prefix: CONFIG_)
ENV_MAPPING: Dict[str, str] = {
    'N': 'CONFIG_N',
    'primes': 'CONFIG_PRIMES',
    'memory_limit_mb': 'CONFIG_MEMORY_LIMIT_MB',
    'seed': 'CONFIG_SEED',
    'memory_check_interval': 'CONFIG_MEMORY_CHECK_INTERVAL',
}


def _parse_primes_env(env_value: str) -> List[int]:
    """
    Parse primes from environment variable string.
    Expected format: comma-separated integers, e.g., "3,5,7,11"
    """
    try:
        return [int(x.strip()) for x in env_value.split(',') if x.strip()]
    except ValueError:
        raise ValueError(
            f"Invalid primes format in environment variable: '{env_value}'. "
            "Expected comma-separated integers (e.g., '3,5,7,11')."
        )


def _parse_int_env(env_value: str, key: str) -> int:
    """
    Parse integer from environment variable with validation.
    """
    try:
        value = int(env_value)
        if value <= 0:
            raise ValueError(f"Value for {key} must be positive, got: {value}")
        return value
    except ValueError as e:
        raise ValueError(f"Invalid integer for {key}: '{env_value}'. Error: {e}")


def load_config(cli_args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Load configuration with the following precedence (lowest to highest):
    1. Default values defined in code
    2. Environment variables (CONFIG_* prefix)
    3. Command-line arguments (if provided)

    Returns a dictionary with exact keys:
    - N (int): Upper bound for totient computation
    - primes (list of int): List of primes for residue analysis
    - memory_limit_mb (int): Memory limit in megabytes
    - seed (int): Random seed for reproducibility
    - memory_check_interval (int): Iteration interval for memory checks

    Args:
        cli_args: Optional parsed argparse namespace. If None, CLI args are ignored.

    Returns:
        Dict[str, Any]: Complete configuration dictionary

    Raises:
        ValueError: If environment variables or CLI args contain invalid values
    """
    config = DEFAULTS.copy()

    # Override with environment variables
    for key, env_var in ENV_MAPPING.items():
        env_value = os.environ.get(env_var)
        if env_value is not None:
            if key == 'primes':
                config[key] = _parse_primes_env(env_value)
            else:
                config[key] = _parse_int_env(env_value, key)

    # Override with CLI arguments if provided
    if cli_args is not None:
        cli_dict = vars(cli_args)
        for key in config.keys():
            if key in cli_dict and cli_dict[key] is not None:
                config[key] = cli_dict[key]

    # Final validation
    _validate_config(config)

    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values for correctness.

    Raises:
        ValueError: If any configuration value is invalid
    """
    if not isinstance(config['N'], int) or config['N'] <= 0:
        raise ValueError(f"N must be a positive integer, got: {config['N']}")

    if not isinstance(config['primes'], list) or len(config['primes']) == 0:
        raise ValueError(f"primes must be a non-empty list, got: {config['primes']}")

    for p in config['primes']:
        if not isinstance(p, int) or p < 2:
            raise ValueError(f"All primes must be integers >= 2, got: {p}")

    if not isinstance(config['memory_limit_mb'], int) or config['memory_limit_mb'] <= 0:
        raise ValueError(f"memory_limit_mb must be a positive integer, got: {config['memory_limit_mb']}")

    if not isinstance(config['seed'], int):
        raise ValueError(f"seed must be an integer, got: {config['seed']}")

    if not isinstance(config['memory_check_interval'], int) or config['memory_check_interval'] <= 0:
        raise ValueError(f"memory_check_interval must be a positive integer, got: {config['memory_check_interval']}")


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create an argument parser with all configuration options as CLI arguments.

    Returns:
        argparse.ArgumentParser: Configured parser instance
    """
    parser = argparse.ArgumentParser(
        description='Residue Distribution of Euler\'s Totient Function Analysis',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--N',
        type=int,
        default=None,
        help='Upper bound for totient computation (n ∈ [1, N])'
    )

    parser.add_argument(
        '--primes',
        type=str,
        default=None,
        help='Comma-separated list of primes for residue analysis (e.g., "3,5,7,11")'
    )

    parser.add_argument(
        '--memory_limit_mb',
        type=int,
        default=None,
        help='Memory limit in megabytes'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )

    parser.add_argument(
        '--memory_check_interval',
        type=int,
        default=None,
        help='Iteration interval for memory checks'
    )

    return parser


def parse_cli_args() -> argparse.Namespace:
    """
    Parse command-line arguments and return a namespace.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = create_argument_parser()
    return parser.parse_args()


def save_config_to_json(config: Dict[str, Any], filepath: str) -> None:
    """
    Save configuration to a JSON file for reproducibility.

    Args:
        config: Configuration dictionary
        filepath: Path to output JSON file
    """
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)


def load_config_from_json(filepath: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        filepath: Path to input JSON file

    Returns:
        Dict[str, Any]: Configuration dictionary

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(filepath, 'r') as f:
        config = json.load(f)
    _validate_config(config)
    return config


if __name__ == '__main__':
    # Example usage: print current configuration
    args = parse_cli_args()
    config = load_config(args)
    print(json.dumps(config, indent=2))