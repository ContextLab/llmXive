import json
import logging
import os
from typing import List, Dict, Any

from utils.logging import get_logger

def discover_environments() -> List[str]:
    """
    Dynamically discover the existing EvoPolicyGym environments.
    
    Returns:
        List[str]: A list of environment IDs registered in evopolicygym.
        
    Raises:
        RuntimeError: If no environments are found (count == 0).
    """
    logger = get_logger(__name__)
    
    try:
        # Import the registry from the installed package
        from evopolicygym.envs import REGISTRY
        
        # Query the keys
        env_ids = list(REGISTRY.keys())
        
        count = len(env_ids)
        logger.info(f"Discovered {count} environments from REGISTRY.")
        
        if count == 0:
            error_msg = "No environments found. Study cannot proceed."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        return env_ids
        
    except ImportError as e:
        logger.error(f"Failed to import evopolicygym REGISTRY: {e}")
        raise RuntimeError(f"Cannot discover environments: {e}")

def write_discovered_envs(env_ids: List[str]) -> None:
    """
    Write the list of discovered environment IDs to data files.
    
    Args:
        env_ids: List of environment IDs.
    """
    logger = get_logger(__name__)
    
    # Ensure data directory exists
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    log_path = os.path.join(data_dir, "discovered_envs.log")
    json_path = os.path.join(data_dir, "discovered_envs.json")
    
    count = len(env_ids)
    expected_count = 16
    
    # Write log file
    with open(log_path, "w") as f:
        f.write(f"Discovered {count} environments.\n")
        if count != expected_count:
            warning_msg = (
                f"Expected {expected_count} (2607.02440, https://arxiv.org/abs/2607.02440) "
                f"environments [UNRESOLVED-CLAIM: c_ccec8d03 — status=verified], found {count}. "
                "Proceeding with available subset."
            )
            logger.warning(warning_msg)
            f.write(warning_msg + "\n")
        f.write("Environment IDs:\n")
        for env_id in env_ids:
            f.write(f"  - {env_id}\n")
    
    # Write JSON file
    with open(json_path, "w") as f:
        json.dump(env_ids, f, indent=2)
    
    logger.info(f"Wrote discovered environments to {log_path} and {json_path}")

def run_discovery() -> List[str]:
    """
    Main entry point to discover environments and write artifacts.
    
    Returns:
        List[str]: The list of discovered environment IDs.
    """
    env_ids = discover_environments()
    write_discovered_envs(env_ids)
    return env_ids
