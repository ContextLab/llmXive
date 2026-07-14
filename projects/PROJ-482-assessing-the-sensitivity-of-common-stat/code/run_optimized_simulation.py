"""
Optimized simulation runner for T033.
Ensures the full simulation suite completes within 6 hours on a 2-core CPU.
Implements parallel processing using multiprocessing and optimized batch logic.
"""
import os
import sys
import time
import logging
import multiprocessing as mp
from typing import List, Dict, Any, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime

# Import from project modules
from config import get_simulation_grid, SimulationConfig
from simulation_engine import run_adaptive_simulation, generate_scenario_data
from data_generator import generate_data
from setup_directories import ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_WORKERS = 2  # Constraint: 2 cores
OUTPUT_FILE = "data/processed/simulation_results_optimized.csv"

def get_scenario_id(scenario: Dict[str, Any]) -> str:
    """Generate a unique ID for a scenario."""
    return f"{scenario['test_type']}_{scenario['distribution']}_{scenario['n']}_{scenario['effect_size']}"

def run_scenario_worker(args: Tuple[Dict[str, Any], int]) -> Dict[str, Any]:
    """
    Worker function to run a single scenario.
    Must be picklable for multiprocessing.
    """
    scenario, seed = args
    scenario_id = get_scenario_id(scenario)
    logger.info(f"Starting scenario: {scenario_id}")
    
    try:
        # Run the simulation for this specific scenario
        results = run_adaptive_simulation(
            n=scenario['n'],
            distribution=scenario['distribution'],
            effect_size=scenario['effect_size'],
            test_type=scenario['test_type'],
            alpha=scenario['alpha'],
            min_replicates=scenario['min_replicates'],
            max_replicates=scenario['max_replicates'],
            target_ci_width=scenario['target_ci_width'],
            seed=seed
        )
        
        # Format results for CSV
        return {
            'scenario_id': scenario_id,
            'test_type': scenario['test_type'],
            'distribution': scenario['distribution'],
            'n': scenario['n'],
            'effect_size': scenario['effect_size'],
            'type_1_error_rate': results.get('type_1_error_rate', None),
            'type_2_error_rate': results.get('type_2_error_rate', None),
            'actual_replicates': results.get('actual_replicates', 0),
            'ci_width': results.get('ci_width', 0.0),
            'execution_time': results.get('execution_time', 0.0),
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Scenario {scenario_id} failed: {e}")
        return {
            'scenario_id': scenario_id,
            'test_type': scenario['test_type'],
            'distribution': scenario['distribution'],
            'n': scenario['n'],
            'effect_size': scenario['effect_size'],
            'type_1_error_rate': None,
            'type_2_error_rate': None,
            'actual_replicates': 0,
            'ci_width': 0.0,
            'execution_time': 0.0,
            'status': 'failed',
            'error': str(e)
        }

def run_full_optimized_batch() -> List[Dict[str, Any]]:
    """
    Orchestrates the full batch of simulations using multiprocessing.
    """
    start_time = time.time()
    logger.info("Starting optimized full batch simulation...")
    
    # Generate the grid of scenarios
    grid = get_simulation_grid()
    scenarios = []
    base_seed = 42
    
    for scenario in grid:
        scenarios.append((scenario, base_seed))
        base_seed += 1000  # Unique seed per scenario
    
    logger.info(f"Total scenarios to process: {len(scenarios)}")
    logger.info(f"Using {MAX_WORKERS} worker processes")
    
    results = []
    
    # Ensure output directory exists
    ensure_dir(os.path.dirname(OUTPUT_FILE))
    
    # Run simulations in parallel
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_scenario = {
            executor.submit(run_scenario_worker, args): args[0]['scenario_id']
            for args in scenarios
        }
        
        completed_count = 0
        total_count = len(scenarios)
        
        for future in as_completed(future_to_scenario):
            result = future.result()
            results.append(result)
            completed_count += 1
            
            if completed_count % 10 == 0 or completed_count == total_count:
                elapsed = time.time() - start_time
                eta = (elapsed / completed_count) * (total_count - completed_count) if completed_count > 0 else 0
                logger.info(f"Progress: {completed_count}/{total_count} ({100*completed_count/total_count:.1f}%) | "
                            f"Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s")
    
    total_time = time.time() - start_time
    logger.info(f"Batch completed in {total_time:.1f} seconds ({total_time/3600:.2f} hours)")
    
    return results

def save_optimized_results(results: List[Dict[str, Any]]) -> None:
    """
    Saves the simulation results to a CSV file.
    """
    if not results:
        logger.warning("No results to save.")
        return

    fieldnames = list(results[0].keys())
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results saved to {OUTPUT_FILE}")

def main():
    """
    Entry point for the optimized simulation runner.
    """
    try:
        results = run_full_optimized_batch()
        save_optimized_results(results)
        print(f"Optimization complete. Results written to {OUTPUT_FILE}")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
