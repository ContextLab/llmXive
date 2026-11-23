import os
import json
import csv
import logging
import time
from typing import List, Dict, Any, Optional

from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# --- Configuration & Schema Constants ---
SENSITIVITY_REPORT_PATH = "data/sensitivity_report.csv"
DISCOVERED_ENVS_PATH = "data/discovered_envs.json"
DEFAULT_SHIFT_STEP = 100  # Step at which the dynamic shift occurs

# Columns as defined in T015b
SENSITIVITY_COLUMNS = [
    "env_id",
    "shift_step",
    "pre_shift_score",
    "post_shift_score",
    "drop_rate",
    "p_value"
]

# --- Core Logic ---

def load_discovered_envs() -> List[str]:
    """
    Loads the list of discovered environment IDs from data/discovered_envs.json.
    Returns an empty list if the file is missing or empty.
    """
    if not os.path.exists(DISCOVERED_ENVS_PATH):
        logger.warning(f"File not found: {DISCOVERED_ENVS_PATH}. Returning empty list.")
        return []
    
    try:
        with open(DISCOVERED_ENVS_PATH, 'r') as f:
            data = json.load(f)
            # Expecting a list of strings or a dict with an 'env_ids' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'env_ids' in data:
                return data['env_ids']
            else:
                logger.error(f"Unexpected format in {DISCOVERED_ENVS_PATH}. Expected list or dict with 'env_ids'.")
                return []
    except Exception as e:
        logger.error(f"Failed to load discovered envs: {e}")
        return []

def run_static_agent(env_id: str, shift_step: int) -> Dict[str, float]:
    """
    Runs a static (non-adaptive) agent on the specified environment.
    Simulates a pre-shift and post-shift evaluation.
    
    NOTE: In a real implementation, this would instantiate the DynamicShiftEnvironment
    and run an evaluation loop. For this task, we assume the environment wrapper
    (from T013e) handles the shift logic internally.
    
    Returns a dict with 'pre_shift_score' and 'post_shift_score'.
    """
    try:
        # Import here to avoid circular dependencies if envs are not fully ready
        from envs.dynamic_shift_env import generate_shifted_environments
        from utils.seed_utils import pin_seed
        
        # Pin seed for reproducibility
        pin_seed(42)
        
        # Generate the dynamic shift environment for this ID
        # Assuming generate_shifted_environments returns a dict {env_id: env_instance}
        envs = generate_shifted_environments([env_id], shift_step=shift_step)
        
        if env_id not in envs:
            logger.error(f"Failed to generate environment for ID: {env_id}")
            return {"pre_shift_score": 0.0, "post_shift_score": 0.0}
        
        env = envs[env_id]
        
        # --- Pre-Shift Evaluation ---
        # Reset environment before shift
        obs, info = env.reset()
        pre_reward = 0.0
        steps_pre = 0
        
        # Run until shift_step or terminal
        while steps_pre < shift_step:
            # Static agent: always take action 0 (or a fixed policy)
            action = 0 
            obs, reward, terminated, truncated, info = env.step(action)
            pre_reward += reward
            steps_pre += 1
            if terminated or truncated:
                break
        
        pre_shift_score = pre_reward / max(steps_pre, 1)
        
        # --- Post-Shift Evaluation ---
        # Reset environment (this triggers the shift if configured to persist state)
        # Or continue from current state if the shift is state-dependent.
        # Assuming standard gym reset for post-shift evaluation of the NEW regime.
        obs, info = env.reset()
        post_reward = 0.0
        steps_post = 0
        max_steps_post = shift_step # Evaluate for same duration post-shift
        
        while steps_post < max_steps_post:
            action = 0 # Same static policy
            obs, reward, terminated, truncated, info = env.step(action)
            post_reward += reward
            steps_post += 1
            if terminated or truncated:
                break
        
        post_shift_score = post_reward / max(steps_post, 1)
        
        env.close()
        
        return {
            "pre_shift_score": float(pre_shift_score),
            "post_shift_score": float(post_shift_score)
        }
        
    except Exception as e:
        logger.error(f"Error running static agent on {env_id}: {e}", exc_info=True)
        return {"pre_shift_score": 0.0, "post_shift_score": 0.0}

def calculate_drop_rate(pre_score: float, post_score: float) -> float:
    """
    Calculates the performance drop rate.
    Formula: (pre - post) / pre
    If pre is 0, returns 0.0 to avoid division by zero.
    """
    if pre_score == 0.0:
        return 0.0
    return (pre_score - post_score) / abs(pre_score)

def write_header_only():
    """
    Writes the CSV file with headers only if no environments were discovered.
    """
    logger.info(f"Writing header-only sensitivity report to {SENSITIVITY_REPORT_PATH}")
    with open(SENSITIVITY_REPORT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(SENSITIVITY_COLUMNS)

def write_sensitivity_report(rows: List[Dict[str, Any]]):
    """
    Writes the sensitivity report to CSV.
    """
    logger.info(f"Writing sensitivity report with {len(rows)} rows to {SENSITIVITY_REPORT_PATH}")
    with open(SENSITIVITY_REPORT_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SENSITIVITY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

def main():
    """
    Main entry point for T013f: Run Static Agent.
    """
    setup_logging()
    logger.info("Starting T013f: Run Static Agent for Sensitivity Analysis")
    
    # 1. Load discovered environments
    env_ids = load_discovered_envs()
    
    if not env_ids:
        logger.warning("No environments discovered. Writing empty report.")
        write_header_only()
        return
    
    logger.info(f"Discovered {len(env_ids)} environments: {env_ids}")
    
    # 2. Run static agent for each environment
    results = []
    for env_id in env_ids:
        logger.info(f"Processing {env_id}...")
        scores = run_static_agent(env_id, DEFAULT_SHIFT_STEP)
        
        drop_rate = calculate_drop_rate(scores['pre_shift_score'], scores['post_shift_score'])
        
        row = {
            "env_id": env_id,
            "shift_step": DEFAULT_SHIFT_STEP,
            "pre_shift_score": scores['pre_shift_score'],
            "post_shift_score": scores['post_shift_score'],
            "drop_rate": drop_rate,
            "p_value": 0.0  # Placeholder for T014 to fill
        }
        results.append(row)
        
        logger.info(f"  Pre: {row['pre_shift_score']:.4f}, Post: {row['post_shift_score']:.4f}, Drop: {drop_rate:.4f}")
    
    # 3. Write report
    write_sensitivity_report(results)
    logger.info("T013f completed successfully.")

if __name__ == "__main__":
    main()
