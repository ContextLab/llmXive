"""
Base Agent class defining the RL loop interface.

Implements T009 requirements.
"""
import abc
from typing import Any, Dict, Optional, Tuple, List
import numpy as np
import torch
from config import TrainingConfig, EnvironmentConfig, ModelConfig
from utils.logging import get_logger, log_training_run

logger = get_logger(__name__)

class BaseAgent(abc.ABC):
    """
    Abstract base class for all agents in the system.
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.step_count = 0
        
    @abc.abstractmethod
    def select_action(self, state: Dict, step: int) -> Dict:
        """
        Select an action based on the current state.
        
        Args:
            state: Current environment state.
            step: Current step number.
            
        Returns:
            Dictionary containing the action and any auxiliary data.
        """
        pass

    @abc.abstractmethod
    def train(self, episode_data: List[Dict]) -> Dict:
        """
        Train the agent on the given episode data.
        
        Args:
            episode_data: List of transitions from the episode.
            
        Returns:
            Dictionary of training metrics.
        """
        pass

    def reset(self):
        """Reset the agent state."""
        self.step_count = 0

    def run_episode(self, env: Any) -> Dict:
        """
        Run a single episode.
        
        Args:
            env: The environment to run the episode in.
            
        Returns:
            Dictionary containing episode metrics.
        """
        self.reset()
        state, info = env.reset()
        done = False
        episode_reward = 0.0
        episode_data = []
        
        while not done:
            action_dict = self.select_action(state, self.step_count)
            action = action_dict["action"]
            
            next_state, reward, done, info = env.step(action)
            
            episode_data.append({
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "done": done,
                "info": info,
                "aux": action_dict
            })
            
            episode_reward += reward
            state = next_state
            self.step_count += 1
            
            if self.step_count > 1000: # Safety limit
                done = True
                
        return {
            "reward": episode_reward,
            "steps": self.step_count,
            "data": episode_data
        }
