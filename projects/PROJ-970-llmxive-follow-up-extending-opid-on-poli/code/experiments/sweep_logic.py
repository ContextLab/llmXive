"""
Sweep Logic Implementation for OPID Critical-First Routing Complexity Analysis.

This module implements the threshold sweep logic required for User Story 3 (T023).
It iterates through thresholds from 0.0 to 1.0 in steps of 0.1 to satisfy FR-006
sensitivity analysis requirements.

It integrates with the existing ExperimentRunner to orchestrate the full sweep.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from experiments.runner import ExperimentRunner, ExperimentConfig
from utils.logging_setup import get_experiment_logger
from config import get_seed, set_seed, ensure_directories

# Configure logger
logger = get_experiment_logger(__name__)

@dataclass
class SweepConfig:
    """Configuration for the threshold sweep."""
    start_threshold: float = 0.0
    end_threshold: float = 1.0
    step_size: float = 0.1
    episodes_per_config: int = 1000
    seed: int = 42

def generate_thresholds(config: SweepConfig) -> List[float]:
    """
    Generate a list of thresholds from start to end with the specified step size.
    
    Args:
        config: SweepConfig containing start, end, and step parameters.
        
    Returns:
        List of float thresholds.
    """
    thresholds = []
    current = config.start_threshold
    # Use a small epsilon to handle floating point precision issues
    # ensuring we include the end_threshold if it's within rounding error
    epsilon = 1e-9
    while current <= config.end_threshold + epsilon:
        thresholds.append(round(current, 2))
        current += config.step_size
    return thresholds

def run_sweep(
    runner: ExperimentRunner,
    sweep_config: SweepConfig,
    tier_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Execute the full threshold sweep across specified tiers.
    
    This function implements the core sweep logic (T023) by iterating through
    thresholds and orchestrating episode execution for each (Tier, Threshold)
    combination.
    
    Args:
        runner: Initialized ExperimentRunner instance.
        sweep_config: Configuration for the sweep parameters.
        tier_ids: Optional list of tier IDs to run. If None, runs all available tiers.
        
    Returns:
        List of summary dictionaries for each (Tier, Threshold) configuration.
    """
    # Ensure output directories exist
    ensure_directories()
    
    thresholds = generate_thresholds(sweep_config)
    logger.info(f"Starting sweep with {len(thresholds)} thresholds: {thresholds}")
    
    # Determine which tiers to process
    # We assume the runner has access to tier definitions or we iterate 1-3 based on project spec
    if tier_ids is None:
        tier_ids = [1, 2, 3]  # Deterministic, Stochastic, High-Entropy
    
    all_results = []
    
    for tier_id in tier_ids:
        logger.info(f"Processing Tier {tier_id}...")
        
        for threshold in thresholds:
            logger.info(f"  Running Tier {tier_id} at threshold {threshold:.1f}")
            
            # Set seed for reproducibility for this specific config
            set_seed(sweep_config.seed)
            
            # Update runner config with current threshold
            # We create a new config instance for this run to avoid mutation issues
            current_config = ExperimentConfig(
                tier_id=tier_id,
                threshold=threshold,
                num_episodes=sweep_config.episodes_per_config,
                seed=sweep_config.seed
            )
            
            # Run the experiment for this specific configuration
            # The runner handles the episode loop internally (T024)
            # and returns aggregated results
            try:
                result = runner.run_experiment(current_config)
                result['tier_id'] = tier_id
                result['threshold'] = threshold
                all_results.append(result)
                logger.info(f"    Completed: Success Rate={result.get('success_rate', 'N/A'):.4f}")
            except Exception as e:
                logger.error(f"    FAILED at Tier {tier_id}, Threshold {threshold}: {str(e)}")
                # Log failure but continue to next threshold
                continue
    
    logger.info(f"Sweep complete. Total configurations processed: {len(all_results)}")
    return all_results

def main():
    """
    Main entry point for running the sweep logic independently.
    """
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize runner with default config
    # In a real scenario, this would be loaded from config files
    runner_config = ExperimentConfig(
        tier_id=1,  # Placeholder, overridden in loop
        threshold=0.0,  # Placeholder, overridden in loop
        num_episodes=1000,
        seed=42
    )
    
    runner = ExperimentRunner(runner_config)
    
    sweep_config = SweepConfig(
        start_threshold=0.0,
        end_threshold=1.0,
        step_size=0.1,
        episodes_per_config=1000,
        seed=42
    )
    
    results = run_sweep(runner, sweep_config)
    
    # Log summary
    logger.info(f"Generated {len(results)} result entries across all tiers and thresholds")
    
    return results

if __name__ == "__main__":
    main()