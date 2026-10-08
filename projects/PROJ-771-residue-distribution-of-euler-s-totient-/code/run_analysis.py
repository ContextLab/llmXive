"""
Orchestration module for the Euler Totient Residue Distribution Analysis.

This module separates the orchestration logic (CLI parsing, seed pinning,
pipeline execution flow) from the domain-specific logic (sieve, stats,
visualization) which resides in their respective modules.

Entry Point:
    python code/run_analysis.py [--N <int>] [--primes <list>] [--seed <int>]
"""
import os
import sys
import argparse
import logging
import random
import time
from typing import List, Dict, Any, Optional

# Import orchestration utilities and domain modules
from config import load_config, create_argument_parser, parse_cli_args
from sieve import (
    MemoryGuard,
    compute_phi_linear_sieve,
    compute_residues,
    save_residue_dataset,
    pin_random_seed,
    log_error
)
from stats import (
    run_full_statistical_analysis,
    save_statistical_result,
    determine_primary_pass_fail,
    determine_bonferroni_pass_fail
)
from visualize import (
    load_residue_data,
    plot_bar_frequencies,
    plot_residual_qq,
    annotate_theoretical_bounds,
    generate_visualization_report
)
from benchmark_runner import run_benchmark, get_memory_usage_mb
from exceptions import FatalSieveError, ResearchIncompleteError, BenchmarkFailure
from constants import get_error_bound_constants

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/reports/analysis.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def pin_orchestration_seed(config: Dict[str, Any]) -> None:
    """
    Pin global random seeds for deterministic execution.
    
    Args:
        config: Configuration dictionary containing 'seed' key.
    """
    seed = config.get('seed', 42)
    random.seed(seed)
    # numpy is imported in stats/visualize, seed will be pinned there too
    # but we pin the python stdlib seed here for any stdlib randomness
    logger.info(f"Orchestration seed pinned to: {seed}")

def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments and merge with config defaults.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = create_argument_parser()
    return parser.parse_args()

def run_sieve_stage(config: Dict[str, Any]) -> None:
    """
    Execute the Sieve stage: Compute phi, residues, and save raw data.
    
    Args:
        config: Configuration dictionary.
    
    Raises:
        FatalSieveError: If sieve computation fails.
    """
    N = config['N']
    primes = config['primes']
    memory_limit_mb = config['memory_limit_mb']
    
    logger.info(f"Starting Sieve Stage for N={N}, Primes={primes}")
    
    # Initialize MemoryGuard
    guard = MemoryGuard(limit_mb=memory_limit_mb, check_interval=10000)
    
    for prime in primes:
        logger.info(f"Processing prime modulus: {prime}")
        try:
            # Compute phi values
            logger.debug("Computing phi values via linear sieve...")
            phi_values = compute_phi_linear_sieve(N, memory_guard=guard)
            
            # Compute residues
            logger.debug("Computing residue counts...")
            residue_counts = compute_residues(phi_values, prime)
            
            # Save raw data
            output_path = f"data/raw/residues_{prime}_{N}.json"
            save_residue_dataset(residue_counts, prime, N, output_path)
            logger.info(f"Saved residue data to {output_path}")
            
        except FatalSieveError as e:
            logger.error(f"Sieve failed for prime {prime}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in sieve stage for prime {prime}: {e}")
            raise FatalSieveError(N, f"Unexpected error: {str(e)}")

def run_stats_stage(config: Dict[str, Any]) -> None:
    """
    Execute the Statistics stage: Load raw data, run tests, save results.
    
    Args:
        config: Configuration dictionary.
    """
    N = config['N']
    primes = config['primes']
    
    logger.info("Starting Statistics Stage")
    
    # Validate constants before proceeding
    try:
        constants = get_error_bound_constants()
        logger.info("Error bound constants loaded successfully")
    except ResearchIncompleteError as e:
        logger.error(f"Constants validation failed: {e}")
        raise
    
    for prime in primes:
        input_path = f"data/raw/residues_{prime}_{N}.json"
        output_path = f"data/processed/stats_{prime}_{N}.json"
        
        logger.info(f"Running statistical analysis for prime {prime}")
        
        try:
            result = run_full_statistical_analysis(input_path, prime, N, constants)
            save_statistical_result(result, output_path)
            logger.info(f"Saved statistical results to {output_path}")
            
            # Log pass/fail status
            primary_flag = determine_primary_pass_fail(result)
            bonferroni_flag = determine_bonferroni_pass_fail(result)
            logger.info(f"Prime {prime}: Primary={primary_flag}, Bonferroni={bonferroni_flag}")
            
        except Exception as e:
            logger.error(f"Statistical analysis failed for prime {prime}: {e}")
            raise

def run_visualization_stage(config: Dict[str, Any]) -> None:
    """
    Execute the Visualization stage: Generate plots and reports.
    
    Args:
        config: Configuration dictionary.
    """
    N = config['N']
    primes = config['primes']
    
    logger.info("Starting Visualization Stage")
    
    for prime in primes:
        residue_path = f"data/raw/residues_{prime}_{N}.json"
        stats_path = f"data/processed/stats_{prime}_{N}.json"
        
        logger.info(f"Generating visualizations for prime {prime}")
        
        try:
            # Load data
            data = load_residue_data(residue_path)
            
            # Generate plots
            plot_bar_frequencies(data, prime)
            plot_residual_qq(data, prime)
            
            # Annotate with theoretical bounds
            annotate_theoretical_bounds(prime, data)
            
            # Generate report
            generate_visualization_report(prime, N, stats_path)
            
            logger.info(f"Visualizations generated for prime {prime}")
            
        except Exception as e:
            logger.error(f"Visualization failed for prime {prime}: {e}")
            raise

def run_orchestration(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestration function: Executes the full pipeline in sequence.
    
    Args:
        config: Configuration dictionary.
    
    Returns:
        Dictionary containing execution summary.
    """
    start_time = time.time()
    results = {
        'status': 'success',
        'start_time': start_time,
        'end_time': None,
        'duration_seconds': None,
        'primes_processed': [],
        'errors': []
    }
    
    N = config['N']
    primes = config['primes']
    
    logger.info(f"=== Starting Orchestration for N={N} ===")
    
    try:
        # Stage 1: Sieve
        run_sieve_stage(config)
        
        # Stage 2: Statistics
        run_stats_stage(config)
        
        # Stage 3: Visualization
        run_visualization_stage(config)
        
    except (FatalSieveError, ResearchIncompleteError, BenchmarkFailure) as e:
        results['status'] = 'failed'
        results['errors'].append(str(e))
        logger.critical(f"Pipeline failed with critical error: {e}")
    except Exception as e:
        results['status'] = 'failed'
        results['errors'].append(f"Unexpected error: {str(e)}")
        logger.critical(f"Pipeline failed with unexpected error: {e}", exc_info=True)
    
    end_time = time.time()
    results['end_time'] = end_time
    results['duration_seconds'] = end_time - start_time
    
    logger.info(f"=== Orchestration Complete: {results['status']} ===")
    logger.info(f"Duration: {results['duration_seconds']:.2f} seconds")
    
    return results

def main() -> int:
    """
    Main entry point for the analysis pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_args()
    config = load_config(args)
    
    # Pin seeds immediately
    pin_orchestration_seed(config)
    
    # Run the pipeline
    results = run_orchestration(config)
    
    if results['status'] == 'failed':
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())