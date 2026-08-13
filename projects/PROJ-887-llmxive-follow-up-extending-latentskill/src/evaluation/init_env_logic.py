"""
Initialize and verify the ALFWorld environment logic before evaluation.

This module handles the setup of the ALFWorld environment, ensuring that
the environment can be instantiated and that a dry-run task execution
returns a valid success/failure flag.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from src.utils.config import get_project_root, get_data_path, get_artifacts_path, ensure_directories


def verify_alfworld_environment() -> bool:
    """
    Verify that the ALFWorld environment can be imported and initialized.

    Returns:
        bool: True if the environment is available, False otherwise.
    """
    try:
        import alfworld
        from alfworld.agents.environment import alfworld_env

        logger.info("ALFWorld environment package found.")

        # Check for necessary config files
        alfworld_path = Path(alfworld.__file__).parent
        config_path = alfworld_path / "configs"
        if not config_path.exists():
            logger.warning(f"ALFWorld config path not found at {config_path}")
            return False

        logger.info("ALFWorld environment verification successful.")
        return True

    except ImportError as e:
        logger.error(f"ALFWorld package not found. Import error: {e}")
        logger.info("Attempting to install alfworld via pip...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "alfworld"])
            logger.info("ALFWorld installed successfully. Please re-run this script.")
            return False
        except Exception as install_error:
            logger.error(f"Failed to install ALFWorld: {install_error}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error during ALFWorld verification: {e}")
        return False


def run_alfworld_dry_run(task_id: str = "pick_and_place_simple") -> Tuple[bool, str]:
    """
    Run a dry-run task in the ALFWorld environment to verify logic.

    This function instantiates the environment, loads a simple task,
    and attempts a single step or a dummy execution to ensure the
    environment returns a valid success/failure flag.

    Args:
        task_id (str): The specific ALFWorld task ID to test.

    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not verify_alfworld_environment():
        return False, "ALFWorld environment verification failed."

    try:
        import alfworld
        from alfworld.agents.environment import alfworld_env
        from alfworld.agents.modules.generic import load_config

        logger.info(f"Initializing ALFWorld dry-run for task: {task_id}")

        # Load configuration
        # Note: In a real scenario, we might need to pass specific config paths
        # depending on the ALFWorld version.
        config = load_config()
        config["env"] = {
            "name": "alfworld",
            "task_type": task_id,
            "domain": "pick_and_place", # Simplified for dry run
        }
        config["general"] = {
            "eval": {"mode": "train"}, # Use train mode for dry run to ensure data exists
        }

        # Initialize environment
        # We use a small split for the dry run
        env = alfworld_env.ALFWorldEnv(config)
        env.init_game()

        logger.info("ALFWorld environment initialized successfully.")

        # Perform a dummy step to verify observation and reward logic
        # In ALFWorld, we typically need to provide an action.
        # For a dry run, we'll try a standard "look" or "go" command if possible,
        # or just check the initial state.
        initial_observation = env.reset()
        logger.info(f"Initial observation received: {str(initial_observation)[:100]}...")

        # Attempt a dummy action to trigger the environment logic
        # A common safe action in many ALFWorld tasks is 'look' or 'inventory'
        dummy_action = "look"
        observation, reward, done, info = env.step(dummy_action)

        logger.info(f"Dry-run action '{dummy_action}' executed.")
        logger.info(f"Reward: {reward}, Done: {done}")

        # Check if the environment returned a valid state
        if isinstance(reward, (int, float)):
            logger.info("Dry-run successful: Environment returned valid reward.")
            return True, f"Dry-run passed. Reward: {reward}, Done: {done}"
        else:
            return False, f"Dry-run failed: Unexpected reward type {type(reward)}"

    except Exception as e:
        logger.error(f"Dry-run execution failed: {e}", exc_info=True)
        return False, f"Dry-run failed with error: {e}"


def main():
    """
    Main entry point for T025a: Initialize and verify ALFWorld environment.
    """
    logger.info("Starting ALFWorld Environment Verification (T025a)...")

    # Ensure directories exist
    ensure_directories()

    # 1. Verify environment availability
    env_available = verify_alfworld_environment()
    if not env_available:
        logger.error("ALFWorld environment is not available. Cannot proceed.")
        # We do not fail loudly here if the task is just to check,
        # but the task requires running a dry-run. If env is missing, dry-run fails.
        # However, the task says "Run a dry-run task to ensure...".
        # If we can't run it, we report the status.
        return 1

    # 2. Run dry-run
    # We try a few common task IDs if the default one fails
    task_ids = ["pick_and_place_simple", "pick_heat_and_place", "cook_and_place"]
    success = False
    message = ""

    for tid in task_ids:
        logger.info(f"Attempting dry-run with task ID: {tid}")
        success, message = run_alfworld_dry_run(tid)
        if success:
            break

    if success:
        logger.info("ALFWorld Environment Verification PASSED.")
        logger.info(f"Result: {message}")
        return 0
    else:
        logger.error("ALFWorld Environment Verification FAILED.")
        logger.error(f"Result: {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
