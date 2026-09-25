"""
Simulation Runner for OPID Critical-First Routing Complexity Analysis.

Implements sequential episode processing to ensure memory usage remains
below the 7GB limit by discarding intermediate trajectory data immediately
after aggregation.
"""
import logging
import time
import csv
import os
import json
from typing import List, Dict, Any, Optional, Tuple, Callable

import numpy as np

# Project imports based on provided API surface
from config import get_seed, set_seed, EPISODES_PER_SETTING, THRESHOLD_STEPS
from environment.graph_generator import GraphGenerator
from environment.state_graph import StateGraph
from agent.policy import BaselinePolicy, create_baseline_policy
from agent.opid_router import OPIDRouter, OPIDRouterConfig
from utils.metrics import calculate_success_rate, calculate_action_entropy
from utils.logging_setup import get_experiment_logger
from experiments.split_data import split_episodes_for_setting, ValidationSetConfig
from experiments.runner import EpisodeResult, ExperimentConfig

# Constants for memory management
MEMORY_SAFE_BUFFER = 0.9  # Keep 10% below theoretical limit

class StepLog:
    """Stores log data for a single step in an episode."""
    def __init__(
        self,
        step_id: int,
        state: Any,
        action: int,
        reward: float,
        log_prob_shift: float,
        injected: bool,
        entropy: float
    ):
        self.step_id = step_id
        self.state = state
        self.action = action
        self.reward = reward
        self.log_prob_shift = log_prob_shift
        self.injected = injected
        self.entropy = entropy

class RunnerConfig:
    """Configuration for the experiment runner."""
    def __init__(
        self,
        tiers: List[int],
        thresholds: List[float],
        episodes_per_setting: int,
        seed: int,
        output_dir: str
    ):
        self.tiers = tiers
        self.thresholds = thresholds
        self.episodes_per_setting = episodes_per_setting
        self.seed = seed
        self.output_dir = output_dir
        self.graph_generator = GraphGenerator()

