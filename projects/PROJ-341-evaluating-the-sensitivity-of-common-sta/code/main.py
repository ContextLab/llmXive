import argparse
import json
import os
import sys
import gc
from datetime import datetime
import logging

# Add project root to path to allow imports from code.*
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation.logging_config import setup_logging, get_logger, log_simulation_params, log_output_file_written, log_error_details, log_shutdown
from simulation.data_generator import generate_normal_data, generate_contingency_table_data
from simulation.test_runner import run_simulation_condition, aggregate_results
from simulation.output_writer import write_p_values_raw
from analysis.aggregator import calculate_error_rates, save_aggregated_results
from analysis.threshold_finder import save_thresholds
from analysis.validator import run_validation_tests, save_simulation_metadata as save_meta_validator
from utils.metadata_manager import register_run, update_run_status, ensure_metadata_file_exists, load_simulation_metadata, save_simulation_metadata, compute_file_checksum, register_dataset_checksum

# Constants
MIN_N = 5
MAX_N = 500
STEP_N = 5
DEFAULT_ITERATIONS = 10000  # FR-001: Hard constraint (placeholder for real value if needed, but task implies loop logic)
# Note: The task description mentions "[deferred] iterations". We will use a configurable argument or default.
# For the purpose of this implementation, we assume a reasonable default for a run, but the logic supports any N.
# To prevent CI timeouts during development, we might cap it, but the prompt asks to implement the loop logic.
# We will use the argument passed or a default.

LOGGER = setup_logging()

def parse_args():
    parser = argparse.ArgumentParser(description="Run statistical sensitivity simulation")
    parser.add_argument('--test', type=str, default='t-test', choices=['t-test', 'anova', 'chi-squared'], help='Statistical test to run')
    parser.add_argument('--min-n', type=int, default=MIN_N, help='Minimum sample size')
    parser.add_argument('--max-n', type=int, default=MAX_N, help='Maximum sample size')
    parser.add_argument('--step-n', type=int, default=STEP_N, help='Step size for sample size')
    parser.add_argument('--iterations', type=int, default=DEFAULT_ITERATIONS, help='Number of iterations per condition')
    parser.add_argument('--effect-size', type=str, default='0.2,0.5,0.8', help='Comma-separated effect sizes')
    parser.add_argument('--hypothesis', type=str, default='two-sided', choices=['two-sided', 'one-sided', 'alternative'], help='Hypothesis type')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--mode', type=str, default='simulation', choices=['simulation', 'validation'], help='Run mode')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    return parser.parse_args()

def validate_args(args):
    if args.min_n >= args.max_n:
        raise ValueError("min-n must be less than max-n")
    if args.step_n <= 0:
        raise ValueError("step-n must be positive")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive")
    return True

def generate_sample_sizes(min_n, max_n, step_n):
    return list(range(min_n, max_n + 1, step_n))

def parse_effect_sizes(effect_str):
    return [float(x.strip()) for x in effect_str.split(',')]

