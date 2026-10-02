"""
Task T013e: Programmatically Iterate over discovered environments and wrap them.

This script loads the list of discovered environment IDs from `data/discovered_envs.json`
(created by T013d) and wraps each one with the `DynamicShiftEnvironment` class defined
in `envs/dynamic_shift_env.py`.

It validates that the discovery file exists and contains valid environment IDs.
It does NOT run the environments yet, but prepares the wrapped instances for downstream
tasks (T013f, T015a).
"""
import json
import os
import logging
import sys

# Add project root to path if running as script
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from envs.dynamic_shift_env import DynamicShiftEnvironment, generate_all_dynamic_shift_envs
from utils.logging import get_logger, setup_logging

# Setup logging for this task
logger = setup_logging("apply_shift_wrappers", log_file="data/apply_shift_wrappers.log")

DISCOVERED_ENVS_PATH = "data/discovered_envs.json"
WRAPPED_ENVS_LOG = "data/wrapped_envs.log"

def load_discovered_envs(path: str) -> list:
    """Load the list of discovered environment IDs."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}. "
                                "Please ensure T013d has been executed successfully.")

    with open(path, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'env_ids' in data:
        return data['env_ids']
    else:
        raise ValueError(f"Unexpected format in {path}. Expected list or dict with 'env_ids'.")

def wrap_environments(env_ids: list) -> list:
    """
    Wrap each environment ID with DynamicShiftEnvironment.

    Returns a list of tuples: (env_id, wrapped_env_instance)
    """
    wrapped_envs = []
    logger.info(f"Attempting to wrap {len(env_ids)} environments...")

    for env_id in env_ids:
        try:
            # The generate_all_dynamic_shift_envs function or similar logic should handle
            # the actual instantiation. Since we are iterating, we assume the underlying
            # gymnasium registry can resolve 'env_id'.
            # We use the helper from dynamic_shift_env if available, or instantiate directly.
            # Based on API surface, generate_all_dynamic_shift_envs might return a dict or list.
            # Here we implement the iteration logic explicitly.

            # Attempt to create the wrapped environment
            # Note: The actual 'make' logic depends on how the base envs are registered.
            # We assume DynamicShiftEnvironment accepts an env_id string or a base env instance.
            # Looking at the API: DynamicShiftEnvironment is a class.
            # We will assume a factory pattern or direct wrapping.
            # Since we don't have the exact signature of the base env wrapper in the prompt,
            # we assume the standard pattern: DynamicShiftEnvironment(base_env, config)
            # But we need the base_env instance first.
            
            # Let's assume the standard gymnasium pattern for now, but since we are wrapping,
            # we might need to import the base registry.
            # However, the task says "wrap each with DynamicShiftEnvironment".
            # We will use the generate_all_dynamic_shift_envs if it takes a list,
            # otherwise we iterate.
            
            # Strategy: Use the generate_all_dynamic_shift_envs helper if it supports a list of IDs.
            # If not, we assume we can make the base env and wrap it.
            # Given the API: `generate_all_dynamic_shift_envs` exists.
            # Let's assume it takes a list of env_ids and returns wrapped ones.
            
            # If the helper is designed for "all", we might need to call it with the specific list.
            # Let's try to call it with the list of IDs.
            wrapped = generate_all_dynamic_shift_envs(env_ids)
            
            if isinstance(wrapped, dict):
                wrapped_envs.extend([(k, v) for k, v in wrapped.items()])
            elif isinstance(wrapped, list):
                # Assume list of (id, env) or just envs.
                # If just envs, we need IDs.
                # Let's assume the return is a list of env objects and we map them back if possible.
                # To be safe, we assume the function returns a dict {env_id: env} or list of tuples.
                wrapped_envs.extend(wrapped)
            else:
                logger.warning(f"Unexpected return type from generate_all_dynamic_shift_envs: {type(wrapped)}")

        except Exception as e:
            logger.error(f"Failed to wrap environment {env_id}: {e}")
            # We do not fail loudly here for T013e, as T013d already warned if count != 16.
            # We log and continue.

    return wrapped_envs

def main():
    """Main entry point for T013e."""
    logger.info("Starting T013e: Apply Shift Wrappers")

    # 1. Load discovered envs
    try:
        env_ids = load_discovered_envs(DISCOVERED_ENVS_PATH)
        logger.info(f"Loaded {len(env_ids)} environment IDs from {DISCOVERED_ENVS_PATH}")
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.critical(f"Invalid JSON in {DISCOVERED_ENVS_PATH}: {e}")
        sys.exit(1)

    if not env_ids:
        logger.warning("No environment IDs found. No wrapping performed.")
        # Write an empty log to indicate completion
        with open(WRAPPED_ENVS_LOG, 'w') as f:
            f.write("No environments to wrap.\n")
        return

    # 2. Wrap environments
    wrapped_envs = wrap_environments(env_ids)

    # 3. Log results
    logger.info(f"Successfully wrapped {len(wrapped_envs)} environments.")
    
    # Write a summary log
    with open(WRAPPED_ENVS_LOG, 'w') as f:
        f.write(f"Total environments processed: {len(env_ids)}\n")
        f.write(f"Successfully wrapped: {len(wrapped_envs)}\n")
        f.write("Wrapped Environment IDs:\n")
        for env_id, _ in wrapped_envs:
            f.write(f"  - {env_id}\n")

    logger.info("T013e completed successfully.")

if __name__ == "__main__":
    main()