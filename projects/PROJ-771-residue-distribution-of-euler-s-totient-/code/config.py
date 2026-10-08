import os
import argparse
import json
import logging
from typing import Dict, Any, List, Optional

def load_config() -> Dict[str, Any]:
    """
    Load configuration with defaults, overridden by CLI args and environment variables.
    Returns a dictionary with keys: N, primes, memory_limit_mb, seed, memory_check_interval.
    """
    defaults = {
        'N': 1000000,
        'primes': [3, 5, 7, 11],
        'memory_limit_mb': 7000,
        'seed': 42,
        'memory_check_interval': 10000
    }

    parser = create_argument_parser()
    args = parser.parse_args()

    config = defaults.copy()
    
    # Override with CLI args if provided
    if args.N is not None:
        config['N'] = args.N
    if args.primes is not None:
        config['primes'] = args.primes
    if args.memory_limit_mb is not None:
        config['memory_limit_mb'] = args.memory_limit_mb
    if args.seed is not None:
        config['seed'] = args.seed
    if args.memory_check_interval is not None:
        config['memory_check_interval'] = args.memory_check_interval

    # Override with environment variables if set
    if os.getenv('LLMXIVE_N'):
        config['N'] = int(os.getenv('LLMXIVE_N'))
    if os.getenv('LLMXIVE_PRIMES'):
        config['primes'] = [int(p) for p in os.getenv('LLMXIVE_PRIMES').split(',')]
    if os.getenv('LLMXIVE_MEMORY_LIMIT_MB'):
        config['memory_limit_mb'] = int(os.getenv('LLMXIVE_MEMORY_LIMIT_MB'))
    if os.getenv('LLMXIVE_SEED'):
        config['seed'] = int(os.getenv('LLMXIVE_SEED'))
    if os.getenv('LLMXIVE_MEMORY_CHECK_INTERVAL'):
        config['memory_check_interval'] = int(os.getenv('LLMXIVE_MEMORY_CHECK_INTERVAL'))

    return config

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Euler Totient Residue Distribution Analysis')
    parser.add_argument('--N', type=int, help='Upper bound for n')
    parser.add_argument('--primes', type=str, help='Comma-separated list of primes')
    parser.add_argument('--memory_limit_mb', type=int, help='Memory limit in MB')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--memory_check_interval', type=int, help='Interval for memory checks')
    return parser

def parse_cli_args() -> argparse.Namespace:
    parser = create_argument_parser()
    return parser.parse_args()

def save_config_to_json(config: Dict[str, Any], path: str) -> None:
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)

def load_config_from_json(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)
