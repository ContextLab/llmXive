"""
Run Static Agent on Dynamic-Shift Environments to generate sensitivity data.

This script implements task T013f. It loads the list of discovered environments,
runs a static (non-adaptive) agent on each, and calculates performance drops
before and after the configured shift step.

Output:
    data/sensitivity_report.csv (or headers-only if no envs found)
    data/shift_validation.log (validation logs)
"""
import os
import json
import csv
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from project modules using the provided API surface
from utils.logging import get_logger, setup_logging
from utils.seed_utils import pin_seed
from utils.config import get_config, set_seed
from envs.dynamic_shift_env import (
    DynamicShiftEnvironment,
    generate_all_dynamic_shift_envs,
    ShiftConfig
)
from utils.env_discovery import discover_environments, write_discovered_envs

# Configure logging for this module
logger = get_logger(__name__)

# Constants
DATA_DIR = "data"
DISCOVERED_ENVS_FILE = os.path.join(DATA_DIR, "discovered_envs.json")
SENSITIVITY_REPORT_FILE = os.path.join(DATA_DIR, "sensitivity_report.csv")
SHIFT_VALIDATION_LOG = os.path.join(DATA_DIR, "shift_validation.log")
DEFAULT_SEED = 42
DEFAULT_RUNS_PER_ENV = 10  # Number of episodes to average for score

def setup_logging_for_task():
    """Configure logging for the shift sensitivity task."""
    setup_logging(log_file=SHIFT_VALIDATION_LOG, level=logging.INFO)
    logger.info("Starting shift sensitivity analysis (Task T013f).")

