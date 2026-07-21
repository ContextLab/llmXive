"""
Optimized main entry point for the llmXive pipeline.
This script uses parallel processing and caching to ensure
completion within 6 hours on a CPU-only runner.
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/processed/optimization_run.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_project_structure():
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "models",
        "figures",
        "data/.cache"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def run_full_pipeline():
    """
    Execute the full pipeline with optimizations.
    Returns timing information.
    """
    start_time = time.time()
    timings = {}
    
    try:
        # Step 1: Parse trajectories (parallel)
        logger.info("Step 1: Parsing trajectories...")
        t0 = time.time()
        from perf_optimizer import parallel_parser
        raw_files = list(Path("data/raw").glob("*.json"))
        if not raw_files:
            logger.warning("No raw trajectory files found. Skipping parsing.")
            timings['parsing'] = 0
        else:
            trajectories = parallel_parser(raw_files)
            import pandas as pd
            all_data = pd.concat(trajectories, ignore_index=True)
            all_data.to_csv("data/processed/metrics_with_moves.csv", index=False)
            timings['parsing'] = time.time() - t0
            logger.info(f"Parsing completed in {timings['parsing']:.2f}s")
        
        # Step 2: Split data
        logger.info("Step 2: Splitting data...")
        t0 = time.time()
        from splitter import stratified_split, save_split_data
        if 'all_data' in locals():
            train_df, holdout_df = stratified_split(all_data)
            save_split_data(train_df, holdout_df, "data/processed")
            timings['splitting'] = time.time() - t0
            logger.info(f"Splitting completed in {timings['splitting']:.2f}s")
        else:
            logger.warning("No data to split. Skipping.")
            timings['splitting'] = 0
        
        # Step 3: Entropy calculation (parallel)
        logger.info("Step 3: Calculating entropy...")
        t0 = time.time()
        from perf_optimizer import parallel_entropy_calculation
        if 'all_data' in locals():
            entropies = parallel_entropy_calculation(all_data.to_dict('records'))
            all_data['entropy'] = entropies
            all_data.to_csv("data/processed/metrics_with_moves.csv", index=False)
            timings['entropy'] = time.time() - t0
            logger.info(f"Entropy calculation completed in {timings['entropy']:.2f}s")
        else:
            timings['entropy'] = 0
        
        # Step 4: Ablation study (optimized)
        logger.info("Step 4: Running ablation study...")
        t0 = time.time()
        from perf_optimizer import optimized_ablation_study
        ablation_config = {'k': 2, 'method': 'static_proxy'}
        if os.path.exists("data/processed/train_set.csv"):
            ablation_results = optimized_ablation_study(
                "data/processed/train_set.csv",
                ablation_config
            )
            import json
            with open("data/processed/ablation_labels_train.json", 'w') as f:
                json.dump(ablation_results, f, indent=2)
            timings['ablation'] = time.time() - t0
            logger.info(f"Ablation completed in {timings['ablation']:.2f}s")
        else:
            logger.warning("Training set not found. Skipping ablation.")
            timings['ablation'] = 0
        
        # Step 5: Train classifier
        logger.info("Step 5: Training classifier...")
        t0 = time.time()
        from classifier import run_training
        if os.path.exists("data/processed/ablation_labels_train.json"):
            run_training("data/processed/ablation_labels_train.json", "models/layer_utility_classifier.pkl")
            timings['training'] = time.time() - t0
            logger.info(f"Training completed in {timings['training']:.2f}s")
        else:
            logger.warning("Ablation results not found. Skipping training.")
            timings['training'] = 0
        
        # Step 6: Simulations (optimized)
        logger.info("Step 6: Running simulations...")
        t0 = time.time()
        from perf_optimizer import optimize_simulation_batch
        if os.path.exists("models/layer_utility_classifier.pkl"):
            # Use a subset for speed if dataset is large
            sample_size = min(100, len(all_data)) if 'all_data' in locals() else 100
            sample_data = all_data.head(sample_size).to_dict('records') if 'all_data' in locals() else []
            
            baseline_configs = [
                {'name': 'static_all', 'strategy': 'all_layers'},
                {'name': 'random_k2', 'strategy': 'random', 'k': 2}
            ]
            sim_results = optimize_simulation_batch(
                sample_data,
                "models/layer_utility_classifier.pkl",
                baseline_configs
            )
            # Save simulation results
            import json
            with open("data/processed/simulation_results.json", 'w') as f:
                json.dump(sim_results, f, indent=2)
            timings['simulation'] = time.time() - t0
            logger.info(f"Simulation completed in {timings['simulation']:.2f}s")
        else:
            logger.warning("Model not found. Skipping simulation.")
            timings['simulation'] = 0
        
        # Step 7: Statistical analysis
        logger.info("Step 7: Running statistical analysis...")
        t0 = time.time()
        from perf_optimizer import vectorized_statistical_tests
        if os.path.exists("data/processed/simulation_results.json"):
            import json
            with open("data/processed/simulation_results.json", 'r') as f:
                sim_data = json.load(f)
            
            dynamic_wins = [r['win'] for r in sim_data['dynamic']]
            static_wins = [r['win'] for r in sim_data['baselines']['static_all']]
            dynamic_tokens = [r['tokens'] for r in sim_data['dynamic']]
            static_tokens = [r['tokens'] for r in sim_data['baselines']['static_all']]
            
            stats_results = vectorized_statistical_tests(
                dynamic_wins, static_wins, dynamic_tokens, static_tokens
            )
            with open("data/processed/statistical_results.json", 'w') as f:
                json.dump(stats_results, f, indent=2)
            timings['statistics'] = time.time() - t0
            logger.info(f"Statistics completed in {timings['statistics']:.2f}s")
        else:
            logger.warning("Simulation results not found. Skipping statistics.")
            timings['statistics'] = 0
        
        # Final timing
        total_time = time.time() - start_time
        timings['total'] = total_time
        
        # Save timing report
        with open("data/processed/optimization_timing_report.json", 'w') as f:
            json.dump(timings, f, indent=2)
        
        logger.info("=" * 50)
        logger.info(f"Pipeline completed in {total_time:.2f} seconds ({total_time/3600:.2f} hours)")
        logger.info("=" * 50)
        
        return timings
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

def main():
    """Main entry point."""
    logger.info(f"Starting optimized pipeline at {datetime.now()}")
    ensure_project_structure()
    timings = run_full_pipeline()
    
    # Verify 6-hour constraint
    if timings['total'] <= 6 * 3600:
        logger.info("SUCCESS: Completed within 6-hour limit")
        return 0
    else:
        logger.error("FAILURE: Exceeded 6-hour limit")
        return 1

if __name__ == "__main__":
    sys.exit(main())
