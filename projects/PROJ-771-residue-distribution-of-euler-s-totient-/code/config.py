"""
Configuration loader for the Euler Totient Residue Distribution project.

This module provides utilities to load configuration values from a YAML
file (``code/config.yaml``) and optionally override them with command‑line
arguments or environment variables. The public API matches the original
specification so that existing orchestration code continues to work.
"""

import os
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Import the custom exception for invalid primes.
from code.exceptions import InvalidPrimeError

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Default configuration values (used when a key is missing from the YAML)
# ----------------------------------------------------------------------
_DEFAULTS: Dict[str, Any] = {
    "N": 1_000_000,
    "primes": [3, 5, 7, 11],
    # The test suite expects the default memory limit to be 6000 MB.
    "memory_limit_mb": 6_000,
    "seed": 42,
    "memory_check_interval": 10_000,
}

# ----------------------------------------------------------------------
# Allowed prime moduli
# ----------------------------------------------------------------------
_ALLOWED_PRIMES = {3, 5, 7, 11}

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def load_config(cli_args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Load configuration values.

    The function reads ``code/config.yaml`` (if it exists) and returns a
    dictionary containing at least the keys ``N``, ``primes``,
    ``memory_limit_mb``, ``seed`` and ``memory_check_interval``.  Values
    from the YAML file are merged with the built‑in defaults, then
    optionally overridden by command‑line arguments and finally by
    environment variables.

    Parameters
    ----------
    cli_args :
        Parsed ``argparse.Namespace`` returned by :func:`parse_cli_args`.
        If ``None`` the function behaves as a pure YAML loader.

    Returns
    -------
    dict
        Configuration dictionary ready for consumption by the rest of the
        pipeline.

    Raises
    ------
    InvalidPrimeError
        If any prime in the final ``primes`` list is not one of the
        supported primes {3, 5, 7, 11}.
    """
    # 1️⃣ Load defaults
    config: Dict[str, Any] = _DEFAULTS.copy()

    # 2️⃣ Load YAML file (if present)
    yaml_path = Path(__file__).with_name("config.yaml")
    if yaml_path.is_file():
        try:
            with yaml_path.open("r") as f:
                yaml_cfg = yaml.safe_load(f) or {}
                if not isinstance(yaml_cfg, dict):
                    raise ValueError("YAML config must be a mapping")
                config.update(yaml_cfg)
        except Exception as exc:
            logger.error("Failed to read configuration YAML: %s", exc)
            raise

    # 3️⃣ Override with CLI arguments (if supplied)
    if cli_args is not None:
        if getattr(cli_args, "N", None) is not None:
            config["N"] = cli_args.N
        if getattr(cli_args, "primes", None) is not None:
            # ``primes`` may be a list of ints (from argparse) or a
            # comma‑separated string.
            if isinstance(cli_args.primes, list):
                config["primes"] = [int(p) for p in cli_args.primes]
            elif isinstance(cli_args.primes, str):
                config["primes"] = [int(p) for p in cli_args.primes.split(",")]
        if getattr(cli_args, "memory_limit_mb", None) is not None:
            config["memory_limit_mb"] = cli_args.memory_limit_mb
        if getattr(cli_args, "seed", None) is not None:
            config["seed"] = cli_args.seed
        if getattr(cli_args, "memory_check_interval", None) is not None:
            config["memory_check_interval"] = cli_args.memory_check_interval

    # 4️⃣ Environment variable overrides (highest priority)
    if os.getenv("LLMXIVE_N"):
        config["N"] = int(os.getenv("LLMXIVE_N"))
    if os.getenv("LLMXIVE_PRIMES"):
        config["primes"] = [int(p) for p in os.getenv("LLMXIVE_PRIMES").split(",")]
    if os.getenv("LLMXIVE_MEMORY_LIMIT_MB"):
        config["memory_limit_mb"] = int(os.getenv("LLMXIVE_MEMORY_LIMIT_MB"))
    if os.getenv("LLMXIVE_SEED"):
        config["seed"] = int(os.getenv("LLMXIVE_SEED"))
    if os.getenv("LLMXIVE_MEMORY_CHECK_INTERVAL"):
        config["memory_check_interval"] = int(os.getenv("LLMXIVE_MEMORY_CHECK_INTERVAL"))

    # ------------------------------------------------------------------
    # Validate prime list
    # ------------------------------------------------------------------
    primes = config.get("primes", [])
    # Ensure we have a list of ints
    primes = [int(p) for p in primes]
    config["primes"] = primes
    for p in primes:
        if p not in _ALLOWED_PRIMES:
            # Raise the domain‑specific exception as required by the spec.
            raise InvalidPrimeError(p)

    return config

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create the :class:`argparse.ArgumentParser` used by the CLI.

    The parser defines the same options that the original ``load_config``
    function understood, allowing downstream scripts to continue using the
    familiar ``--N``, ``--primes`` etc.
    """
    parser = argparse.ArgumentParser(
        description="Euler Totient Residue Distribution Analysis"
    )
    parser.add_argument("--N", type=int, help="Upper bound for n")
    parser.add_argument(
        "--primes",
        nargs="+",
        type=int,
        help="List of primes (e.g., 3 5 7 11).",
    )
    parser.add_argument("--memory_limit_mb", type=int, help="Memory limit in MB")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument(
        "--memory_check_interval",
        type=int,
        help="Interval (in iterations) for memory‑limit checks",
    )
    return parser

def parse_cli_args() -> argparse.Namespace:
    """
    Parse command‑line arguments using the parser from
    :func:`create_argument_parser`.

    Returns
    -------
    argparse.Namespace
        Parsed arguments namespace.
    """
    parser = create_argument_parser()
    return parser.parse_args()

def save_config_to_json(config: Dict[str, Any], path: str) -> None:
    """
    Persist a configuration dictionary as a pretty‑printed JSON file.

    Parameters
    ----------
    config :
        Configuration dictionary to write.
    path :
        Destination file path (any string accepted by ``open``).
    """
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

def load_config_from_json(path: str) -> Dict[str, Any]:
    """
    Load a configuration dictionary from a JSON file.

    Parameters
    ----------
    path :
        Path to the JSON file.

    Returns
    -------
    dict
        Configuration dictionary.
    """
    with open(path, "r") as f:
        return json.load(f)