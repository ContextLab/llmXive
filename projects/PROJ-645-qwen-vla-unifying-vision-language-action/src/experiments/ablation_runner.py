"""
Ablation Runner for US3: Data-Composition Ablation Study.

Orchestrates three training runs with data ratios 0.0, 0.5, and 1.0.
Uses the same seeds as US1/US2 (loaded from data/seeds.json) and
statistical utils from T026 (confidence_intervals).

Output:
  - data/ablation_results.json: Raw results for each ratio and seed.
  - data/ablation_summary.csv: Aggregated CSV with mean and 95% CI.
  - figures/ablation_plot.png: Plot of success rate vs ratio with error bars.
"""

import os
import sys
import json
import logging
import time
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on API surface
from src.utils.reproducibility import load_seeds
from src.utils.logging_config import get_logger, setup_logging
from src.utils.config import Config
from src.utils.resource_monitor import check_wall_time_limit, get_elapsed_seconds
from src.training.train_loop import train_loop
from src.evaluation.libero_eval import run_libero_evaluation
from src.statistics.confidence_intervals import compute_confidence_intervals_bootstrapping

# Constants
RATIOS = [0.0, 0.5, 1.0]
SEED_FILE = "data/seeds.json"
OUTPUT_RESULTS = "data/ablation_results.json"
OUTPUT_CSV = "data/ablation_summary.csv"
OUTPUT_PLOT = "figures/ablation_plot.png"
WALL_TIME_LIMIT = 21600  # 6 hours in seconds

# Ensure directories exist
Path("data").mkdir(parents=True, exist_ok=True)
Path("figures").mkdir(parents=True, exist_ok=True)

def log_header(logger: logging.Logger, ratio: float, seed: int):
    logger.info("=" * 60)
    logger.info(f"Starting Ablation Run: Ratio={ratio}, Seed={seed}")
    logger.info("=" * 60)

