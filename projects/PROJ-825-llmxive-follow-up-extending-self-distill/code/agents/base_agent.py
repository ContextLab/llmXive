"""
Base Agent Module for llmXive.
Defines the abstract interface for Reinforcement Learning agents used in the SDAR pipeline.
"""
import abc
from typing import Any, Dict, Optional, Tuple, List
import numpy as np
import torch

from config import TrainingConfig, EnvironmentConfig, ModelConfig
from utils.logging import get_logger, log_training_run


class BaseAgent(abc.ABC):
    """
    Abstract base class for all RL agents in the llmXive pipeline.
    
    This class defines the standard interface for:
    1. Initialization with configuration and models.
    2. Step execution (observation -> action -> reward).
    3. Training/Update logic (optional, depending on agent type).
    4. Logging and metric tracking.
    
    Attributes:
        config (TrainingConfig): The training configuration object.
        env_config (EnvironmentConfig): The environment configuration.
        model_config (ModelConfig): The model configuration.
        logger: The logger instance for the run.
        step_count (int): Global step counter.
        episode_count (int): Current episode counter.
        episode_reward (float): Cumulative reward for the current episode.
    """

    def __init__(
        self,
        config: TrainingConfig,
        env_config: EnvironmentConfig,
        model_config: ModelConfig,
        seed: int = 42
    ):
        """
        Initialize the Base Agent.
        
        Args:
            config: Training configuration.
            env_config: Environment configuration.
            model_config: Model configuration.
            seed: Random seed for reproducibility.
        """
        self.config = config
        self.env_config = env_config
        self.model_config = model_config
        self.seed = seed
        
        # Initialize RNG state
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.manual_seed(seed)
            torch.cuda.manual_seed(seed)
            
        self.logger = get_logger(run_id=f"{config.variant}_{seed}")
        self.step_count = 0
        self.episode_count = 0
        self.episode_reward = 0.0
        self.is_training = False

    @abc.abstractmethod
    def reset(self, env: Any) -> Any:
        """
        Reset the agent's internal state at the start of a new episode.
        
        Args:
            env: The environment instance to reset.
            
        Returns:
            The initial observation from the environment.
        """
        pass

    @abc.abstractmethod
    def select_action(self, observation: Any, training: bool = False) -> Tuple[Any, Dict[str, Any]]:
        """
        Select an action based on the current observation.
        
        Args:
            observation: The current environment observation.
            training: If True, the agent is in training mode (may explore more).
            
        Returns:
            A tuple containing:
            - action: The selected action.
            - info: A dictionary of metadata (e.g., logits, entropy, gating scores).
        """
        pass

    @abc.abstractmethod
    def update(self, trajectory: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Update the agent's policy/value networks based on a collected trajectory.
        
        Args:
            trajectory: A list of step dictionaries containing states, actions, rewards, etc.
            
        Returns:
            A dictionary of loss metrics (e.g., {'policy_loss': 0.05, 'value_loss': 0.02}).
        """
        pass

    def run_episode(self, env: Any, max_steps: Optional[int] = None) -> float:
        """
        Run a single episode in the environment.
        
        This method orchestrates the interaction loop: reset -> observe -> act -> reward -> step.
        
        Args:
            env: The environment instance.
            max_steps: Optional override for the maximum number of steps per episode.
            
        Returns:
            The total reward accumulated in the episode.
        """
        obs = self.reset(env)
        total_reward = 0.0
        step_limit = max_steps if max_steps is not None else self.env_config.max_steps_per_episode
        
        self.episode_reward = 0.0
        
        self.logger.log_gating_signal(
            episode_id=self.episode_count,
            step_id=0,
            event="episode_start",
            metrics={"episode": self.episode_count, "limit": step_limit}
        )

        for step in range(step_limit):
            action, info = self.select_action(obs, training=self.is_training)
            
            next_obs, reward, done, truncated, info_env = env.step(action)
            
            total_reward += reward
            self.episode_reward += reward
            self.step_count += 1

            # Log step metrics if available in info
            log_data = {
                "episode": self.episode_count,
                "step": step,
                "reward": reward,
                "cumulative_reward": self.episode_reward,
                "done": done,
                **info
            }
            self.logger.log_gating_signal(
                episode_id=self.episode_count,
                step_id=step,
                event="step_complete",
                metrics=log_data
            )

            if done or truncated:
                self.logger.log_gating_signal(
                    episode_id=self.episode_count,
                    step_id=step,
                    event="episode_end",
                    metrics={"final_reward": self.episode_reward, "steps_taken": step + 1}
                )
                self.episode_count += 1
                return total_reward

            obs = next_obs

        # If max steps reached without termination
        self.logger.log_gating_signal(
            episode_id=self.episode_count,
            step_id=step_limit,
            event="step_limit_reached",
            metrics={"final_reward": self.episode_reward, "steps_taken": step_limit}
        )
        self.episode_count += 1
        return total_reward

    def train(self, env: Any, num_episodes: int) -> Dict[str, float]:
        """
        Execute a training run for a specified number of episodes.
        
        Args:
            env: The environment instance.
            num_episodes: Number of episodes to train.
            
        Returns:
            Aggregated training metrics.
        """
        self.is_training = True
        all_metrics = {}
        
        self.logger.log_training_run(
            variant=self.config.variant,
            num_episodes=num_episodes,
            seed=self.seed,
            model_type=self.model_config.model_type
        )

        for ep in range(num_episodes):
            self.episode_reward = 0.0
            # Collect trajectory for update
            trajectory = []
            obs = self.reset(env)
            
            for step in range(self.env_config.max_steps_per_episode):
                action, info = self.select_action(obs, training=True)
                next_obs, reward, done, truncated, info_env = env.step(action)
                
                trajectory.append({
                    "step": step,
                    "obs": obs,
                    "action": action,
                    "reward": reward,
                    "next_obs": next_obs,
                    "done": done,
                    "info": {**info, **info_env}
                })
                
                if done or truncated:
                    break
                obs = next_obs

            # Update agent
            step_metrics = self.update(trajectory)
            
            # Aggregate metrics
            for k, v in step_metrics.items():
                if k not in all_metrics:
                    all_metrics[k] = []
                all_metrics[k].append(v)
            
            # Log episode summary
            self.logger.log_gating_signal(
                episode_id=ep,
                step_id=-1,
                event="episode_summary",
                metrics={
                    "total_reward": sum(t["reward"] for t in trajectory),
                    "steps": len(trajectory)
                }
            )

        self.is_training = False
        # Compute averages
        return {k: np.mean(v) for k, v in all_metrics.items()}

    def save_checkpoint(self, path: str) -> None:
        """
        Save the current model state to disk.
        
        Args:
            path: File path to save the checkpoint.
        """
        raise NotImplementedError("Subclasses must implement save_checkpoint")

    def load_checkpoint(self, path: str) -> None:
        """
        Load a model checkpoint from disk.
        
        Args:
            path: File path to load the checkpoint from.
        """
        raise NotImplementedError("Subclasses must implement load_checkpoint")
