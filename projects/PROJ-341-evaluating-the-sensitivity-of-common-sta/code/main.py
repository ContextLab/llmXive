import argparse
import gc
import json
import os
import sys
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Import simulation modules
from code.simulation.data_generator import generate_normal_data, generate_multinomial_data, generate_contingency_table_data
from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation.output_writer import write_p_values_raw
from code.simulation.logging_config import setup_logging, get_logger, log_simulation_params, log_shutdown
from code.simulation import set_seed, get_rng
from code.utils.metadata_manager import ensure_metadata_file_exists, save_simulation_metadata, register_run

# Import analysis modules
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.threshold_finder import save_thresholds
from code.analysis.validator import main as run_validation
from code.analysis.bootstrapper import main as run_bootstrapper
from code.visualization.plotter import main as run_plotter
from code.visualization.saver import main as run_saver
from code.analysis.report_generator import main as run_report

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except:
        return 0.0

def check_memory_limit(limit_mb: float = 7000) -> bool:
    """Check if memory usage is within limit."""
    current = get_memory_usage_mb()
    return current < limit_mb

def force_gc():
    """Force garbage collection."""
    gc.collect()

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Statistical Test Sensitivity Simulation')
    
    # Mode selection
    parser.add_argument('--mode', type=str, default='simulation', 
                      choices=['simulation', 'validation', 'full_pipeline'],
                      help='Execution mode')
    
    # Simulation parameters
    parser.add_argument('--test', type=str, default='t-test',
                      choices=['t-test', 'anova', 'chi-squared'],
                      help='Statistical test to run')
    parser.add_argument('--min-n', type=int, default=5,
                      help='Minimum sample size')
    parser.add_argument('--max-n', type=int, default=500,
                      help='Maximum sample size')
    parser.add_argument('--step-n', type=int, default=5,
                      help='Step size for sample size')
    parser.add_argument('--effect-sizes', type=str, default='0.0,0.2,0.5,0.8',
                      help='Comma-separated list of effect sizes')
    parser.add_argument('--hypotheses', type=str, default='null,alternative',
                      help='Comma-separated list of hypotheses (null/alternative)')
    parser.add_argument('--iterations', type=int, default=10000,
                      help='Number of iterations per condition')
    parser.add_argument('--alpha', type=float, default=0.05,
                      help='Significance level')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    
    # Validation parameters
    parser.add_argument('--datasets', type=str, default='breast_cancer,wine,adult',
                      help='Comma-separated list of datasets to validate')
    
    return parser.parse_args()

def validate_args(args: argparse.Namespace) -> bool:
    """Validate command line arguments."""
    if args.min_n < 2:
        print("Error: min-n must be at least 2")
        return False
    if args.max_n < args.min_n:
        print("Error: max-n must be greater than min-n")
        return False
    if args.step_n < 1:
        print("Error: step-n must be at least 1")
        return False
    if args.iterations < 100:
        print("Warning: Low iteration count may reduce accuracy")
    return True

def generate_sample_sizes(min_n: int, max_n: int, step: int) -> List[int]:
    """Generate list of sample sizes to test."""
    return list(range(min_n, max_n + 1, step))

def parse_effect_sizes(effect_sizes_str: str) -> List[float]:
    """Parse effect sizes from comma-separated string."""
    return [float(x.strip()) for x in effect_sizes_str.split(',')]

def parse_hypotheses(hypotheses_str: str) -> List[str]:
    """Parse hypotheses from comma-separated string."""
    return [x.strip().lower() for x in hypotheses_str.split(',')]

def generate_conditions(test_type: str, sample_sizes: List[int], 
                       effect_sizes: List[float], hypotheses: List[str],
                       alpha: float) -> List[Dict[str, Any]]:
    """Generate all simulation conditions to test."""
    conditions = []
    for n in sample_sizes:
        for effect_size in effect_sizes:
            for hypothesis in hypotheses:
                # Determine if this is a null or alternative hypothesis scenario
                if hypothesis == 'null':
                    # For null hypothesis, effect size should be 0
                    actual_effect = 0.0
                else:
                    actual_effect = effect_size
                
                conditions.append({
                    'test_type': test_type,
                    'sample_size': n,
                    'effect_size': actual_effect,
                    'hypothesis': hypothesis,
                    'alpha': alpha
                })
    return conditions

