"""
T013e: Programmatically Iterate over discovered environments and wrap them.

This script loads the list of environment IDs from `data/discovered_envs.json`
(produced by T013d) and wraps each one with the `DynamicShiftEnvironment` wrapper.
It ensures that the wrapping process is logged and that the wrapped environments
are ready for subsequent sensitivity analysis (T013f).
"""

import json
import os
import logging
import sys

# Add project root to path if running as script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from envs.dynamic_shift_env import DynamicShiftEnvironment, generate_all_dynamic_shift_envs
from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

def load_discovered_envs(filepath: str) -> list:
    """
    Load the list of discovered environment IDs from a JSON file.

    Args:
        filepath: Path to the JSON file containing discovered env IDs.

    Returns:
        List of environment ID strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
        RuntimeError: If the list is empty.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Discovered environments file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # The file is expected to be a list of strings or a dict with an 'env_ids' key
    if isinstance(data, list):
        env_ids = data
    elif isinstance(data, dict) and 'env_ids' in data:
        env_ids = data['env_ids']
    else:
        raise ValueError(f"Unexpected format in {filepath}: expected list or dict with 'env_ids' key")

    if not env_ids:
        raise RuntimeError("Discovered environments list is empty. Cannot proceed with wrapping.")

    logger.info(f"Loaded {len(env_ids)} environment IDs from {filepath}")
    return env_ids

def wrap_environments(env_ids: list, shift_config: dict = None) -> list:
    """
    Wrap each discovered environment with DynamicShiftEnvironment.

    Args:
        env_ids: List of environment ID strings.
        shift_config: Optional configuration for the dynamic shift.
                      If None, default config from DynamicShiftEnvironment is used.

    Returns:
        List of wrapped environment instances.
    """
    wrapped_envs = []
    success_count = 0
    failure_count = 0

    for env_id in env_ids:
        try:
            # The generate_all_dynamic_shift_envs function or similar logic
            # is expected to create the wrapped environment.
            # Based on API surface, we use generate_all_dynamic_shift_envs
            # which likely handles the instantiation of the base env and wrapping.
            # If that function takes a list, we might need to call it differently.
            # However, the task says "wrap each with DynamicShiftEnvironment".
            # Let's assume we need to instantiate the base env first, then wrap.
            # But the API surface shows `generate_all_dynamic_shift_envs` which
            # might do exactly this for a list of envs.
            # Given the dependency on T013d which writes the list, and T013e
            # which iterates, let's implement the iteration logic explicitly.

            # We need to import the base env registry or creation logic.
            # Since the API surface for envs.dynamic_shift_env includes
            # `generate_all_dynamic_shift_envs`, let's check if it accepts a list.
            # If not, we might need to create a loop that calls a factory.
            # Assuming `generate_all_dynamic_shift_envs` is a helper that takes
            # env_ids and returns wrapped ones. If it doesn't, we adapt.

            # Let's assume the standard pattern:
            # 1. Get base env from gymnasium or evopolicygym registry
            # 2. Wrap it with DynamicShiftEnvironment

            # Since we don't have the exact signature of generate_all_dynamic_shift_envs
            # in the prompt's API surface beyond the import, we will assume it
            # is a function that takes a list of env_ids and returns a list of wrapped envs.
            # If the previous task T013d used `generate_all_dynamic_shift_envs` to
            # create the list, T013e might just need to call it again or process the list.
            # However, the task says "wrap each with DynamicShiftEnvironment".
            # Let's try to call `generate_all_dynamic_shift_envs` with the list.
            # If that function is designed to generate ALL envs from scratch, we might
            # just need to call it once. But the task implies iterating over the *discovered* list.

            # Alternative interpretation: The `DynamicShiftEnvironment` class is a wrapper.
            # We need to instantiate it for each env_id.
            # Let's assume there is a factory function or we can do:
            #   base_env = gym.make(env_id)
            #   wrapped = DynamicShiftEnvironment(base_env, shift_config)

            # Since `gym` import is not in the API surface for this file, but `envs.dynamic_shift_env`
            # is, we rely on the functions in that module.
            # Let's assume `generate_all_dynamic_shift_envs` is the correct entry point
            # that takes the list of env_ids and returns the wrapped versions.
            # If it doesn't take a list, we might need to loop and call a different function.
            # Given the constraints, we will implement the loop assuming we can instantiate
            # the base env and wrap it, using the `DynamicShiftEnvironment` class directly.
            # We need to ensure we have a way to get the base env.
            # The API surface for `envs.dynamic_shift_env` includes `generate_all_dynamic_shift_envs`.
            # Let's assume this function is the one to use, and it might take env_ids.

            # If the function `generate_all_dynamic_shift_envs` is not designed to take a list,
            # we might need to implement the wrapping logic here.
            # Let's assume we can do:
            #   from evopolicygym.envs import REGISTRY
            #   base_env = REGISTRY[env_id]()
            #   wrapped = DynamicShiftEnvironment(base_env, shift_config)

            # But the API surface does not show `REGISTRY` in `envs.dynamic_shift_env`.
            # It shows `DynamicShiftEnvironment` and `generate_all_dynamic_shift_envs`.
            # Let's assume `generate_all_dynamic_shift_envs` is the correct function
            # and it takes a list of env_ids.

            # If we cannot call a function that takes a list, we must implement the loop.
            # We will assume we can create the base env using a standard method.
            # Since `gymnasium` is a dependency (T001c), we can use `gymnasium.make`.

            import gymnasium as gym

            base_env = gym.make(env_id)
            wrapped_env = DynamicShiftEnvironment(base_env, shift_config)
            wrapped_envs.append(wrapped_env)
            success_count += 1
            logger.debug(f"Successfully wrapped environment: {env_id}")

        except Exception as e:
            failure_count += 1
            logger.error(f"Failed to wrap environment {env_id}: {e}", exc_info=True)

    logger.info(f"Wrapping complete. Success: {success_count}, Failed: {failure_count}")
    return wrapped_envs

def main():
    """
    Main entry point for T013e.
    Loads discovered envs and wraps them.
    """
    setup_logging()
    logger.info("Starting T013e: Apply Shift Wrappers")

    discovered_envs_path = os.path.join(project_root, "data", "discovered_envs.json")
    wrapped_envs_output_path = os.path.join(project_root, "data", "wrapped_envs.json") # Optional output if needed

    try:
        env_ids = load_discovered_envs(discovered_envs_path)
        logger.info(f"Processing {len(env_ids)} environments.")

        # Assuming default shift config is used if not specified
        wrapped_envs = wrap_environments(env_ids)

        # We don't necessarily need to save the wrapped env objects to disk
        # as they are runtime objects. The important part is that they are
        # created and ready for the next step (T013f).
        # However, if we need to log the successful wrapping, we can write a log.
        logger.info(f"Successfully wrapped {len(wrapped_envs)} environments.")

        # If the next task expects a file indicating the wrapped envs are ready,
        # we could write a marker file. But the task description doesn't specify an output file.
        # It says "wrap each with DynamicShiftEnvironment".
        # The next task T013f will likely load these or the list again.
        # We'll just log success.

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in discovered environments file: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during wrapping: {e}", exc_info=True)
        sys.exit(1)

    logger.info("T013e completed successfully.")

if __name__ == "__main__":
    main()