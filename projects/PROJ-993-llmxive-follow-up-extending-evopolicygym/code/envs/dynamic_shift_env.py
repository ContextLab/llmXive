"""
Dynamic shift environment wrapper for EvoPolicyGym.
Implements configurable shift injection at a specific step N.
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
    """
    Configuration for dynamic shift injection.
    Enforces default moderate step N (50% of budget) if not provided.
    """
    shift_step: int = 500
    shift_magnitude: float = 0.5
    shift_type: str = "reward"  # "reward" or "transition"
    enabled: bool = True
    budget: int = 1000  # Total episode budget to calculate default step

    def __post_init__(self):
        """Enforce default moderate step N if shift_step is not explicitly set or is 0."""
        if self.shift_step <= 0:
            # Default to 50% of the budget as the moderate shift point
            self.shift_step = int(self.budget * 0.5)
            logger.info("Shift step not provided or invalid. Using default moderate step: %d (50%% of budget %d)",
                        self.shift_step, self.budget)

def get_default_shift_config() -> ShiftConfig:
    """Return the default shift configuration with moderate step N."""
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
        self._current_step = 0

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict] = None):
        """Reset the environment and reset shift state."""
        obs, info = super().reset(seed=seed, options=options)
        self._current_step = 0
        self.shifted = False
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Step the environment, applying shift if configured step is reached.

        Args:
            action: The action to take.

        Returns:
            Tuple of (observation, reward, terminated, truncated, info).
        """
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._current_step += 1

        if not self.shifted and self.config.enabled and self._current_step >= self.config.shift_step:
            self._apply_shift()
            self.shifted = True
            info['shift_applied'] = True
        else:
            info['shift_applied'] = False

        return obs, reward, terminated, truncated, info

    def _apply_shift(self):
        """Apply the configured shift to the environment."""
        self.logger.info("Applying %s shift with magnitude %f at step %d",
                       self.config.shift_type, self.config.shift_magnitude, self._current_step)
        
        # Implement actual shift logic based on shift_type
        if self.config.shift_type == "reward":
            self._apply_reward_shift()
        elif self.config.shift_type == "transition":
            self._apply_transition_shift()
        else:
            self.logger.warning("Unknown shift_type: %s. No shift applied.", self.config.shift_type)

    def _apply_reward_shift(self):
        """
        Apply reward shift by modifying the reward function.
        For environments with a reward_function attribute, we wrap it.
        For others, we inject a shift signal into the info dict that
        downstream components can use to adjust rewards.
        """
        # Mark that reward shift is active
        self.shifted = True
        
        # Attempt to modify environment's reward function if it exists
        if hasattr(self.env, 'reward_function') and callable(self.env.reward_function):
            original_reward_fn = self.env.reward_function
            magnitude = self.config.shift_magnitude
            
            def shifted_reward_fn(state, action, next_state):
                original_reward = original_reward_fn(state, action, next_state)
                # Apply magnitude shift (can be positive or negative depending on implementation)
                # Here we assume magnitude > 0 means reduction in reward for non-adaptive agents
                return original_reward * (1.0 - magnitude)
            
            self.env.reward_function = shifted_reward_fn
            self.logger.debug("Wrapped reward function with shift magnitude %f", magnitude)
        
        # Also modify the immediate reward returned by step if it's a simple gym env
        # This is a fallback for environments that don't expose reward_function
        if hasattr(self.env, '_step') and callable(self.env._step):
            # This is a more invasive approach, modifying the step method behavior
            # For now, we rely on the info dict to signal the shift
            pass

    def _apply_transition_shift(self):
        """
        Apply transition shift by modifying transition probabilities.
        This is more complex and environment-specific.
        For now, we signal the shift and let the environment handle it
        if it has the capability.
        """
        self.shifted = True
        
        # Attempt to modify transition dynamics if the environment supports it
        if hasattr(self.env, 'transition_matrix') and hasattr(self.env, 'set_transition_matrix'):
            original_matrix = self.env.transition_matrix
            magnitude = self.config.shift_magnitude
            
            # Create a perturbed transition matrix
            # This is a simplified approach - real implementation would be environment-specific
            noise = np.random.randn(*original_matrix.shape) * magnitude
            perturbed_matrix = original_matrix + noise
            
            # Normalize to ensure valid probabilities
            perturbed_matrix = np.clip(perturbed_matrix, 0, 1)
            perturbed_matrix = perturbed_matrix / perturbed_matrix.sum(axis=-1, keepdims=True)
            
            self.env.set_transition_matrix(perturbed_matrix)
            self.logger.debug("Modified transition matrix with magnitude %f", magnitude)
        
        # For environments without explicit transition matrix, signal the shift
        # The environment can then internally adjust its dynamics

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
        try:
            base_env = gym.make(name)
            shifted_env = DynamicShiftEnvironment(base_env, config)
            shifted_envs.append((f"{name}_shifted", shifted_env))
            logger.info("Created shifted environment: %s", f"{name}_shifted")
        except Exception as e:
            logger.error("Failed to create shifted environment for %s: %s", name, e)
    return shifted_envs

def generate_all_dynamic_shift_envs(env_registry_path: str, output_path: str):
    """
    Generate all dynamic shift environments and save registry.

    Args:
        env_registry_path: Path to base environment registry.
        output_path: Path to save the generated registry.
    """
    logger.info("Generating dynamic shift environments from registry: %s", env_registry_path)
    
    if not os.path.exists(env_registry_path):
        logger.error("Registry file not found: %s", env_registry_path)
        return

    try:
        with open(env_registry_path, 'r') as f:
            registry = json.load(f)
        
        env_names = list(registry.keys())
        config = get_default_shift_config()
        
        shifted_envs = generate_shifted_environments(env_names, config)
        
        # Save registry of shifted environments
        shifted_registry = {}
        for name, env in shifted_envs:
            shifted_registry[name] = {
                'base_env': name.replace('_shifted', ''),
                'shift_config': {
                    'shift_step': config.shift_step,
                    'shift_magnitude': config.shift_magnitude,
                    'shift_type': config.shift_type
                }
            }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(shifted_registry, f, indent=2)
        
        logger.info("Saved shifted environment registry to: %s", output_path)
        
    except Exception as e:
        logger.error("Failed to generate dynamic shift environments: %s", e)
        raise