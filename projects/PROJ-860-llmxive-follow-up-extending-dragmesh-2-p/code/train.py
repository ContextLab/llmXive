import os
import sys
import time
import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Import project modules
from environment import PhysicsEnvironment, create_cpu_environment
from estimator import VirtualTactileEstimator
from scheduler import AdaptiveRewardScheduler
from seed_config import set_seeds, enforce_seed_in_training_loop
from logging_config import setup_training_logger, get_logger_for_module

# Configure logging for this module
logger = setup_training_logger() if 'setup_training_logger' in dir() else logging.getLogger(__name__)

class TrainingStats:
    """Container for training metrics and state."""
    def __init__(self):
        self.episode_count = 0
        self.total_steps = 0
        self.success_count = 0
        self.average_reward = 0.0
        self.estimated_stiffness_history: List[float] = []
        self.reward_adjustment_history: List[Dict[str, float]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'episode_count': self.episode_count,
            'total_steps': self.total_steps,
            'success_count': self.success_count,
            'average_reward': self.average_reward,
            'avg_estimated_stiffness': np.mean(self.estimated_stiffness_history) if self.estimated_stiffness_history else 0.0,
            'last_reward_adjustment': self.reward_adjustment_history[-1] if self.reward_adjustment_history else None
        }

class AdaptiveTrainingLoop:
    """
    Main training loop integrating VirtualTactileEstimator and AdaptiveRewardScheduler.
    Implements FR-001 (Estimation), FR-002 (Adaptation), FR-004 (CPU-only), FR-007 (Stiction).
    """
    def __init__(self, 
                 env: PhysicsEnvironment,
                 estimator: VirtualTactileEstimator,
                 scheduler: AdaptiveRewardScheduler,
                 seed: int = 42,
                 log_interval: int = 10):
        self.env = env
        self.estimator = estimator
        self.scheduler = scheduler
        self.seed = seed
        self.log_interval = log_interval
        self.stats = TrainingStats()
        
        # Set global seeds for reproducibility
        set_seeds(self.seed)
        enforce_seed_in_training_loop(self.seed)

        # Ensure CPU mode is enforced at runtime (FR-004)
        if hasattr(self.env, 'check_cpu_mode'):
            self.env.check_cpu_mode()

    def run_episode(self, episode_id: int, max_steps: int = 500) -> Tuple[bool, float]:
        """
        Run a single training episode with adaptive reward scheduling.
        
        Returns:
            Tuple of (success, total_reward)
        """
        self.env.reset()
        self.estimator.reset()
        
        episode_reward = 0.0
        step_count = 0
        success = False

        # Log initial state
        logger.debug(f"Starting episode {episode_id} with seed {self.seed}")

        for step in range(max_steps):
            # 1. Get current state and actions
            state = self.env.get_state()
            action = self.env.get_policy_action(state) # Placeholder for actual policy logic

            # 2. Step environment
            next_state, reward, done, info = self.env.step(action)

            # 3. Estimate virtual tactile stiffness (k_est)
            # The estimator needs torque derivative and velocity derivative
            # Assuming env provides these in info or state for this implementation
            torque_deriv = info.get('torque_derivative', np.array([0.0]))
            velocity_deriv = info.get('velocity_derivative', np.array([0.0]))
            
            k_est = self.estimator.update(torque_deriv, velocity_deriv)
            
            # LOGGING REQUIREMENT T016b: Log k_est value
            logger.info(f"[Episode {episode_id}, Step {step}] Estimated Stiffness (k_est): {k_est:.6f}")

            # 4. Adjust rewards based on k_est
            # The scheduler maps k_est to reward weights/multipliers
            reward_adjustment = self.scheduler.update(k_est, current_reward=reward)
            
            # LOGGING REQUIREMENT T016b: Log reward weight adjustments
            # The scheduler returns a dict with the specific adjustments made
            if reward_adjustment:
                for key, value in reward_adjustment.items():
                    logger.info(f"[Episode {episode_id}, Step {step}] Reward Adjustment: {key} changed by {value:.4f} (New Value: {reward_adjustment.get(f'{key}_new', 'N/A')})")
                
                # Log the specific multipliers if available
                if 'multiplier' in reward_adjustment:
                    logger.info(f"[Episode {episode_id}, Step {step}] Final Reward Multiplier applied: {reward_adjustment['multiplier']:.4f}")

            # Apply adjustment to current reward
            adjusted_reward = reward * reward_adjustment.get('multiplier', 1.0)
            episode_reward += adjusted_reward

            # 5. Check termination
            if done:
                success = info.get('success', False)
                break

            step_count += 1

        # Update stats
        self.stats.episode_count += 1
        self.stats.total_steps += step_count
        if success:
            self.stats.success_count += 1
        self.stats.average_reward = (self.stats.average_reward * (self.stats.episode_count - 1) + episode_reward) / self.stats.episode_count
        self.stats.estimated_stiffness_history.append(k_est)
        self.stats.reward_adjustment_history.append(reward_adjustment)

        # Log periodic summary
        if self.stats.episode_count % self.log_interval == 0:
            logger.info(f"Training Summary at Episode {self.stats.episode_count}: "
                        f"Avg Reward: {self.stats.average_reward:.4f}, "
                        f"Avg k_est: {np.mean(self.stats.estimated_stiffness_history):.4f}, "
                        f"Success Rate: {self.stats.success_count/self.stats.episode_count:.2%}")

        return success, episode_reward

    def train(self, num_episodes: int = 100) -> Dict[str, Any]:
        """
        Run the full training loop.
        
        Args:
            num_episodes: Number of episodes to train for.
            
        Returns:
            Final training statistics dictionary.
        """
        logger.info(f"Starting Adaptive Training Loop for {num_episodes} episodes.")
        
        start_time = time.time()
        
        for ep in range(num_episodes):
            success, total_reward = self.run_episode(ep)
            
            # Optional: Early stopping or checkpointing could go here
            
        elapsed_time = time.time() - start_time
        
        final_stats = self.stats.to_dict()
        final_stats['training_time_seconds'] = elapsed_time
        
        logger.info(f"Training completed in {elapsed_time:.2f}s. Final Success Rate: {final_stats['success_count']/num_episodes:.2%}")
        logger.debug(f"Final Stats: {json.dumps(final_stats, indent=2)}")
        
        return final_stats

def run_episode(env, estimator, scheduler, episode_id):
    """Convenience wrapper for single episode execution."""
    loop = AdaptiveTrainingLoop(env, estimator, scheduler)
    return loop.run_episode(episode_id)

def train(num_episodes: int = 100, seed: int = 42) -> Dict[str, Any]:
    """
    Main entry point for training.
    
    Args:
        num_episodes: Number of training episodes.
        seed: Random seed for reproducibility.
        
    Returns:
        Training results dictionary.
    """
    # Setup environment
    env = create_cpu_environment()
    estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
    scheduler = AdaptiveRewardScheduler()
    
    # Create loop
    loop = AdaptiveTrainingLoop(env, estimator, scheduler, seed=seed)
    
    # Run training
    results = loop.train(num_episodes)
    
    return results

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train Adaptive Tactile Policy')
    parser.add_argument('--episodes', type=int, default=100, help='Number of episodes')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    results = train(num_episodes=args.episodes, seed=args.seed)
    
    print(json.dumps(results, indent=2))
    
    return results

if __name__ == '__main__':
    main()