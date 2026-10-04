"""
Configuration loader module.
"""
import os
import argparse
import json
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables, CLI args, or defaults.
    
    Returns:
        Dictionary with keys: N, primes, memory_limit_mb, seed, memory_check_interval
    """
    # Defaults
    config = {
        "N": int(os.environ.get("TOTIENT_N", "1000000")),
        "primes": json.loads(os.environ.get("TOTIENT_PRIMES", "[3, 5, 7, 11]")),
        "memory_limit_mb": int(os.environ.get("TOTIENT_MEMORY_LIMIT_MB", "6000")),
        "seed": int(os.environ.get("TOTIENT_SEED", "42")),
        "memory_check_interval": int(os.environ.get("TOTIENT_MEMORY_CHECK_INTERVAL", "10000"))
    }
    
    # Override with CLI args if available (handled by parse_cli_args)
    # This function returns the base config
    return config

def create_argument_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI overrides."""
    parser = argparse.ArgumentParser(description="Euler's Totient Residue Distribution Analysis")
    
    parser.add_argument("--N", type=int, help="Upper bound N for totient calculation")
    parser.add_argument("--primes", type=str, help='JSON list of primes, e.g. "[3, 5, 7]"')
    parser.add_argument("--memory-limit-mb", type=int, help="Memory limit in MB")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--memory-check-interval", type=int, help="Interval for memory checks")
    
    return parser

def parse_cli_args(parser: Optional[argparse.ArgumentParser] = None) -> Dict[str, Any]:
    """Parse CLI arguments and merge with config."""
    if parser is None:
        parser = create_argument_parser()
        
    args = parser.parse_args()
    config = load_config()
    
    if args.N is not None:
        config["N"] = args.N
    if args.primes is not None:
        config["primes"] = json.loads(args.primes)
    if args.memory_limit_mb is not None:
        config["memory_limit_mb"] = args.memory_limit_mb
    if args.seed is not None:
        config["seed"] = args.seed
    if args.memory_check_interval is not None:
        config["memory_check_interval"] = args.memory_check_interval
        
    return config

def save_config_to_json(config: Dict[str, Any], path: str) -> None:
    """Save configuration to a JSON file."""
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Config saved to {path}")

def load_config_from_json(path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)