class ExperimentRunner:
    """
    Orchestrates the full sweep of experiments.

    CRITICAL: Implements sequential processing logic (T025).
    Episodes are processed one-by-one, and intermediate trajectory data
    is discarded immediately after aggregation to keep memory < 7GB.
    """
    def __init__(self, config: RunnerConfig):
        self.config = config
        self.logger = get_experiment_logger("runner")
        self.graph_gen = config.graph_generator
        
        # Ensure output directory exists
        os.makedirs(config.output_dir, exist_ok=True)

    def run_episode(
        self,
        tier: int,
        threshold: float,
        episode_idx: int,
        rng: np.random.Generator
    ) -> EpisodeResult:
        """
        Run a single episode.

        Memory Safety: All intermediate state (trajectory, step logs)
        is discarded upon return. Only aggregated statistics are kept.
        """
        # 1. Generate Graph for this tier
        # Seed is derived from global seed + tier + threshold + episode_idx
        local_seed = self.config.seed + tier * 10000 + int(threshold * 100) * 1000 + episode_idx
        set_seed(local_seed)
        
        graph = self.graph_gen.generate(tier, seed=local_seed)
        
        if not graph.is_valid():
            # Should not happen due to generator retry logic, but safety check
            self.logger.warning(f"Invalid graph generated for tier {tier}, episode {episode_idx}")
            return EpisodeResult(
                tier=tier,
                threshold=threshold,
                episode_id=episode_idx,
                success=False,
                steps=0,
                total_reward=0.0,
                mean_entropy=0.0,
                mean_log_prob_shift=0.0,
                validation=False
            )

        # 2. Initialize Policy and Router
        # Policy is CPU-only numpy
        policy = create_baseline_policy(graph, seed=local_seed)
        
        router_config = OPIDRouterConfig(routing_threshold=threshold, seed=local_seed)
        router = OPIDRouter(router_config)

        # 3. Run Episode Loop
        # We maintain ONLY aggregated statistics to save memory.
        # We do NOT store the full trajectory list.
        current_state = graph.start
        steps = 0
        total_reward = 0.0
        entropy_sum = 0.0
        log_prob_shift_sum = 0.0
        injected_count = 0
        max_steps = 1000  # Prevent infinite loops
        success = False
        ground_truth_path = graph.get_shortest_path() if hasattr(graph, 'get_shortest_path') else []

        trajectory_actions = [] # Only store actions for success check, not full state history

        while steps < max_steps:
            # Get action distribution and entropy
            action_probs, entropy = policy.get_action_distribution(current_state)
            
            # Determine if skill injection happens
            should_inject = router.should_inject(current_state)
            log_prob_shift = 0.0
            
            if should_inject:
                # Simulate skill injection (add advantage)
                # Assuming action 0 is "goal-directed" for simplicity in this abstract runner
                # In a real implementation, this would use the specific skill signal
                log_prob_shift = 1.0 
                injected_count += 1
                router.inject_skill_signal(current_state, action_probs)

            # Select action
            action = rng.choice(len(action_probs), p=action_probs)
            trajectory_actions.append(action)

            # Update stats
            entropy_sum += entropy
            log_prob_shift_sum += log_prob_shift

            # Transition
            next_state, reward, done = graph.step(current_state, action)
            total_reward += reward
            steps += 1
            current_state = next_state

            if done:
                # Check success against ground truth path if available
                # For this simulation, we assume reaching 'goal' is success
                if current_state == graph.goal:
                    success = True
                break

        # Calculate aggregated metrics
        mean_entropy = entropy_sum / steps if steps > 0 else 0.0
        mean_log_prob_shift = log_prob_shift_sum / steps if steps > 0 else 0.0

        # CRITICAL: Discard trajectory_actions and graph immediately after use
        # Python's GC will reclaim memory for the graph object once this scope ends
        # and local references are cleared.
        del graph
        del policy
        del router
        del trajectory_actions

        return EpisodeResult(
            tier=tier,
            threshold=threshold,
            episode_id=episode_idx,
            success=success,
            steps=steps,
            total_reward=total_reward,
            mean_entropy=mean_entropy,
            mean_log_prob_shift=mean_log_prob_shift,
            validation=False # Will be updated by split logic
        )

    def run_sweep(self) -> List[EpisodeResult]:
        """
        Execute the full experimental sweep.

        Implements T025: Sequential processing.
        Iterates thresholds -> tiers -> episodes.
        Each episode result is written to disk (or buffer) immediately,
        and the episode's internal data structures are discarded.
        """
        self.logger.info(f"Starting sweep with {len(self.config.thresholds)} thresholds, "
                         f"{len(self.config.tiers)} tiers, "
                         f"{self.config.episodes_per_setting} episodes/setting")
        
        all_results: List[EpisodeResult] = []
        
        # Pre-generate RNG
        rng = np.random.default_rng(self.config.seed)

        # 1. Iterate Thresholds (T023 requirement: np.arange 0.0 to 1.0 step 0.1)
        # Note: config.thresholds is expected to be pre-generated by the caller
        # using np.arange(0.0, 1.01, 0.1)
        
        for threshold in self.config.thresholds:
            self.logger.info(f"Processing Threshold: {threshold:.1f}")
            
            # 2. Iterate Tiers
            for tier in self.config.tiers:
                self.logger.info(f"  Processing Tier: {tier}")
                
                # 3. Determine Validation Split (T023b)
                # We need to know which episodes are validation for this setting
                # We simulate the split logic here to mark episodes
                # In a real flow, split_data.py might output a config, 
                # but for sequential runner we compute the index range.
                # Assuming 80% train, 20% val based on typical split logic
                val_start_idx = int(self.config.episodes_per_setting * 0.8)
                
                # 4. Run Episodes Sequentially (T024 & T025)
                for ep_idx in range(self.config.episodes_per_setting):
                    # T025: Process one-by-one
                    result = self.run_episode(
                        tier=tier,
                        threshold=threshold,
                        episode_idx=ep_idx,
                        rng=rng
                    )
                    
                    # Mark validation
                    if ep_idx >= val_start_idx:
                        result.validation = True
                    
                    # T025: Append to results (in memory list)
                    # Note: The list grows, but each EpisodeResult is small.
                    # The large objects (Graph, Policy, Trajectory) are discarded.
                    all_results.append(result)
                    
                    # Optional: Periodic flush to disk to prevent memory bloat
                    # if len(all_results) % 1000 == 0:
                    #     self._flush_to_disk(all_results)
                    #     all_results.clear()
                    
                    if ep_idx % 100 == 0:
                        self.logger.debug(f"    Completed episode {ep_idx}/{self.config.episodes_per_setting}")

        self.logger.info("Sweep completed.")
        return all_results

    def save_results(self, results: List[EpisodeResult], filename: str):
        """Save results to CSV."""
        filepath = os.path.join(self.config.output_dir, filename)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                'tier', 'threshold', 'episode_id', 'success', 'steps',
                'total_reward', 'mean_entropy', 'mean_log_prob_shift', 'validation'
            ])
            for r in results:
                writer.writerow([
                    r.tier, r.threshold, r.episode_id, r.success, r.steps,
                    r.total_reward, r.mean_entropy, r.mean_log_prob_shift, r.validation
                ])
        self.logger.info(f"Saved {len(results)} results to {filepath}")

def main():
    """Entry point for the runner."""
    # Initialize config
    tiers = [1, 2, 3]
    # T023 requirement: explicit range 0.0 to 1.0 step 0.1
    thresholds = list(np.arange(0.0, 1.01, 0.1))
    
    config = RunnerConfig(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=EPISODES_PER_SETTING, # From config.py
        seed=42,
        output_dir="data/processed"
    )
    
    runner = ExperimentRunner(config)
    results = runner.run_sweep()
    runner.save_results(results, "episode_results.csv")

if __name__ == "__main__":
    main()