def run_simulation_grid_chunked(conditions: List[Dict[str, Any]], 
                               iterations: int, 
                               seed: int,
                               chunk_size: int = 100) -> Dict[str, Any]:
    """
    Run simulation grid in chunks to manage memory.
    
    Args:
        conditions: List of simulation conditions
        iterations: Number of iterations per condition
        seed: Base random seed
        chunk_size: Number of conditions to process at once
        
    Returns:
        Dictionary containing all p-values and metadata
    """
    logger = get_logger()
    all_results = []
    total_conditions = len(conditions)
    
    logger.info(f"Starting simulation with {total_conditions} conditions, {iterations} iterations each")
    
    # Process conditions in chunks
    for i in range(0, total_conditions, chunk_size):
        chunk = conditions[i:i+chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1}/{(total_conditions + chunk_size - 1)//chunk_size}")
        
        for condition in chunk:
            try:
                # Run simulation for this condition
                results = run_simulation_condition(
                    test_type=condition['test_type'],
                    n=condition['sample_size'],
                    effect_size=condition['effect_size'],
                    hypothesis=condition['hypothesis'],
                    iterations=iterations,
                    alpha=condition['alpha'],
                    seed=seed + hash(str(condition)) % 10000
                )
                all_results.append(results)
                
                # Check memory and force GC if needed
                if not check_memory_limit():
                    logger.warning("Memory limit approaching, forcing GC")
                    force_gc()
                    
            except Exception as e:
                logger.error(f"Error in condition {condition}: {str(e)}")
                raise
        
        # Force GC between chunks
        force_gc()
        
    return {'results': all_results, 'total_conditions': total_conditions}

def run_validation_mode(datasets: List[str], seed: int = 42):
    """Run validation mode on real datasets."""
    logger = get_logger()
    logger.info("Starting validation mode")
    
    # Run validation
    run_validation()
    
    # Run bootstrapper
    run_bootstrapper()
    
    logger.info("Validation mode completed")

def run_full_pipeline(args: argparse.Namespace):
    """Run the complete pipeline: simulation, analysis, visualization, and report."""
    logger = get_logger()
    logger.info("Starting full pipeline")
    
    # Step 1: Run simulation
    logger.info("Phase 1: Running simulation")
    sample_sizes = generate_sample_sizes(args.min_n, args.max_n, args.step_n)
    effect_sizes = parse_effect_sizes(args.effect_sizes)
    hypotheses = parse_hypotheses(args.hypotheses)
    
    conditions = generate_conditions(
        test_type=args.test,
        sample_sizes=sample_sizes,
        effect_sizes=effect_sizes,
        hypotheses=hypotheses,
        alpha=args.alpha
    )
    
    # Run simulation
    simulation_results = run_simulation_grid_chunked(
        conditions=conditions,
        iterations=args.iterations,
        seed=args.seed
    )
    
    # Step 2: Write raw p-values
    logger.info("Phase 2: Writing raw p-values")
    write_p_values_raw(simulation_results['results'])
    
    # Step 3: Aggregate results
    logger.info("Phase 3: Aggregating results")
    error_rates = calculate_error_rates()
    save_aggregated_results(error_rates)
    
    # Step 4: Find thresholds
    logger.info("Phase 4: Finding thresholds")
    save_thresholds(error_rates)
    
    # Step 5: Run validation
    logger.info("Phase 5: Running validation")
    run_validation_mode(args.datasets.split(','))
    
    # Step 6: Generate plots
    logger.info("Phase 6: Generating plots")
    run_plotter()
    run_saver()
    
    # Step 7: Generate report
    logger.info("Phase 7: Generating report")
    run_report()
    
    logger.info("Full pipeline completed successfully")

def main():
    """Main entry point."""
    args = parse_args()
    
    if not validate_args(args):
        sys.exit(1)
        
    # Setup logging
    log_file = setup_logging()
    logger = get_logger()
    logger.info("Simulation started")
    
    # Register run
    ensure_metadata_file_exists()
    register_run({
        'args': vars(args),
        'timestamp': time.time()
    })
    
    try:
        if args.mode == 'simulation':
            # Run simulation only
            sample_sizes = generate_sample_sizes(args.min_n, args.max_n, args.step_n)
            effect_sizes = parse_effect_sizes(args.effect_sizes)
            hypotheses = parse_hypotheses(args.hypotheses)
            
            conditions = generate_conditions(
                test_type=args.test,
                sample_sizes=sample_sizes,
                effect_sizes=effect_sizes,
                hypotheses=hypotheses,
                alpha=args.alpha
            )
            
            logger.info(f"Running {len(conditions)} conditions with {args.iterations} iterations each")
            log_simulation_params({
                'test_type': args.test,
                'sample_sizes': sample_sizes,
                'effect_sizes': effect_sizes,
                'hypotheses': hypotheses,
                'iterations': args.iterations,
                'alpha': args.alpha,
                'seed': args.seed
            })
            
            simulation_results = run_simulation_grid_chunked(
                conditions=conditions,
                iterations=args.iterations,
                seed=args.seed
            )
            
            # Write results
            write_p_values_raw(simulation_results['results'])
            
            # Aggregate and save
            error_rates = calculate_error_rates()
            save_aggregated_results(error_rates)
            save_thresholds(error_rates)
            
            logger.info("Simulation completed successfully")
            
        elif args.mode == 'validation':
            run_validation_mode(args.datasets.split(','))
            
        elif args.mode == 'full_pipeline':
            run_full_pipeline(args)
            
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        raise
    finally:
        log_shutdown()

if __name__ == '__main__':
    main()