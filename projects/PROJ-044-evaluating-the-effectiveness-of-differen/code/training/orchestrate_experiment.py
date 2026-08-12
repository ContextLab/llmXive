"""
Orchestration script for User Story 2 (DP-FL Training).
Implements the 5-seed loop mandated by FR-004.

Iterates through seeds and configurations, calling the FedAvg orchestrator,
and aggregates logs into a single CSV file.
"""
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config, get_default_config
from training.fedavg import run_experiment, FedAvgOrchestrator
from training.logging import ExperimentLogger, log_training_round
from data.partition import generate_and_save_partitions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'results' / 'orchestration.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants per FR-004 and spec
SEEDS = [42, 123, 456, 789, 101112]  # 5 seeds
EPSILONS = [0.1, 0.5, 1.0, 5.0, 10.0]
ALPHAS = [0.1, 0.5, 1.0]
DATASET = "femnist"
TARGET_ACCURACY = 0.85
MAX_ROUNDS = 100
NUM_CLIENTS = 100
CLIENT_SAMPLE_RATE = 0.1
BATCH_SIZE = 32
LEARNING_RATE = 0.01
NOISE_MULTIPLIER = 1.0  # Will be calculated based on epsilon

def run_single_configuration(seed: int, alpha: float, epsilon: float) -> Dict[str, Any]:
    """
    Run a single training configuration with a specific seed.
    
    Args:
        seed: Random seed for reproducibility
        alpha: Dirichlet concentration parameter
        epsilon: Privacy budget (epsilon)
        
    Returns:
        Dictionary containing training results and metadata
    """
    logger.info(f"Starting run: seed={seed}, alpha={alpha}, epsilon={epsilon}")
    
    try:
        # Initialize config
        config = get_default_config()
        config.seed = seed
        config.alpha = alpha
        config.epsilon = epsilon
        config.dataset = DATASET
        
        # Create experiment directory
        experiment_dir = project_root / 'results' / 'experiments' / f"seed{seed}_alpha{alpha}_eps{epsilon}"
        experiment_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate partitions for this specific configuration
        partition_dir = project_root / 'data' / 'partitions'
        partition_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating partitions for seed={seed}, alpha={alpha}")
        partition_metadata = generate_and_save_partitions(
            dataset_name=DATASET,
            seed=seed,
            alpha=alpha,
            output_dir=partition_dir,
            num_clients=NUM_CLIENTS
        )
        
        # Run the experiment
        logger.info(f"Running FedAvg experiment for seed={seed}, alpha={alpha}, epsilon={epsilon}")
        
        # Initialize orchestrator
        orchestrator = FedAvgOrchestrator(
            config=config,
            partition_metadata=partition_metadata,
            experiment_dir=experiment_dir
        )
        
        # Run training
        results = orchestrator.run(
            target_accuracy=TARGET_ACCURACY,
            max_rounds=MAX_ROUNDS,
            client_sample_rate=CLIENT_SAMPLE_RATE,
            batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE
        )
        
        # Extract key metrics
        final_accuracy = results.get('final_global_accuracy', 0.0)
        rounds_to_target = results.get('rounds_to_target', -1)
        is_time_limited = results.get('is_time_limited', False)
        is_utility_collapse = results.get('is_utility_collapse', False)
        privacy_budget_used = results.get('privacy_budget_used', epsilon)
        
        # Log to individual experiment log
        logger.info(f"Experiment completed: accuracy={final_accuracy:.4f}, "
                   f"rounds={rounds_to_target}, time_limited={is_time_limited}")
        
        return {
            'seed': seed,
            'alpha': alpha,
            'epsilon': epsilon,
            'global_accuracy': final_accuracy,
            'rounds_to_target': rounds_to_target,
            'is_time_limited': is_time_limited,
            'is_utility_collapse': is_utility_collapse,
            'privacy_budget_used': privacy_budget_used,
            'experiment_dir': str(experiment_dir),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Experiment failed for seed={seed}, alpha={alpha}, epsilon={epsilon}: {str(e)}")
        # Return failure record
        return {
            'seed': seed,
            'alpha': alpha,
            'epsilon': epsilon,
            'global_accuracy': 0.0,
            'rounds_to_target': -1,
            'is_time_limited': True,
            'is_utility_collapse': True,
            'privacy_budget_used': epsilon,
            'experiment_dir': str(experiment_dir) if 'experiment_dir' in locals() else '',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'error': str(e)
        }

def aggregate_logs(results_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Aggregate all experiment results into a single CSV file.
    
    Args:
        results_list: List of result dictionaries from each configuration
        output_path: Path to save the aggregated CSV
    """
    if not results_list:
        logger.warning("No results to aggregate")
        return
        
    df = pd.DataFrame(results_list)
    
    # Ensure proper column ordering
    columns = [
        'seed', 'alpha', 'epsilon', 'global_accuracy', 'rounds_to_target',
        'is_time_limited', 'is_utility_collapse', 'privacy_budget_used',
        'experiment_dir', 'timestamp', 'error'
    ]
    
    # Only include columns that exist in the dataframe
    available_columns = [col for col in columns if col in df.columns]
    df = df[available_columns]
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Aggregated results saved to {output_path} with {len(df)} rows")

def main():
    """
    Main orchestration function.
    Iterates through all seeds and configurations, runs experiments,
    and aggregates results.
    """
    logger.info("Starting experiment orchestration")
    logger.info(f"Seeds: {SEEDS}")
    logger.info(f"Epsilons: {EPSILONS}")
    logger.info(f"Alphas: {ALPHAS}")
    logger.info(f"Dataset: {DATASET}")
    
    # Ensure results directory exists
    results_dir = project_root / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    
    # Iterate through all configurations
    for seed in SEEDS:
        for alpha in ALPHAS:
            for epsilon in EPSILONS:
                logger.info(f"Running configuration: seed={seed}, alpha={alpha}, epsilon={epsilon}")
                
                # Run single configuration
                result = run_single_configuration(seed, alpha, epsilon)
                all_results.append(result)
                
                # Small delay to prevent overwhelming system
                time.sleep(1)
    
    # Aggregate all results
    output_csv = results_dir / 'raw_logs.csv'
    aggregate_logs(all_results, output_csv)
    
    logger.info(f"Orchestration complete. Total runs: {len(all_results)}")
    logger.info(f"Results saved to {output_csv}")
    
    # Print summary
    df = pd.DataFrame(all_results)
    if not df.empty:
        logger.info(f"Success rate: {len(df[df['is_time_limited'] == False]) / len(df) * 100:.1f}%")
        logger.info(f"Average accuracy: {df['global_accuracy'].mean():.4f}")
        logger.info(f"Average rounds to target: {df[df['rounds_to_target'] > 0]['rounds_to_target'].mean():.1f}")

if __name__ == "__main__":
    main()
