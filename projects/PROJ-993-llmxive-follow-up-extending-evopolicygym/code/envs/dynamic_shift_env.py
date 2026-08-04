"""
Dynamic shift environment wrapper for EvoPolicyGym.
"""
import gymnasium as gym
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import json
import os
from dataclasses import dataclass, field
import logging

from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ShiftConfig:
    """Configuration for dynamic shift injection."""
    shift_step: int = 500
    shift_magnitude: float = 0.5
    shift_type: str = "reward"  # "reward" or "transition"
    enabled: bool = True

def get_default_shift_config() -> ShiftConfig:
    """Return the default shift configuration."""
    return ShiftConfig()

class DynamicShiftEnvironment(gym.Wrapper):
    """
    Environment wrapper that injects dynamic shifts at a configured step.
    """

    def __init__(self, env: gym.Env, config: Optional[ShiftConfig] = None):
        """
        Initialize the dynamic shift environment.

        Args:
            env: The base environment to wrap.
            config: Shift configuration.
        """
        super().__init__(env)
        self.config = config or get_default_shift_config()
        self.shifted = False
        self.logger = logger

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Step the environment, applying shift if configured step is reached.

        Args:
            action: The action to take.

        Returns:
            Tuple of (observation, reward, terminated, truncated, info).
        """
        obs, reward, terminated, truncated, info = self.env.step(action)

        if not self.shifted and self.env.unwrapped._current_step >= self.config.shift_step:
            self._apply_shift()
            self.shifted = True

        return obs, reward, terminated, truncated, info

    def _apply_shift(self):
        """Apply the configured shift to the environment."""
        self.logger.info("Applying %s shift with magnitude %f",
                       self.config.shift_type, self.config.shift_magnitude)
        # Placeholder for actual shift logic
        # In real implementation, modify reward function or transition probs

def generate_shifted_environments(env_names: List[str], config: ShiftConfig) -> List[Tuple[str, gym.Env]]:
    """
    Generate dynamic shift variants of existing environments.

    Args:
        env_names: List of base environment names.
        config: Shift configuration.

    Returns:
        List of (name, env) tuples.
    """
    shifted_envs = []
    for name in env_names:
        # Placeholder: assume base env creation
        base_env = gym.make(name)
        shifted_env = DynamicShiftEnvironment(base_env, config)
        shifted_envs.append((f"{name}_shifted", shifted_env))
    return shifted_envs

def generate_all_dynamic_shift_envs(env_registry_path: str, output_path: str):
    """
    Generate all dynamic shift environments and save registry.

    Args:
        env_registry_path: Path to base environment registry.
        output_path: Path to save the generated registry.
    """
    # Placeholder implementation
    logger.info("Generating dynamic shift environments...")
    # In real implementation, load registry and generate variants
