import os
import sys
import csv
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field, asdict

from config import get_seed, set_seed, ensure_directories, get_tier_config
from utils.logging_setup import get_experiment_logger
from env.graph_generator import GraphGenerator, GraphGeneratorConfig
from agent.opid_router import OPIDRouter, OPIDRouterConfig
from agent.policy import BaselinePolicy, create_baseline_policy
from experiments.episode_runner import EpisodeRunner, EpisodeRunnerConfig
from utils.metrics import calculate_success_rate, calculate_raw_entropy, calculate_mean_entropy, calculate_variance

@dataclass
class EpisodeResult:
    tier: str
    threshold: float
    episode_id: int
    success: bool
    steps: int
    action_entropy_sum: float
    log_prob_shift_sum: float
    injection_count: int

@dataclass
class ExperimentConfig:
    tiers: List[str] = field(default_factory=lambda: ["Tier1", "Tier2", "Tier3"])
    thresholds: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    episodes_per_setting: int = 1000
    seed: int = 42
    output_dir: str = "data/processed"

class ExperimentRunner:
    """
    Orchestrates the full sweep of experiments across tiers and thresholds.
    
    CRITICAL: Implements sequential processing logic to ensure memory footprint < 7GB.
    Intermediate episode data is discarded immediately after aggregation.
    """
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.logger = get_experiment_logger("experiment_runner")
        self.output_dir = config.output_dir
        ensure_directories()
        
        # Pre-allocate minimal buffers for aggregation to avoid memory bloat
        self.agg_success_counts = {} # (tier, threshold) -> count
        self.agg_entropy_sums = {}   # (tier, threshold) -> sum
        self.agg_entropy_sq_sums = {} # (tier, threshold) -> sum of squares for variance
        self.agg_log_prob_sums = {}  # (tier, threshold) -> sum
        self.agg_injection_counts = {} # (tier, threshold) -> sum
        
        # Initialize aggregation dicts
        for tier in config.tiers:
            for thresh in config.thresholds:
                key = (tier, thresh)
                self.agg_success_counts[key] = 0
                self.agg_entropy_sums[key] = 0.0
                self.agg_entropy_sq_sums[key] = 0.0
                self.agg_log_prob_sums[key] = 0.0
                self.agg_injection_counts[key] = 0

    def _get_graph_generator(self, tier: str) -> GraphGenerator:
        """Instantiates a GraphGenerator for a specific tier."""
        tier_config = get_tier_config(tier)
        if not tier_config:
            raise ValueError(f"Invalid tier configuration: {tier}")
        
        gen_config = GraphGeneratorConfig(
            tier_name=tier,
            num_nodes=tier_config.get("num_nodes", 10),
            branching_prob=tier_config.get("branching_prob", 0.0),
            entropy_level=tier_config.get("entropy_level", "low"),
            seed=self.config.seed
        )
        return GraphGenerator(gen_config)

    def _run_single_episode(self, tier: str, threshold: float, episode_id: int, graph_gen: GraphGenerator) -> Optional[EpisodeResult]:
        """
        Runs a single episode and returns results.
        This function is designed to be lightweight and not retain large state.
        """
        try:
            # Generate graph on-the-fly for this episode to ensure diversity within tier
            # but deterministic based on seed + episode_id
            set_seed(self.config.seed + episode_id)
            state_graph = graph_gen.generate()
            
            # Initialize components
            router_config = OPIDRouterConfig(routing_threshold=threshold, seed=self.config.seed + episode_id)
            router = OPIDRouter(router_config)
            
            policy_config = BaselinePolicyConfig()
            policy = create_baseline_policy(policy_config)
            
            episode_runner_config = EpisodeRunnerConfig(
                state_graph=state_graph,
                router=router,
                policy=policy,
                max_steps=1000
            )
            runner = EpisodeRunner(episode_runner_config)
            
            # Execute episode
            result = runner.run()
            
            return EpisodeResult(
                tier=tier,
                threshold=threshold,
                episode_id=episode_id,
                success=result.success,
                steps=result.steps,
                action_entropy_sum=result.action_entropy_sum,
                log_prob_shift_sum=result.log_prob_shift_sum,
                injection_count=result.injection_count
            )
        except Exception as e:
            self.logger.error(f"Episode {episode_id} failed in {tier} at threshold {threshold}: {e}")
            return None

    def run_sweep(self):
        """
        Executes the full experimental sweep sequentially.
        
        Memory Management Strategy:
        1. Process (Tier, Threshold) pairs one by one.
        2. Inside each pair, process episodes one by one.
        3. Accumulate ONLY scalar aggregates (sums, counts).
        4. Discard individual EpisodeResult objects immediately after aggregation.
        5. Write final summary to disk only after all processing is complete.
        """
        self.logger.info("Starting sequential experiment sweep...")
        self.logger.info(f"Configuration: {len(self.config.tiers)} tiers, {len(self.config.thresholds)} thresholds, {self.config.episodes_per_setting} episodes/setting")
        
        episode_log_path = os.path.join(self.output_dir, "episode_results.csv")
        
        # Open CSV for appending to avoid loading history into memory
        with open(episode_log_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tier", "threshold", "episode_id", "success", "steps", "action_entropy_sum", "log_prob_shift_sum", "injection_count"])
            
            for tier in self.config.tiers:
                self.logger.info(f"Processing Tier: {tier}")
                graph_gen = self._get_graph_generator(tier)
                
                for threshold in self.config.thresholds:
                    self.logger.info(f"  -> Threshold: {threshold:.1f}")
                    key = (tier, threshold)
                    
                    for ep_id in range(self.config.episodes_per_setting):
                        result = self._run_single_episode(tier, threshold, ep_id, graph_gen)
                        
                        if result:
                            # Write to disk immediately (streaming log)
                            writer.writerow([
                                result.tier,
                                result.threshold,
                                result.episode_id,
                                result.success,
                                result.steps,
                                result.action_entropy_sum,
                                result.log_prob_shift_sum,
                                result.injection_count
                            ])
                            
                            # Aggregate scalars only
                            self.agg_success_counts[key] += 1 if result.success else 0
                            self.agg_entropy_sums[key] += result.action_entropy_sum
                            self.agg_entropy_sq_sums[key] += (result.action_entropy_sum ** 2)
                            self.agg_log_prob_sums[key] += result.log_prob_shift_sum
                            self.agg_injection_counts[key] += result.injection_count
                            
                            # Explicitly delete reference to allow GC to reclaim memory
                            del result
                        
                        # Optional: Log progress every 100 episodes
                        if (ep_id + 1) % 100 == 0:
                            self.logger.debug(f"    Completed {ep_id + 1}/{self.config.episodes_per_setting} episodes")
        
        self.logger.info("Sweep complete. Generating summary statistics...")
        self._generate_summary_stats()

    def _generate_summary_stats(self):
        """Calculates and writes summary statistics to disk."""
        summary_path = os.path.join(self.output_dir, "summary_stats.csv")
        
        with open(summary_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tier", "threshold", "success_rate", "mean_action_entropy", "action_entropy_variance", "mean_log_prob_shift", "total_injections"])
            
            for tier in self.config.tiers:
                for threshold in self.config.thresholds:
                    key = (tier, threshold)
                    n = self.agg_success_counts[key]
                    
                    if n == 0:
                        continue
                        
                    success_rate = self.agg_success_counts[key] / n
                    mean_entropy = self.agg_entropy_sums[key] / n
                    
                    # Variance = E[X^2] - (E[X])^2
                    mean_sq_entropy = self.agg_entropy_sq_sums[key] / n
                    variance_entropy = mean_sq_entropy - (mean_entropy ** 2)
                    
                    mean_log_prob = self.agg_log_prob_sums[key] / n
                    total_inj = self.agg_injection_counts[key]
                    
                    writer.writerow([
                        tier,
                        threshold,
                        f"{success_rate:.4f}",
                        f"{mean_entropy:.4f}",
                        f"{variance_entropy:.4f}",
                        f"{mean_log_prob:.4f}",
                        total_inj
                    ])
        
        self.logger.info(f"Summary stats written to {summary_path}")

def main():
    config = ExperimentConfig()
    runner = ExperimentRunner(config)
    runner.run_sweep()

if __name__ == "__main__":
    main()