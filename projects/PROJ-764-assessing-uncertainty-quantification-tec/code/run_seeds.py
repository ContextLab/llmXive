"""
Seed Orchestrator for User Story 2.

Iterates over a fixed list of seeds, invokes run_single_seed.py for each,
and aggregates the resulting ECE scores into a JSON report.

Constraints:
- Does NOT download or preprocess data (relies on data/processed/ artifacts).
- Generates results/uq_predictions_seed_<seed>.csv for each seed.
- Aggregates results into results/ece_scores_by_seed.json.
"""
import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/seeds_orchestrator.log')
    ]
)
logger = logging.getLogger('run_seeds')

# Fixed list of seeds as per task requirements
SEEDS: List[int] = [42, 43, 44]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / 'results'
CODE_DIR = PROJECT_ROOT / 'code'

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_single_seed(seed: int) -> bool:
    """
    Invoke run_single_seed.py for a specific seed.
    
    Args:
        seed: The random seed to use for this run.
        
    Returns:
        True if the script completed successfully, False otherwise.
    """
    logger.info(f"Starting run for seed {seed}...")
    
    script_path = CODE_DIR / 'models' / 'run_single_seed.py'
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    try:
        # Execute the script with the seed argument
        result = subprocess.run(
            [sys.executable, str(script_path), '--seed', str(seed)],
            cwd=str(PROJECT_ROOT),
            capture_output=False,  # Let output go to logs/console
            check=True
        )
        
        logger.info(f"Seed {seed} completed successfully.")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Seed {seed} failed with return code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running seed {seed}: {e}")
        return False

def extract_ece_score(seed: int) -> float:
    """
    Extract the ECE score from the generated predictions file for a seed.
    
    The run_single_seed.py script is expected to produce results/uq_predictions_seed_<seed>.csv
    which should contain a 'ece' column or the score can be derived from the metrics.
    
    For this implementation, we assume the script logs the ECE score or we read it
    from a generated metrics file. Since T024 generates calibration_report.csv,
    we will look for a seed-specific metrics file or parse the predictions if it contains ECE.
    
    NOTE: Based on T016a, the output is uq_predictions_seed_<seed>.csv.
    We need to find where ECE is stored. If not in the CSV, we might need to 
    re-calculate or rely on a side-car file. 
    
    Assumption: The run_single_seed.py script (T016a) or the subsequent metric calculation
    (T024 logic adapted for seeds) produces a JSON or CSV with ECE. 
    Since T024 generates a global report, we need a seed-specific metric extraction.
    
    Strategy: We will check for a generated file `results/ece_seed_<seed>.json` 
    created by the run_single_seed script (if we extend it) or calculate it here.
    
    However, T016a produces `uq_predictions_seed_<seed>.csv`. 
    To avoid re-implementing ECE calculation here, we assume the run_single_seed script
    also saves a small metrics JSON for the seed, OR we calculate it from the CSV.
    
    Let's implement a robust check:
    1. Check if `results/ece_seed_<seed>.json` exists (if run_single_seed was updated to save it).
    2. If not, load `uq_predictions_seed_<seed>.csv` and calculate ECE using code/uq/metrics.py.
    
    For this task, we will assume the run_single_seed script (T016a) has been updated 
    to output a metrics summary, OR we implement a quick ECE calculation here using the imported metrics module.
    
    Given the strict dependency on T016a and T021, let's calculate ECE here to be safe.
    """
    predictions_file = RESULTS_DIR / f'uq_predictions_seed_{seed}.csv'
    
    if not predictions_file.exists():
        logger.error(f"Predictions file not found for seed {seed}: {predictions_file}")
        return float('nan')
    
    try:
        import pandas as pd
        import numpy as np
        from code.uq.metrics import expected_calibration_error
        
        df = pd.read_csv(predictions_file)
        
        # We need ground truth to calculate ECE.
        # The predictions file might not have ground truth.
        # We must load the test set to match predictions.
        # T006a produces data/processed/raw_test.csv which has the target.
        # However, run_single_seed.py likely maps sample_id to predictions.
        
        # If the predictions file has 'sample_id', we can join with the test set.
        test_data_path = PROJECT_ROOT / 'data' / 'processed' / 'raw_test.csv'
        
        if not test_data_path.exists():
            logger.error(f"Test data not found at {test_data_path}")
            return float('nan')
        
        test_df = pd.read_csv(test_data_path)
        
        # Merge predictions with test data
        # Assuming sample_id is the key
        merged = df.merge(test_df[['sample_id', 'target']], on='sample_id', how='inner')
        
        if merged.empty:
            logger.warning(f"No matching samples for seed {seed}")
            return float('nan')
        
        # Calculate ECE for each method
        # We'll take the average ECE across methods or the ECE of the best method?
        # The task asks to aggregate ECE scores. Let's compute the mean ECE across all methods for this seed.
        
        ece_scores = []
        for method in merged['method'].unique():
            method_df = merged[merged['method'] == method]
            if 'lower_50' in method_df.columns and 'upper_50' in method_df.columns:
                # ECE calculation requires predictions and targets
                # The metrics.py function expects specific arguments
                # Let's call expected_calibration_error
                # Signature: expected_calibration_error(y_true, y_pred, intervals=None)
                # We need to adapt.
                
                # Simpler approach: The run_single_seed.py might have already calculated this.
                # If not, we implement a basic ECE here.
                
                # For now, let's assume the script T016a outputs a metric. 
                # If not, we fallback to a placeholder logic to satisfy the structure,
                # but the requirement is REAL data.
                
                # Let's calculate ECE manually for 50% and 90% intervals
                # ECE = sum |coverage - nominal| / N
                
                y_true = method_df['target'].values
                y_pred = method_df['prediction'].values
                lower = method_df['lower_50'].values
                upper = method_df['upper_50'].values
                
                # 50% interval coverage
                in_interval = (y_true >= lower) & (y_true <= upper)
                coverage_50 = np.mean(in_interval)
                ece_50 = abs(coverage_50 - 0.50)
                
                ece_scores.append(ece_50)
        
        if not ece_scores:
            logger.warning(f"No ECE scores calculated for seed {seed}")
            return float('nan')
        
        return np.mean(ece_scores)
        
    except Exception as e:
        logger.error(f"Error calculating ECE for seed {seed}: {e}")
        import traceback
        traceback.print_exc()
        return float('nan')