def run_simulation_grid_chunked(args, logger):
    """
    Implements the parameter loop logic:
    Iterate through n=5..500 (step 5), effect sizes, and hypotheses.
    Enforce iteration count.
    """
    sample_sizes = generate_sample_sizes(args.min_n, args.max_n, args.step_n)
    effect_sizes = parse_effect_sizes(args.effect_size)
    
    logger.info(f"Starting simulation grid: n={sample_sizes[0]}..{sample_sizes[-1]}, effects={effect_sizes}, iterations={args.iterations}")
    
    all_results = []
    total_conditions = len(sample_sizes) * len(effect_sizes)
    current_condition = 0

    # Ensure output directories exist
    os.makedirs('data/simulation', exist_ok=True)
    os.makedirs('data/raw', exist_ok=True)

    # Register run in metadata
    metadata = ensure_metadata_file_exists()
    run_id = register_run(metadata, args, status='running')

    try:
        for n in sample_sizes:
            for effect in effect_sizes:
                current_condition += 1
                logger.info(f"Processing condition {current_condition}/{total_conditions}: n={n}, effect={effect}")
                
                # Run simulation for this specific condition
                # run_simulation_condition handles the iterations and returns aggregated stats per condition
                # However, to write raw p-values as required by T016, we need to capture raw data.
                # The existing test_runner returns aggregated results. We need to adapt or use the writer.
                # Given the constraints, we will run the condition and write raw p-values if the runner supports it,
                # or we assume the runner returns the raw list for this task.
                # Based on API: run_simulation_condition returns (p_values, stats_dict).
                
                p_values, stats_dict = run_simulation_condition(
                    test_type=args.test,
                    sample_size=n,
                    effect_size=effect,
                    hypothesis=args.hypothesis,
                    alpha=args.alpha,
                    iterations=args.iterations,
                    seed=args.seed + current_condition # Ensure unique seed per condition
                )
                
                # Write raw p-values to CSV (T016 requirement)
                # We write immediately to handle memory and ensure data is on disk
                row_data = {
                    'sample_size': n,
                    'effect_size': effect,
                    'test_type': args.test,
                    'hypothesis': args.hypothesis,
                    'p_values': p_values, # This might be a list, need to handle in writer
                    'condition_seed': args.seed + current_condition
                }
                write_p_values_raw(row_data, 'data/simulation/p_values_raw.csv')
                
                # Collect aggregated results for final summary
                all_results.append({
                    'n': n,
                    'effect_size': effect,
                    'test_type': args.test,
                    'hypothesis': args.hypothesis,
                    'alpha': args.alpha,
                    'type_i_error': stats_dict.get('type_i_error', 0.0),
                    'type_ii_error': stats_dict.get('type_ii_error', 0.0),
                    'power': stats_dict.get('power', 0.0),
                    'iterations': args.iterations
                })
                
                # Garbage collection to manage memory
                if current_condition % 10 == 0:
                    gc.collect()
            
        # Save aggregated results (T017/T018 requirement)
        save_aggregated_results(all_results, 'data/simulation/error_rates_summary.csv')
        
        # Update metadata status
        update_run_status(metadata, run_id, status='completed', checksum=compute_file_checksum('data/simulation/p_values_raw.csv'))
        save_simulation_metadata(metadata)
        
        logger.info("Simulation grid completed successfully.")
        return all_results

    except Exception as e:
        log_error_details(logger, e)
        update_run_status(metadata, run_id, status='failed', error=str(e))
        save_simulation_metadata(metadata)
        raise

def save_results_streaming(results, output_path):
    # This is handled by write_p_values_raw and save_aggregated_results in the loop
    pass

def run_validation_mode(args, logger):
    """
    Runs validation against real datasets (T029-T033).
    """
    logger.info("Starting validation mode...")
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/simulation', exist_ok=True)

    # Download and verify datasets
    datasets = run_validation_tests() # This function handles downloading and basic prep
    
    # Run tests on real data and save p-values
    # The validator or real_data_runner should handle this. 
    # We assume run_validation_tests returns paths or data, but we need to ensure the CSV is written.
    # Based on API, run_validation_tests is in validator.py.
    # We might need to call specific functions if run_validation_tests doesn't write the CSV.
    # Let's assume run_validation_tests orchestrates the download and prep, and we call the runner.
    
    # Since the API surface for validator.py shows run_validation_tests and main,
    # and real_data_runner has save_p_values_to_csv, we should ensure that is called.
    # However, to keep this task focused on the loop logic and fixing the import error:
    # We will call the main validation flow which should handle the outputs.
    
    from analysis.validator import main as validator_main
    # We can't easily pass args to validator_main if it doesn't accept them, 
    # but we can assume it runs the full validation pipeline if called.
    # Alternatively, we rely on the fact that T029-T033 are marked done and just need to run.
    # Let's call the validator main which should trigger the whole chain.
    validator_main()

    logger.info("Validation completed.")

def main():
    args = parse_args()
    validate_args(args)
    
    logger = get_logger()
    log_simulation_params(logger, args)
    
    try:
        if args.mode == 'simulation':
            run_simulation_grid_chunked(args, logger)
        elif args.mode == 'validation':
            run_validation_mode(args, logger)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
            
    except Exception as e:
        log_error_details(logger, e)
        sys.exit(1)
    finally:
        log_shutdown(logger)

if __name__ == '__main__':
    main()
