"""
Simulation Runner for OPID Critical-First Routing Complexity Analysis.

This module implements the ExperimentRunner class to orchestrate the full sweep
of thresholds and tiers, executing episodes sequentially to manage memory constraints.
"""

import logging
import time
import csv
import os
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
import numpy as np

# Local imports matching the provided API surface
from config import get_seed, set_seed, ensure_directories, EPISODES_PER_SETTING, THRESHOLD_STEPS
from environment.graph_generator import GraphGenerator
from agent.opid_router import OPIDRouter
from agent.policy import BaselinePolicy, create_baseline_policy
from utils.metrics import calculate_success_rate, calculate_action_entropy
from utils.logging_setup import get_experiment_logger


@dataclass
class EpisodeResult:
    """Container for the results of a single episode."""
    tier: int
    threshold: float
    episode_id: int
    success: bool
    steps: int
    total_log_prob_shift: float
    action_entropy: float
    trajectory_length: int


@dataclass
class RunnerConfig:
    """Configuration for the ExperimentRunner."""
    seed: int
    num_tiers: int
    thresholds: List[float]
    episodes_per_setting: int
    output_dir: str
    log_level: str = "INFO"


class ExperimentRunner:
    """
    Orchestrates the full sweep of experiments across tiers and thresholds.

    This class manages the execution of episodes, ensuring sequential processing
    to stay within memory limits (< 7GB RAM) and writing results to disk immediately.
    """

    def __init__(self, config: RunnerConfig):
        self.config = config
        self.logger = get_experiment_logger("ExperimentRunner", level=config.log_level)
        ensure_directories([config.output_dir])
        
        # Initialize components
        self.graph_generator = GraphGenerator()
        self.policy = create_baseline_policy()
        
        # Ensure reproducibility
        set_seed(config.seed)

    def _run_single_episode(
        self, 
        tier: int, 
        threshold: float, 
        episode_id: int,
        graph: Any
    ) -> EpisodeResult:
        """
        Executes a single episode on a given graph with a specific threshold.
        
        Args:
            tier: The complexity tier of the graph.
            threshold: The routing threshold (0.0 to 1.0).
            episode_id: Unique ID for this episode.
            graph: The StateGraph instance to run on.
            
        Returns:
            EpisodeResult containing metrics for this episode.
        """
        # Initialize router for this episode with the specific threshold
        router = OPIDRouter(routing_threshold=threshold)
        
        # Reset policy state if needed
        self.policy.reset()
        
        current_node = graph.start
        trajectory = [current_node]
        total_log_prob_shift = 0.0
        actions_taken = []
        steps = 0
        max_steps = 1000  # Safety limit
        
        while current_node != graph.goal and steps < max_steps:
            # Get action from policy
            action_probs = self.policy.get_action_probs(current_node)
            
            # Determine if we should inject skill signal
            should_inject = router.should_inject(current_node)
            
            if should_inject:
                # Inject skill signal (log-probability shift)
                # This simulates the OPID mechanism by modifying action probabilities
                shift_amount = router.inject_skill_signal(current_node, action_probs)
                total_log_prob_shift += shift_amount
                
                # Update action probabilities based on injection
                # In a real implementation, this would modify the policy's logits
                # Here we simulate by adding a constant advantage to the goal-directed action
                goal_action_idx = router.get_goal_directed_action(current_node, graph)
                if goal_action_idx is not None and goal_action_idx < len(action_probs):
                    action_probs[goal_action_idx] += shift_amount
                    # Renormalize
                    action_probs = action_probs / np.sum(action_probs)
            
            # Sample action based on (possibly modified) probabilities
            action_idx = np.random.choice(len(action_probs), p=action_probs)
            actions_taken.append(action_idx)
            
            # Transition to next node
            next_node = graph.transition(current_node, action_idx)
            trajectory.append(next_node)
            current_node = next_node
            steps += 1

        # Calculate metrics
        success = (current_node == graph.goal)
        entropy = calculate_action_entropy(actions_taken) if actions_taken else 0.0
        
        return EpisodeResult(
            tier=tier,
            threshold=threshold,
            episode_id=episode_id,
            success=success,
            steps=steps,
            total_log_prob_shift=total_log_prob_shift,
            action_entropy=entropy,
            trajectory_length=len(trajectory)
        )

    def run_sweep(self) -> List[EpisodeResult]:
        """
        Executes the full experimental sweep across all tiers and thresholds.
        
        Returns:
            List of EpisodeResult objects for all executed episodes.
        """
        self.logger.info("Starting Experiment Sweep")
        self.logger.info(f"Configuration: {self.config}")
        
        all_results: List[EpisodeResult] = []
        output_file = os.path.join(self.config.output_dir, "episode_results.csv")
        
        # Open CSV file for writing
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['tier', 'threshold', 'episode_id', 'success', 'steps', 
                        'total_log_prob_shift', 'action_entropy', 'trajectory_length']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            total_episodes = (
                self.config.num_tiers * 
                len(self.config.thresholds) * 
                self.config.episodes_per_setting
            )
            self.logger.info(f"Total episodes to run: {total_episodes}")
            
            global_episode_id = 0
            
            for tier in range(1, self.config.num_tiers + 1):
                self.logger.info(f"Processing Tier {tier}")
                
                for threshold in self.config.thresholds:
                    self.logger.info(f"  Threshold: {threshold}")
                    
                    for ep_idx in range(self.config.episodes_per_setting):
                        # Generate a fresh graph for each episode to ensure independence
                        # This satisfies the requirement for real data generation
                        graph = self.graph_generator.generate(tier=tier, seed=get_seed() + global_episode_id)
                        
                        # Run the episode
                        result = self._run_single_episode(
                            tier=tier,
                            threshold=threshold,
                            episode_id=global_episode_id,
                            graph=graph
                        )
                        
                        all_results.append(result)
                        
                        # Write to CSV immediately to manage memory
                        writer.writerow({
                            'tier': result.tier,
                            'threshold': result.threshold,
                            'episode_id': result.episode_id,
                            'success': int(result.success),
                            'steps': result.steps,
                            'total_log_prob_shift': result.total_log_prob_shift,
                            'action_entropy': result.action_entropy,
                            'trajectory_length': result.trajectory_length
                        })
                        
                        global_episode_id += 1
                        
                        # Progress logging
                        if global_episode_id % 100 == 0:
                            self.logger.info(f"  Completed {global_episode_id}/{total_episodes} episodes")
        
        self.logger.info(f"Experiment sweep complete. Results written to {output_file}")
        return all_results


def main():
    """Entry point for running the experiment sweep."""
    # Initialize logger
    logger = get_experiment_logger("RunnerMain", level="INFO")
    
    # Load configuration from global constants
    seed = get_seed()
    num_tiers = 3  # Tiers 1, 2, 3 as per spec
    
    # Generate thresholds from 0.0 to 1.0 in steps of 0.1
    thresholds = [i * 0.1 for i in range(THRESHOLD_STEPS)]
    
    # Ensure we have the episodes per setting from config
    episodes_per_setting = EPISODES_PER_SETTING
    if episodes_per_setting is None:
        # Fallback if not set in config (should not happen if T004 is correct)
        logger.warning("EPISODES_PER_SETTING not set, using default 100")
        episodes_per_setting = 100
    
    config = RunnerConfig(
        seed=seed,
        num_tiers=num_tiers,
        thresholds=thresholds,
        episodes_per_setting=episodes_per_setting,
        output_dir="data/processed"
    )
    
    runner = ExperimentRunner(config)
    results = runner.run_sweep()
    
    logger.info(f"Total episodes executed: {len(results)}")
    logger.info("Experiment complete.")


if __name__ == "__main__":
    main()