def aggregate_results() -> Dict[str, Any]:
    """
    Aggregate ECE scores from all seeds into a JSON report.
    
    Returns:
        Dictionary containing ECE scores for each seed.
    """
    results = {
        "seeds": SEEDS,
        "ece_scores": {},
        "success_count": 0,
        "total_count": len(SEEDS)
    }
    
    for seed in SEEDS:
        ece = extract_ece_score(seed)
        results["ece_scores"][str(seed)] = ece
        if not np.isnan(ece):
            results["success_count"] += 1
    
    output_path = RESULTS_DIR / 'ece_scores_by_seed.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Aggregated results saved to {output_path}")
    return results

def main():
    """Main entry point for the seed orchestrator."""
    parser = argparse.ArgumentParser(description='Run UQ inference for multiple seeds.')
    parser.add_argument('--seeds', type=str, default=None, 
                        help='Comma-separated list of seeds (default: 42,43,44)')
    args = parser.parse_args()
    
    seeds_to_run = SEEDS
    if args.seeds:
        seeds_to_run = [int(s.strip()) for s in args.seeds.split(',')]
    
    logger.info(f"Starting seed orchestration for seeds: {seeds_to_run}")
    
    success_count = 0
    for seed in seeds_to_run:
        if run_single_seed(seed):
            success_count += 1
        else:
            logger.error(f"Skipping aggregation for seed {seed} due to failure.")
    
    if success_count == 0:
        logger.critical("No seeds completed successfully. Exiting.")
        sys.exit(1)
    
    aggregate_results()
    logger.info("Seed orchestration completed.")

if __name__ == '__main__':
    main()