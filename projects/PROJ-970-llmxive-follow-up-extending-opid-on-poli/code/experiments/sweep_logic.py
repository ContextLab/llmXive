import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np
from experiments.runner import ExperimentRunner, ExperimentConfig
from utils.logging_setup import get_experiment_logger

@dataclass
class SweepConfig:
    """Configuration for the threshold sweep experiment."""
    min_threshold: float = 0.0
    max_threshold: float = 1.0
    step_size: float = 0.1
    tiers: List[int] = field(default_factory=lambda: [1, 2, 3])
    episodes_per_setting: int = 1000
    output_dir: str = "data/processed"

def generate_thresholds(config: SweepConfig) -> List[float]:
    """
    Generate the list of thresholds to sweep.
    Explicitly uses np.arange(0.0, 1.01, 0.1) to satisfy FR-006 (intervals of 0.1).
    """
    # Explicitly satisfy FR-006: intervals of 0.1 from 0.0 to 1.0
    thresholds = np.arange(config.min_threshold, config.max_threshold + config.step_size, config.step_size)
    # Round to avoid floating point artifacts (e.g. 0.30000000000000004)
    return [round(t, 1) for t in thresholds]

def run_sweep(config: SweepConfig, runner: ExperimentRunner, exp_cfg: ExperimentConfig) -> Dict[str, Any]:
    """
    Execute the full threshold sweep.
    
    Logic:
    1. Iterate thresholds across the full range (T023 requirement).
    2. For each threshold, iterate over tiers.
    3. For each (tier, threshold) pair, run the episode loop (T024).
    
    This structure enforces the loop over thresholds BEFORE the episode loop
    as required by the task specification.
    """
    logger = get_experiment_logger("sweep_logic")
    logger.info(f"Starting sweep with {len(config.tiers)} tiers and {len(generate_thresholds(config))} thresholds.")
    
    thresholds = generate_thresholds(config)
    all_results = []
    
    # T023: MUST enforce the loop over thresholds before the episode loop
    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")
        
        for tier in config.tiers:
            logger.info(f"  Running Tier {tier} at threshold {threshold}")
            
            # Configure runner for this specific setting
            current_cfg = exp_cfg.copy()
            current_cfg.tier = tier
            current_cfg.threshold = threshold
            current_cfg.episodes = config.episodes_per_setting
            
            # T024: Execute episode loop (delegated to runner.run_episodes)
            # The runner handles the `range(config.EPISODES_PER_SETTING)` loop internally
            episode_results = runner.run_episodes(current_cfg)
            
            # Aggregate results for this setting
            setting_summary = {
                "tier": tier,
                "threshold": threshold,
                "episode_count": len(episode_results),
                "results": episode_results
            }
            all_results.append(setting_summary)
            
    return {
        "config": asdict(config),
        "thresholds_used": thresholds,
        "results": all_results
    }

def main():
    """Entry point for running the sweep."""
    logging.basicConfig(level=logging.INFO)
    logger = get_experiment_logger("sweep_main")
    
    # Load or define config
    sweep_cfg = SweepConfig()
    
    # Initialize runner and experiment config
    # Note: In a real execution, these would be loaded from args or a config file
    runner = ExperimentRunner()
    exp_cfg = ExperimentConfig()
    
    # Run the sweep
    logger.info("Executing sweep...")
    results = run_sweep(sweep_cfg, runner, exp_cfg)
    
    # Log summary
    logger.info(f"Sweep complete. Total settings processed: {len(results['results'])}")
    return results

if __name__ == "__main__":
    main()