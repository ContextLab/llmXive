"""
Orchestrator for the full simulation batch.

This script coordinates the execution of Monte Carlo simulations across
multiple sample sizes, distributions, and statistical tests. It consumes
intermediate results from T021b (raw_pvalues.csv) and T021c (validation_report.csv)
and saves aggregated intermediate results to data/processed/.

Execution Order: T017b -> T018 -> T020-1 -> T020-2 -> T021b-0 -> T021b -> T021c -> T022
"""
import os
import sys
import csv
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import SimulationConfig, get_simulation_grid, get_test_grid
from simulation_engine import run_full_simulation_batch, validate_type_i_error_rates
from analyzer import load_simulation_results, aggregate_results
from utils.file_lock import file_lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simulation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    dirs = [
        'data/processed',
        'data/processed/plots',
        'logs'
    ]
    for dir_path in dirs:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {full_path}")

def verify_input_files():
    """Verify that required input files from T021b and T021c exist."""
    raw_pvalues_path = PROJECT_ROOT / 'data/processed' / 'raw_pvalues.csv'
    validation_report_path = PROJECT_ROOT / 'data/processed' / 'validation_report.csv'
    
    missing_files = []
    if not raw_pvalues_path.exists():
        missing_files.append(str(raw_pvalues_path))
    if not validation_report_path.exists():
        missing_files.append(str(validation_report_path))
        
    if missing_files:
        error_msg = f"Missing required input files: {', '.join(missing_files)}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info("All required input files verified.")

def run_full_batch():
    """
    Execute the full simulation batch across all configurations.
    
    This function:
    1. Verifies input files from T021b and T021c
    2. Runs the full simulation batch
    3. Saves intermediate results to data/processed/
    """
    ensure_output_dirs()
    verify_input_files()
    
    start_time = time.time()
    logger.info("Starting full simulation batch execution.")
    
    try:
        # Get simulation grids
        sample_sizes = [10, 20, 50, 100, 200, 500, 1000]
        distributions = ['normal', 'uniform', 'log_normal']
        test_types = ['t_test', 'anova', 'chi_squared']
        
        # Run the full simulation batch
        # This will reuse the simulation engine which already has access to
        # raw p-values from T021b and validation data from T021c
        results = run_full_simulation_batch(
            sample_sizes=sample_sizes,
            distributions=distributions,
            test_types=test_types,
            alpha=0.05,
            min_replicates=1000,
            max_replicates=10000,
            target_ci_width=0.01
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Full simulation batch completed in {elapsed_time:.2f} seconds.")
        
        # Save intermediate results
        save_intermediate_results(results)
        
        return results
        
    except Exception as e:
        logger.error(f"Error during simulation batch execution: {str(e)}", exc_info=True)
        raise

def save_intermediate_results(results: List[Dict[str, Any]]):
    """
    Save intermediate results to data/processed/.
    
    Args:
        results: List of simulation result dictionaries
    """
    if not results:
        logger.warning("No results to save.")
        return
    
    output_path = PROJECT_ROOT / 'data/processed' / 'intermediate_results.csv'
    
    try:
        with file_lock(output_path):
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if results:
                    # Get all unique keys from all results
                    all_keys = set()
                    for result in results:
                        all_keys.update(result.keys())
                    
                    # Define column order
                    columns = ['sample_size', 'distribution_type', 'test_type', 
                             'hypothesis_type', 'replicates', 'type_i_errors', 
                             'type_ii_errors', 'observed_error_rate', 'ci_lower', 
                             'ci_upper', 'ci_width', 'stable']
                    
                    # Write header
                    writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
                    writer.writeheader()
                    
                    # Write data
                    for result in results:
                        # Ensure all required fields are present with defaults
                        row = {col: result.get(col, None) for col in columns}
                        writer.writerow(row)
        
        logger.info(f"Intermediate results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving intermediate results: {str(e)}", exc_info=True)
        raise

def main():
    """Main entry point for the simulation orchestrator."""
    logger.info("=" * 60)
    logger.info("Starting T022: Simulation Orchestrator")
    logger.info("=" * 60)
    
    try:
        results = run_full_batch()
        
        if results:
            logger.info(f"Successfully processed {len(results)} simulation scenarios.")
            logger.info("Intermediate results saved to data/processed/intermediate_results.csv")
            logger.info("Pipeline execution completed successfully.")
            return 0
        else:
            logger.warning("No results were generated.")
            return 1
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())