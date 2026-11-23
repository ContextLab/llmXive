"""
Orchestrator for running the full DP-FL experiment across multiple seeds and configurations.

This script implements the 5-seed orchestration loop mandated by FR-004.
It iterates through seeds and configurations, calling the training logic,
and aggregates logs into results/raw_logs.csv.

Dependency: T018b (DP Integration)
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from existing project modules
from config import Config, get_default_config
from training.fedavg import run_experiment
from training.logging import ExperimentLogger, TrainingMetrics
from data.partition import partition_femnist
from data.generate_partition_metadata import generate_metadata_for_configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/experiment_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEEDS = [42, 123, 456, 789, 101112]
DEFAULT_ALPHAS = [0.1, 0.5, 1.0]
DEFAULT_EPSILONS = [0.1, 1.0, 10.0]  # Including high epsilon for non-DP approximation
RESULTS_DIR = Path("results")
RAW_LOGS_FILE = RESULTS_DIR / "raw_logs.csv"

def ensure_results_directory():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_single_seed_configuration(
    seed: int,
    alpha: float,
    epsilon: float,
    config: Config
) -> Optional[Dict[str, Any]]:
    """
    Run a single experiment configuration for a specific seed.

    Args:
        seed: Random seed for reproducibility
        alpha: Dirichlet distribution parameter
        epsilon: Privacy budget
        config: Base configuration object

    Returns:
        Dictionary containing results metrics or None if failed
    """
    logger.info(f"Starting run: seed={seed}, alpha={alpha}, epsilon={epsilon}")
    start_time = time.time()

    try:
        # Create a modified config for this specific run
        run_config = Config(
            seed=seed,
            alpha=alpha,
            epsilon=epsilon,
            dataset=config.dataset
        )

        # Step 1: Partition data for this seed and alpha
        logger.info(f"Partitioning data for seed={seed}, alpha={alpha}")
        partition_femnist(
            seed=seed,
            alpha=alpha,
            dataset_name=config.dataset,
            data_dir=Path("data/raw"),
            output_dir=Path("data/partitions")
        )

        # Step 2: Generate metadata
        logger.info(f"Generating metadata for seed={seed}, alpha={alpha}")
        generate_metadata_for_configuration(
            seed=seed,
            alpha=alpha,
            dataset_name=config.dataset,
            output_dir=Path("data/partitions")
        )

        # Step 3: Run the training experiment
        logger.info(f"Running training for seed={seed}, alpha={alpha}, epsilon={epsilon}")
        metrics = run_experiment(run_config)

        if metrics is None:
            logger.warning(f"Training returned None for seed={seed}, alpha={alpha}, epsilon={epsilon}")
            return None

        # Add configuration metadata to metrics
        metrics['seed'] = seed
        metrics['alpha'] = alpha
        metrics['epsilon'] = epsilon
        metrics['dataset'] = config.dataset
        metrics['run_duration_seconds'] = time.time() - start_time

        logger.info(f"Completed run: seed={seed}, alpha={alpha}, epsilon={epsilon}, "
                    f"accuracy={metrics.get('final_global_accuracy', 'N/A')}")
        return metrics

    except Exception as e:
        logger.error(f"Error during run (seed={seed}, alpha={alpha}, epsilon={epsilon}): {e}", exc_info=True)
        # Return a failure record
        return {
            'seed': seed,
            'alpha': alpha,
            'epsilon': epsilon,
            'dataset': config.dataset,
            'final_global_accuracy': None,
            'final_minority_accuracy': None,
            'final_majority_accuracy': None,
            'rounds_to_target': None,
            'is_time_limited': True,
            'is_utility_collapse': True,
            'run_duration_seconds': time.time() - start_time,
            'error': str(e)
        }

def aggregate_logs(all_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate all result dictionaries into a single DataFrame.

    Args:
        all_results: List of result dictionaries from individual runs

    Returns:
        DataFrame containing all results
    """
    if not all_results:
        logger.warning("No results to aggregate")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)

    # Ensure consistent column ordering
    preferred_columns = [
        'seed', 'alpha', 'epsilon', 'dataset',
        'final_global_accuracy', 'final_minority_accuracy', 'final_majority_accuracy',
        'rounds_to_target', 'is_time_limited', 'is_utility_collapse',
        'run_duration_seconds', 'error'
    ]

    # Reorder columns if they exist
    existing_cols = [col for col in preferred_columns if col in df.columns]
    other_cols = [col for col in df.columns if col not in preferred_columns]
    df = df[existing_cols + other_cols]

    return df

def main():
    """Main entry point for the experiment orchestrator."""
    parser = argparse.ArgumentParser(description="Orchestrate DP-FL experiment across seeds and configurations")
    parser.add_argument('--seeds', type=int, nargs='+', default=DEFAULT_SEEDS,
                        help=f'List of random seeds (default: {DEFAULT_SEEDS})')
    parser.add_argument('--alphas', type=float, nargs='+', default=DEFAULT_ALPHAS,
                        help=f'List of alpha values (default: {DEFAULT_ALPHAS})')
    parser.add_argument('--epsilons', type=float, nargs='+', default=DEFAULT_EPSILONS,
                        help=f'List of epsilon values (default: {DEFAULT_EPSILONS})')
    parser.add_argument('--dataset', type=str, default='femnist',
                        help='Dataset name (default: femnist)')
    parser.add_argument('--output', type=str, default=str(RAW_LOGS_FILE),
                        help=f'Output CSV file path (default: {RAW_LOGS_FILE})')

    args = parser.parse_args()

    # Validate dataset
    if args.dataset != 'femnist':
        logger.error(f"Dataset '{args.dataset}' is not supported. Only 'femnist' is allowed per T000.")
        sys.exit(1)

    logger.info("Starting experiment orchestration")
    logger.info(f"Seeds: {args.seeds}")
    logger.info(f"Alphas: {args.alphas}")
    logger.info(f"Epsilons: {args.epsilons}")
    logger.info(f"Dataset: {args.dataset}")

    ensure_results_directory()

    # Load base config
    base_config = get_default_config()
    base_config.dataset = args.dataset

    all_results = []
    total_runs = len(args.seeds) * len(args.alphas) * len(args.epsilons)
    current_run = 0

    for seed in args.seeds:
        for alpha in args.alphas:
            for epsilon in args.epsilons:
                current_run += 1
                logger.info(f"Run {current_run}/{total_runs}: seed={seed}, alpha={alpha}, epsilon={epsilon}")

                result = run_single_seed_configuration(seed, alpha, epsilon, base_config)
                if result:
                    all_results.append(result)

                # Optional: Add a small delay between runs to avoid resource contention
                # time.sleep(1)

    # Aggregate and save results
    logger.info(f"Aggregating {len(all_results)} results")
    df_results = aggregate_logs(all_results)

    if not df_results.empty:
        output_path = Path(args.output)
        df_results.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
        logger.info(f"Summary:\n{df_results.describe()}")
    else:
        logger.warning("No results were generated. Output file not created.")

    logger.info("Experiment orchestration completed")
    return 0 if not df_results.empty else 1

if __name__ == "__main__":
    sys.exit(main())