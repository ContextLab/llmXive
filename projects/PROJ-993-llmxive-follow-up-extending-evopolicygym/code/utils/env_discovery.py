import json
import logging
import os
from typing import List, Dict, Any

# Import the registry from the installed package
try:
    from evopolicygym.envs import REGISTRY
except ImportError:
    # Fallback import path if the package structure differs slightly
    try:
        from evopolicygym.envs.registry import REGISTRY
    except ImportError:
        raise ImportError(
            "Failed to import REGISTRY from evopolicygym.envs. "
            "Ensure 'evopolicygym' is installed and accessible."
        )

from utils.logging import get_logger

logger = get_logger(__name__)

def discover_environments() -> List[str]:
    """
    Dynamically discover the existing EvoPolicyGym environments.

    Logic:
    1. Import REGISTRY.
    2. Query REGISTRY.keys().
    3. If count is 0, raise RuntimeError.
    4. If count != 16, log warning and return available IDs.

    Returns:
        List[str]: List of discovered environment IDs.

    Raises:
        RuntimeError: If no environments are found.
    """
    env_ids = list(REGISTRY.keys())
    count = len(env_ids)

    if count == 0:
        logger.error("No environments found in REGISTRY.")
        raise RuntimeError("No environments found. Study cannot proceed.")

    if count != 16:
        logger.warning(
            f"Expected 16 environments, found {count}. "
            "Proceeding with available subset."
        )

    logger.info(f"Discovered {count} environments: {env_ids}")
    return env_ids

def write_discovered_envs(env_ids: List[str], output_dir: str = "data") -> str:
    """
    Write the list of discovered environment IDs to JSON and log files.

    Args:
        env_ids: List of environment IDs.
        output_dir: Directory to write output files.

    Returns:
        str: Path to the written JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "discovered_envs.json")
    log_path = os.path.join(output_dir, "discovered_envs.log")

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(env_ids, f, indent=2)

    # Write Log
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Discovered {len(env_ids)} environments:\n")
        for env_id in env_ids:
            f.write(f"- {env_id}\n")

    logger.info(f"Wrote discovered environments to {json_path} and {log_path}")
    return json_path

def run_discovery() -> List[str]:
    """
    Main entry point to discover and persist environment list.

    Returns:
        List[str]: The list of discovered environment IDs.
    """
    env_ids = discover_environments()
    write_discovered_envs(env_ids)
    return env_ids

if __name__ == "__main__":
    run_discovery()