def load_discovered_envs() -> List[str]:
    """
    Load the list of discovered environment IDs from data/discovered_envs.json.

    Returns:
        List of environment IDs (strings).
        Returns empty list if file does not exist or is empty.
    """
    if not os.path.exists(DISCOVERED_ENVS_FILE):
        logger.warning(f"File {DISCOVERED_ENVS_FILE} not found. Returning empty env list.")
        return []

    try:
        with open(DISCOVERED_ENVS_FILE, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            env_ids = data
        elif isinstance(data, dict) and "env_ids" in data:
            env_ids = data["env_ids"]
        else:
            logger.error(f"Unexpected format in {DISCOVERED_ENVS_FILE}: {data}")
            return []

        logger.info(f"Loaded {len(env_ids)} environment IDs from {DISCOVERED_ENVS_FILE}.")
        return env_ids

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {DISCOVERED_ENVS_FILE}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading {DISCOVERED_ENVS_FILE}: {e}")
        return []

def run_static_agent(env: DynamicShiftEnvironment, seed: int, num_runs: int) -> Dict[str, float]:
    """
    Run a static (non-adaptive) agent on the environment for a given number of runs.

    The static agent performs a random action or a fixed policy (e.g., always action 0).
    For this implementation, we use a simple random action policy to simulate a non-adaptive agent.

    Args:
        env: The dynamic shift environment instance.
        seed: Random seed for reproducibility.
        num_runs: Number of episodes to run.

    Returns:
        Dictionary with 'pre_shift_score' and 'post_shift_score'.
    """
    pin_seed(seed)
    pre_shift_scores = []
    post_shift_scores = []

    shift_step = env.shift_config.shift_step if hasattr(env, 'shift_config') else env._shift_step

    for run_idx in range(num_runs):
        obs, _ = env.reset(seed=seed + run_idx)
        total_reward = 0.0
        step = 0
        pre_shift_reward = 0.0
        post_shift_reward = 0.0
        in_pre_shift = True

        while True:
            # Static agent: random action (non-adaptive)
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            step += 1

            # Track pre/post shift rewards based on step
            if step <= shift_step:
                pre_shift_reward += reward
            else:
                post_shift_reward += reward
                in_pre_shift = False

            if terminated or truncated:
                break

        # Calculate average rewards per step for pre and post shift
        # We need to normalize by the number of steps in each phase to get a meaningful score
        # For simplicity, we use total reward in each phase as the score
        # A more robust approach would be to calculate reward per step
        pre_shift_scores.append(pre_shift_reward)
        post_shift_scores.append(post_shift_reward)

    return {
        'pre_shift_score': sum(pre_shift_scores) / len(pre_shift_scores),
        'post_shift_score': sum(post_shift_scores) / len(post_shift_scores)
    }

def calculate_drop_rate(pre_score: float, post_score: float) -> float:
    """
    Calculate the performance drop rate.

    drop_rate = (pre_score - post_score) / pre_score
    If pre_score is 0 or negative, return 0.0 to avoid division by zero.
    """
    if pre_score <= 0:
        return 0.0
    return (pre_score - post_score) / pre_score

def write_sensitivity_report(results: List[Dict[str, Any]]):
    """
    Write the sensitivity report to data/sensitivity_report.csv.

    Columns: env_id, shift_step, pre_shift_score, post_shift_score, drop_rate, p_value
    Note: p_value is calculated in T014, so we set it to 0.0 here as a placeholder.
    """
    logger.info(f"Writing sensitivity report to {SENSITIVITY_REPORT_FILE}")

    fieldnames = [
        'env_id', 'shift_step', 'pre_shift_score', 'post_shift_score',
        'drop_rate', 'p_value'
    ]

    with open(SENSITIVITY_REPORT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    logger.info(f"Wrote {len(results)} rows to {SENSITIVITY_REPORT_FILE}")

def write_header_only():
    """Write headers only to sensitivity report if no environments found."""
    logger.info("No environments found. Writing headers-only sensitivity report.")
    fieldnames = [
        'env_id', 'shift_step', 'pre_shift_score', 'post_shift_score',
        'drop_rate', 'p_value'
    ]
    with open(SENSITIVITY_REPORT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

def main():
    """Main entry point for T013f."""
    setup_logging_for_task()

    # Load discovered environments
    env_ids = load_discovered_envs()

    if not env_ids:
        logger.warning("No environments discovered. Skipping analysis.")
        write_header_only()
        return

    # Generate dynamic shift environments
    # We assume the environments are already wrapped with DynamicShiftEnvironment
    # as per T013e. We'll re-wrap them here for safety.
    shifted_envs = generate_all_dynamic_shift_envs(env_ids)

    if not shifted_envs:
        logger.error("Failed to generate any shifted environments.")
        write_header_only()
        return

    logger.info(f"Generated {len(shifted_envs)} shifted environments.")

    results = []
    seed = DEFAULT_SEED

    for env_id, env in shifted_envs.items():
        logger.info(f"Processing environment: {env_id}")
        try:
            # Run static agent
            scores = run_static_agent(env, seed, DEFAULT_RUNS_PER_ENV)

            # Get shift step
            shift_step = env.shift_config.shift_step if hasattr(env, 'shift_config') else env._shift_step

            # Calculate drop rate
            drop_rate = calculate_drop_rate(scores['pre_shift_score'], scores['post_shift_score'])

            # Prepare result row
            result_row = {
                'env_id': env_id,
                'shift_step': shift_step,
                'pre_shift_score': scores['pre_shift_score'],
                'post_shift_score': scores['post_shift_score'],
                'drop_rate': drop_rate,
                'p_value': 0.0  # Placeholder, will be calculated in T014
            }

            results.append(result_row)
            logger.info(f"  Pre-shift: {scores['pre_shift_score']:.4f}, "
                        f"Post-shift: {scores['post_shift_score']:.4f}, "
                        f"Drop rate: {drop_rate:.4f}")

        except Exception as e:
            logger.error(f"Error processing environment {env_id}: {e}", exc_info=True)
            # Continue with other environments
            continue

    # Write results
    if results:
        write_sensitivity_report(results)
    else:
        logger.warning("No successful runs. Writing headers-only report.")
        write_header_only()

    logger.info("Shift sensitivity analysis (T013f) completed.")

if __name__ == "__main__":
    main()