import csv
import json
import logging
import ast
import os
from typing import List, Dict, Any, Optional, Callable, Tuple
import random
import time

from envs.base_env import BaseEvoEnv
from envs.dynamic_shift_env import DynamicShiftEnvironment
from utils.config import set_seed
from utils.logging import get_logger

logger = get_logger(__name__)

class GenerationError(Exception):
    """Custom exception for policy generation errors."""
    pass

class EvolutionaryHarness:
    """
    Runs agents on both baseline and counterfactual conditions.
    """
    def __init__(self):
        self.logger = get_logger(__name__)

    def run(self, env_id: str, condition: str, seed: int, run_id: int) -> Tuple[float, str]:
        """
        Runs a single evolutionary run.
        Returns: (score, policy_code_string)
        """
        set_seed(seed)
        
        # 1. Setup Environment
        # T013d ensures environments are registered. We instantiate here.
        # If condition is 'counterfactual', we might need to apply shifts?
        # T033: Implement baseline vs counterfactual logic.
        # For now, we assume the environment handles the shift if configured.
        # We'll create a basic environment for the harness to evolve a policy for.
        
        try:
            # If the env_id corresponds to a dynamic shift env, we use it.
            # Otherwise, we use a base env.
            # For simplicity in this harness, we assume env_id is valid.
            env = DynamicShiftEnvironment(env_id, {"shift_step": 80})
        except Exception as e:
            logger.warning(f"Failed to create DynamicShiftEnvironment for {env_id}, falling back to base. Error: {e}")
            # Fallback to a simple env if dynamic one fails
            env = BaseEvoEnv(env_id)

        # 2. Evolution Loop (Simplified for CLI demo)
        # T032a: Must ensure policy write is flushed before parsing.
        # We simulate a "policy" generation. In a real scenario, this would be an LLM/Genetic Algo.
        # Since we are in a CLI entry point context without a full LLM backend running,
        # we will generate a deterministic "policy" based on the seed and condition.
        
        policy_code = self._generate_dummy_policy(env_id, condition, seed, run_id)
        
        # Simulate execution of the policy to get a score
        score = self._evaluate_policy(env, policy_code)
        
        # T032a: Ensure policy write is flushed
        # We write the policy to a temp file to simulate the write/flush check
        policy_path = f"data/policy_{run_id}.py"
        with open(policy_path, 'w') as f:
            f.write(policy_code)
        # Ensure flush
        if hasattr(f, 'flush'):
            pass # Context manager handles flush
        
        # File existence check (T032a requirement)
        if not os.path.exists(policy_path):
            raise GenerationError(f"Policy file {policy_path} was not created.")

        return score, policy_code

    def _generate_dummy_policy(self, env_id: str, condition: str, seed: int, run_id: int) -> str:
        """
        Generates a dummy policy code string for testing.
        In a real implementation, this would call the LLM generator (T021).
        """
        # Create a simple Python function that acts as a policy
        # The content depends on condition to simulate difference
        base_logic = "action = 0"
        if condition == "counterfactual":
            base_logic = "action = 1 # Counterfactual adjustment"
        
        code = f"""
import gymnasium as gym
def policy(obs, info):
    # Seed: {seed}, Run: {run_id}, Condition: {condition}
    {base_logic}
    return action
"""
        return code

    def _evaluate_policy(self, env: BaseEvoEnv, policy_code: str) -> float:
        """
        Executes the policy code in the environment and returns the score.
        """
        try:
            # Execute the policy code in a safe namespace
            namespace = {}
            exec(policy_code, namespace)
            policy_func = namespace.get('policy')
            
            if not callable(policy_func):
                logger.warning("Policy code did not define a callable 'policy' function.")
                return 0.0
            
            obs, _ = env.reset()
            total_reward = 0.0
            done = False
            step = 0
            
            while not done and step < 100:
                try:
                    action = policy_func(obs, {})
                    obs, reward, terminated, truncated, _ = env.step(action)
                    total_reward += reward
                    done = terminated or truncated
                except Exception as e:
                    logger.warning(f"Policy execution error: {e}")
                    break
                step += 1
            
            return total_reward
            
        except Exception as e:
            logger.error(f"Error evaluating policy: {e}")
            return 0.0