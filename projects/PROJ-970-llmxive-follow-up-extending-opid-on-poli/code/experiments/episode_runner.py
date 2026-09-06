"""
Implementation of Task T024: Episode Loop for Statistical Power.

Executes exactly 1,000 simulated episodes per (Tier, Threshold) combination.
This module satisfies FR-003 statistical power requirements.
"""
import os
import sys
import csv
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Local imports from API surface
from config import get_seed, set_seed, get_tier_config, ensure_directories
from env.graph_generator import GraphGenerator, GraphGenerationConfig
from env.graph_validator import GraphValidator, regenerate_graph_if_invalid
from agent.opid_router import OPIDRouter, OPIDRouterConfig
from agent.policy import BaselinePolicy, create_baseline_policy
from experiments.runner import EpisodeResult, ExperimentConfig
from utils.logging_setup import get_experiment_logger

@dataclass
class EpisodeRunnerConfig:
    """Configuration for the episode execution loop."""
    episodes_per_setting: int = 1000
    seed: int = 42
    output_dir: str = "data/processed"
    output_filename: str = "episode_results.csv"

class EpisodeRunner:
    """
    Executes the core simulation loop for T024.
    
    Responsible for:
    1. Iterating over Tiers and Thresholds.
    2. Generating valid graphs for each setting.
    3. Running exactly N episodes (default 1000) per setting.
    4. Collecting EpisodeResult data for downstream analysis.
    """
    
    def __init__(self, config: EpisodeRunnerConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or get_experiment_logger("episode_runner")
        self.validator = GraphValidator()
        
        # Ensure output directory exists
        ensure_directories()
        self.output_path = os.path.join(self.config.output_dir, self.config.output_filename)
        
        # Prepare CSV header
        self.fieldnames = [
            "tier_id", "threshold", "episode_id", "seed", 
            "success", "steps", "final_entropy", "log_prob_shift",
            "path_traversed", "graph_nodes", "graph_edges"
        ]

    def _generate_graph_for_setting(self, tier_id: int, threshold: float) -> Tuple[Any, int]:
        """
        Generates a valid StateGraph for a specific Tier.
        
        Returns:
            Tuple of (StateGraph, node_count)
        """
        set_seed(self.config.seed)
        tier_cfg = get_tier_config(tier_id)
        
        # Use a deterministic seed for graph generation based on tier and threshold
        # to ensure reproducibility across runs for the same setting
        graph_seed = self.config.seed + int(threshold * 1000000)
        set_seed(graph_seed)
        
        gen_config = GraphGenerationConfig(
            tier_id=tier_id,
            seed=graph_seed,
            **tier_cfg
        )
        
        generator = GraphGenerator(gen_config)
        graph = generator.generate()
        
        # Validate and regenerate if necessary
        validation = self.validator.validate(graph)
        if not validation.is_valid:
            self.logger.warning(
                f"Graph for Tier {tier_id}, Threshold {threshold} invalid. "
                f"Regenerating with adjusted seed."
            )
            graph = regenerate_graph_if_invalid(graph, self.validator, generator, max_attempts=5)
        
        return graph, len(graph.nodes)

    def run_single_episode(
        self, 
        graph: Any, 
        router: OPIDRouter, 
        policy: BaselinePolicy, 
        episode_id: int
    ) -> EpisodeResult:
        """
        Executes a single episode on the provided graph.
        
        Returns:
            EpisodeResult containing success, steps, and metrics.
        """
        # Reset environment state (conceptual, as graph is static but agent state changes)
        current_node_id = graph.start_node_id
        steps = 0
        path = [current_node_id]
        log_prob_shift = 0.0
        total_entropy = 0.0
        
        # Simulate episode
        while current_node_id != graph.goal_node_id and steps < 1000:
            # Get available actions (neighbors)
            neighbors = graph.get_neighbors(current_node_id)
            
            if not neighbors:
                # Dead end (should be caught by validator, but safe guard)
                break
            
            # Policy action selection
            action_probs, entropy = policy.get_action_probs(neighbors)
            total_entropy += entropy
            
            # Router decision: Critical-First Routing
            # The router determines if we inject hindsight skill or follow baseline
            # This is the core logic from T017-T021
            injection_signal = router.should_inject(current_node_id, steps)
            
            if injection_signal:
                # Inject skill: modify probabilities or force specific action
                # For this implementation, we simulate the shift
                # In a real scenario, this would interact with the distillation signal
                shifted_probs = router.apply_skill_injection(action_probs, neighbors)
                log_prob_shift += abs(sum(shifted_probs) - sum(action_probs)) # Simplified shift metric
                action_probs = shifted_probs
            
            # Sample action (next node)
            next_node_id = policy.sample_action(neighbors, action_probs)
            
            # Transition
            current_node_id = next_node_id
            path.append(current_node_id)
            steps += 1

        success = (current_node_id == graph.goal_node_id)
        avg_entropy = total_entropy / steps if steps > 0 else 0.0
        
        return EpisodeResult(
            success=success,
            steps=steps,
            final_entropy=avg_entropy,
            log_prob_shift=log_prob_shift,
            path_traversed=path,
            success_path_length=len(path)
        )

    def run_setting_sweep(
        self, 
        tier_id: int, 
        thresholds: List[float]
    ) -> List[EpisodeResult]:
        """
        Runs the 1,000 episode loop for a specific Tier across all thresholds.
        """
        all_results = []
        self.logger.info(f"Starting sweep for Tier {tier_id} with {self.config.episodes_per_setting} episodes per threshold.")
        
        for threshold in thresholds:
            self.logger.info(f"  Processing Threshold: {threshold:.2f}")
            
            # 1. Generate Graph (once per threshold setting for consistency)
            graph, node_count = self._generate_graph_for_setting(tier_id, threshold)
            
            # 2. Initialize Components
            # Router config depends on threshold
            router_config = OPIDRouterConfig(routing_threshold=threshold)
            router = OPIDRouter(router_config)
            
            policy = create_baseline_policy()
            
            # 3. Execute Episodes
            for ep_id in range(self.config.episodes_per_setting):
                # Set seed for episode randomness
                set_seed(self.config.seed + tier_id * 10000 + int(threshold * 1000000) + ep_id)
                
                result = self.run_single_episode(graph, router, policy, ep_id)
                
                # Annotate result with context for CSV
                result.metadata = {
                    "tier_id": tier_id,
                    "threshold": threshold,
                    "episode_id": ep_id,
                    "graph_nodes": node_count
                }
                
                all_results.append(result)
                
                if (ep_id + 1) % 100 == 0:
                    self.logger.debug(f"    Completed {ep_id + 1}/{self.config.episodes_per_setting} episodes")
                    
        return all_results

    def run_full_experiment(self, tiers: List[int], thresholds: List[float]) -> str:
        """
        Orchestrates the full experiment: Tier x Threshold x 1000 Episodes.
        
        Returns:
            Path to the generated CSV file.
        """
        self.logger.info("Starting Full Episode Loop Execution (T024)")
        self.logger.info(f"Configuration: {self.config.episodes_per_setting} episodes per (Tier, Threshold)")
        
        all_results: List[EpisodeResult] = []
        
        for tier_id in tiers:
            results = self.run_setting_sweep(tier_id, thresholds)
            all_results.extend(results)
        
        # Write results to CSV
        self._write_results_to_csv(all_results)
        
        self.logger.info(f"Experiment complete. Results written to {self.output_path}")
        return self.output_path

    def _write_results_to_csv(self, results: List[EpisodeResult]):
        """Writes the episode results to the CSV file."""
        with open(self.output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            
            for res in results:
                row = {
                    "tier_id": res.metadata.get("tier_id"),
                    "threshold": res.metadata.get("threshold"),
                    "episode_id": res.metadata.get("episode_id"),
                    "seed": get_seed(),
                    "success": 1 if res.success else 0,
                    "steps": res.steps,
                    "final_entropy": res.final_entropy,
                    "log_prob_shift": res.log_prob_shift,
                    "path_traversed": len(res.path_traversed),
                    "graph_nodes": res.metadata.get("graph_nodes")
                }
                writer.writerow(row)

def main():
    """
    Entry point for T024 execution.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = get_experiment_logger("t024_main")
    
    # Configuration
    # Tiers defined in spec: 1 (Deterministic), 2 (Stochastic), 3 (High-Entropy)
    tiers = [1, 2, 3]
    
    # Thresholds: 0.0 to 1.0 in steps of 0.1 (T023)
    thresholds = [i * 0.1 for i in range(11)]
    
    config = EpisodeRunnerConfig(
        episodes_per_setting=1000,
        seed=42,
        output_dir="data/processed",
        output_filename="episode_results.csv"
    )
    
    runner = EpisodeRunner(config, logger)
    output_file = runner.run_full_experiment(tiers, thresholds)
    
    logger.info(f"SUCCESS: Generated {output_file}")
    print(f"Task T024 Complete: {output_file}")

if __name__ == "__main__":
    main()