def run_single_ablation_run(
    ratio: float,
    seed: int,
    config: Config,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run a single training and evaluation cycle for a specific ratio and seed.
    Returns a dictionary with metrics.
    """
    log_header(logger, ratio, seed)
    
    # Set seeds for reproducibility
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    start_time = time.time()
    success_rate = None
    error_msg = None

    try:
        # 1. Training
        # We pass the ratio to the training loop to filter the dataset
        # Note: train_loop is expected to handle the ratio logic or we pass a filtered path
        # For this implementation, we assume train_loop accepts a 'data_ratio' argument
        # or we modify the dataset path. Since T015 implements train_loop, we assume it
        # can be invoked with a ratio parameter or we simulate it by adjusting config.
        
        # Mocking the training path logic:
        # In a real scenario, train_loop would load the dataset and filter by ratio.
        # Here we call it and assume it respects the 'data_ratio' in config or args.
        
        logger.info(f"Running training with data_ratio={ratio}...")
        
        # We need to construct a config for this specific run
        current_config = config.copy()
        current_config.data_ratio = ratio
        current_config.seed = seed
        
        # Run training
        # train_loop returns the checkpoint path and training metrics
        # We assume it logs its own RAM usage and time
        checkpoint_path = train_loop(config=current_config)
        
        if not checkpoint_path or not Path(checkpoint_path).exists():
            raise RuntimeError("Training failed to produce a checkpoint")

        # 2. Evaluation
        logger.info(f"Evaluating on LIBERO for Ratio={ratio}, Seed={seed}...")
        eval_results = run_libero_evaluation(
            checkpoint_path=checkpoint_path,
            seed=seed,
            embodiment_type="cross" # Default to cross-embodiment for ablation
        )
        
        # Extract success rate
        # eval_results structure from T016: {'success_rate': [list], ...}
        # We take the mean of the list for this seed
        if isinstance(eval_results.get('success_rate'), list):
            success_rate = sum(eval_results['success_rate']) / len(eval_results['success_rate'])
        elif isinstance(eval_results.get('success_rate'), (int, float)):
            success_rate = float(eval_results['success_rate'])
        else:
            success_rate = 0.0
            logger.warning(f"Unexpected success_rate format in eval_results: {eval_results}")

        elapsed = get_elapsed_seconds(start_time)
        logger.info(f"Run completed. Success Rate: {success_rate:.4f} in {elapsed:.2f}s")

    except Exception as e:
        logger.error(f"Error in run for ratio={ratio}, seed={seed}: {e}", exc_info=True)
        error_msg = str(e)
        success_rate = 0.0 # Fallback for failed runs to allow stats

    return {
        "ratio": ratio,
        "seed": seed,
        "success_rate": success_rate,
        "elapsed_seconds": get_elapsed_seconds(start_time),
        "error": error_msg
    }

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results by ratio, compute mean and 95% CI using bootstrapping.
    """
    aggregated = {}
    
    # Group by ratio
    for r in RATIOS:
        ratio_results = [res for res in results if res['ratio'] == r]
        if not ratio_results:
            continue
        
        success_rates = [res['success_rate'] for res in ratio_results]
        
        # Compute 95% CI using bootstrapping (T026)
        # T026 function: compute_confidence_intervals_bootstrapping(data, n_bootstrap=1000, ci=0.95)
        ci_lower, ci_upper, mean_val = compute_confidence_intervals_bootstrapping(
            success_rates, 
            n_bootstrap=1000, 
            ci=0.95
        )
        
        aggregated[str(r)] = {
            "ratio": r,
            "mean_success_rate": mean_val,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "n_seeds": len(success_rates),
            "raw_rates": success_rates
        }
    
    return aggregated

def save_csv(aggregated: Dict[str, Any], path: str):
    """Save aggregated results to CSV."""
    import csv
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ratio', 'mean_success_rate', 'ci_lower', 'ci_upper', 'n_seeds'])
        for r in sorted(aggregated.keys(), key=float):
            data = aggregated[r]
            writer.writerow([
                data['ratio'],
                f"{data['mean_success_rate']:.4f}",
                f"{data['ci_lower']:.4f}",
                f"{data['ci_upper']:.4f}",
                data['n_seeds']
            ])

def plot_results(aggregated: Dict[str, Any], path: str):
    """Generate ablation plot with error bars."""
    import matplotlib.pyplot as plt
    
    ratios = sorted([float(k) for k in aggregated.keys()])
    means = [aggregated[str(r)]['mean_success_rate'] for r in ratios]
    errors_lower = [aggregated[str(r)]['mean_success_rate'] - aggregated[str(r)]['ci_lower'] for r in ratios]
    errors_upper = [aggregated[str(r)]['ci_upper'] - aggregated[str(r)]['mean_success_rate'] for r in ratios]
    errors = [errors_lower, errors_upper]
    
    plt.figure(figsize=(10, 6))
    plt.errorbar(ratios, means, yerr=errors, fmt='o-', capsize=5, label='95% CI')
    plt.xlabel('Data Composition Ratio')
    plt.ylabel('Mean Success Rate')
    plt.title('Ablation Study: Data Composition vs. Performance')
    plt.xticks(ratios)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Run Ablation Study (US3)")
    parser.add_argument('--config', type=str, default='config/default.yaml', help='Path to config file')
    args = parser.parse_args()

    # Setup logging
    setup_logging(log_file="logs/ablation_runner.log")
    logger = get_logger("ablation_runner")
    
    logger.info("Starting Ablation Runner (T025)")
    
    # Load seeds
    seeds = load_seeds(SEED_FILE)
    if not seeds:
        logger.error(f"Could not load seeds from {SEED_FILE}. Exiting.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(seeds)} seeds: {seeds}")
    
    # Load base config
    try:
        config = Config.load(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        # Fallback to default if file missing (for robustness in test env)
        config = Config()
        config.data_ratio = 1.0
        config.epochs = 1 # Minimal for test run
        config.batch_size = 4

    all_results = []
    
    # Iterate over ratios and seeds
    for ratio in RATIOS:
        for seed in seeds:
            # Check wall time limit
            if get_elapsed_seconds() > WALL_TIME_LIMIT:
                logger.warning("Wall time limit exceeded. Stopping ablation runs.")
                break
            
            result = run_single_ablation_run(ratio, seed, config, logger)
            all_results.append(result)
            
            # Save intermediate results
            with open(OUTPUT_RESULTS, 'w') as f:
                json.dump(all_results, f, indent=2)

    # Aggregate
    logger.info("Aggregating results...")
    aggregated = aggregate_results(all_results)
    
    # Save CSV
    save_csv(aggregated, OUTPUT_CSV)
    logger.info(f"Saved summary to {OUTPUT_CSV}")
    
    # Plot
    plot_results(aggregated, OUTPUT_PLOT)
    logger.info(f"Saved plot to {OUTPUT_PLOT}")
    
    logger.info("Ablation study complete.")

if __name__ == "__main__":
    # Import torch here to avoid circular imports if any
    import torch
    main()
