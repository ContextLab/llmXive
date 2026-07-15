import argparse
import json
import os
import sys
import gc
from datetime import datetime
import logging

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.simulation.data_generator import generate_normal_data, generate_multinomial_data
from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation.output_writer import write_p_values_raw
from code.simulation.logging_config import setup_logging, get_logger, log_simulation_params, log_error_details, log_output_file_written
from code.simulation import get_rng
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.validator import download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset, preprocess_dataset_for_validation, compute_file_checksum, save_simulation_metadata, load_simulation_metadata
from code.analysis.real_data_runner import run_ttest_on_dataset, run_anova_on_dataset, run_chi_squared_on_dataset, save_p_values_to_csv
from code.analysis.bootstrapper import run_bootstrapped_validation, save_power_results
from code.analysis.validation_metrics import calculate_validation_metrics, save_validation_metrics
from code.analysis.threshold_finder import save_thresholds
from code.utils.metadata_manager import register_run, update_run_status

# Constants
DEFAULT_ITERATIONS = 10000  # Hard constraint per FR-001 (deferred value resolved to 10k for MVP feasibility)
MIN_N = 5
MAX_N = 500
STEP_N = 5

def parse_args():
    parser = argparse.ArgumentParser(description="Main entry point for statistical test sensitivity analysis")
    
    # Simulation parameters
    parser.add_argument('--mode', type=str, choices=['simulation', 'validation', 'aggregation', 'full'], default='simulation',
                        help='Execution mode: simulation, validation, aggregation, or full pipeline')
    parser.add_argument('--test', type=str, choices=['t-test', 'anova', 'chi-squared', 'all'], default='all',
                        help='Statistical test to run')
    parser.add_argument('--min-n', type=int, default=MIN_N, help='Minimum sample size')
    parser.add_argument('--max-n', type=int, default=MAX_N, help='Maximum sample size')
    parser.add_argument('--step-n', type=int, default=STEP_N, help='Step size for sample sizes')
    parser.add_argument('--effect-sizes', type=str, default='0.2,0.5,0.8',
                        help='Comma-separated list of effect sizes')
    parser.add_argument('--iterations', type=int, default=DEFAULT_ITERATIONS,
                        help='Number of iterations per condition (hard constraint)')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--hypothesis', type=str, choices=['two-sided', 'one-sided'], default='two-sided',
                        help='Hypothesis type')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
    
    # Validation parameters
    parser.add_argument('--datasets', type=str, default='breast_cancer,wine,adult',
                        help='Comma-separated list of datasets to validate')
    
    return parser.parse_args()

def validate_args(args):
    if args.min_n < 2:
        raise ValueError("Minimum sample size must be at least 2")
    if args.max_n < args.min_n:
        raise ValueError("Maximum sample size must be greater than or equal to minimum")
    if args.iterations < 100:
        raise ValueError("Iterations must be at least 100 for meaningful results")
    return True

def generate_sample_sizes(min_n, max_n, step):
    """Generate list of sample sizes from min_n to max_n with given step"""
    return list(range(min_n, max_n + 1, step))

def parse_effect_sizes(effect_sizes_str):
    """Parse comma-separated effect sizes"""
    return [float(x.strip()) for x in effect_sizes_str.split(',')]

def generate_conditions(sample_sizes, effect_sizes, test_types, hypotheses, alpha):
    """Generate all simulation conditions"""
    conditions = []
    for n in sample_sizes:
        for effect_size in effect_sizes:
            for test_type in test_types:
                for hypothesis in hypotheses:
                    conditions.append({
                        'n': n,
                        'effect_size': effect_size,
                        'test_type': test_type,
                        'hypothesis': hypothesis,
                        'alpha': alpha
                    })
    return conditions

def run_simulation_grid_chunked(conditions, iterations, seed=None):
    """Run simulation for all conditions with chunked processing and streaming output"""
    logger = get_logger()
    all_results = []
    
    logger.info(f"Starting simulation grid with {len(conditions)} conditions, {iterations} iterations each")
    
    for i, condition in enumerate(conditions):
        logger.info(f"Processing condition {i+1}/{len(conditions)}: n={condition['n']}, "
                   f"effect={condition['effect_size']}, test={condition['test_type']}")
        
        # Run simulation for this condition
        results = run_simulation_condition(
            n=condition['n'],
            effect_size=condition['effect_size'],
            test_type=condition['test_type'],
            hypothesis=condition['hypothesis'],
            alpha=condition['alpha'],
            iterations=iterations,
            seed=seed + i if seed else None
        )
        
        all_results.append({
            'condition': condition,
            'results': results
        })
        
        # Garbage collection every 10 conditions
        if i % 10 == 0:
            gc.collect()
    
    return all_results

def save_results_streaming(all_results, output_path):
    """Save simulation results to CSV in streaming fashion"""
    logger = get_logger()
    
    # Prepare data for CSV
    csv_rows = []
    for item in all_results:
        condition = item['condition']
        results = item['results']
        
        for p_value in results['p_values']:
            csv_rows.append({
                'sample_size': condition['n'],
                'effect_size': condition['effect_size'],
                'test_type': condition['test_type'],
                'hypothesis': condition['hypothesis'],
                'alpha': condition['alpha'],
                'p_value': p_value,
                'rejection': p_value < condition['alpha']
            })
    
    # Write to CSV
    write_p_values_raw(csv_rows, output_path)
    log_output_file_written(output_path)
    
    return csv_rows

def run_validation_mode(datasets, iterations=1000):
    """Run validation against real-world datasets"""
    logger = get_logger()
    logger.info("Starting validation mode")
    
    # Ensure data directories exist
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/simulation', exist_ok=True)
    
    # Download and verify datasets
    dataset_map = {
        'breast_cancer': download_breast_cancer_dataset,
        'wine': download_wine_dataset,
        'adult': download_adult_dataset
    }
    
    downloaded_datasets = {}
    metadata = load_simulation_metadata()
    
    for dataset_name in datasets:
        if dataset_name in dataset_map:
            logger.info(f"Downloading {dataset_name} dataset")
            data_path = dataset_map[dataset_name]()
            if data_path:
                checksum = compute_file_checksum(data_path)
                downloaded_datasets[dataset_name] = {
                    'path': data_path,
                    'checksum': checksum
                }
                # Update metadata
                if 'datasets' not in metadata:
                    metadata['datasets'] = {}
                metadata['datasets'][dataset_name] = {
                    'path': data_path,
                    'checksum': checksum,
                    'downloaded_at': datetime.now().isoformat()
                }
    
    # Save metadata with checksums
    save_simulation_metadata(metadata)
    
    # Preprocess and run tests on real data
    real_data_results = []
    for dataset_name, dataset_info in downloaded_datasets.items():
        logger.info(f"Processing {dataset_name} dataset")
        data = preprocess_dataset_for_validation(dataset_info['path'], dataset_name)
        
        if data:
            # Run t-test
            if 'groups' in data and len(data['groups']) >= 2:
                ttest_results = run_ttest_on_dataset(data, dataset_name)
                real_data_results.extend(ttest_results)
            
            # Run ANOVA if more than 2 groups
            if 'groups' in data and len(data['groups']) > 2:
                anova_results = run_anova_on_dataset(data, dataset_name)
                real_data_results.extend(anova_results)
            
            # Run chi-squared if categorical data available
            if 'contingency' in data:
                chi_results = run_chi_squared_on_dataset(data, dataset_name)
                real_data_results.extend(chi_results)
    
    # Save real data p-values
    if real_data_results:
        save_p_values_to_csv(real_data_results, 'data/simulation/real_data_pvalues.csv')
    
    # Run bootstrapped validation
    if os.path.exists('data/simulation/real_data_pvalues.csv'):
        bootstrapped_results = run_bootstrapped_validation(iterations=iterations)
        save_power_results(bootstrapped_results, 'data/simulation/real_data_power.json')
    
    # Calculate validation metrics
    if os.path.exists('data/simulation/real_data_pvalues.csv') and os.path.exists('data/simulation/p_values_raw.csv'):
        validation_metrics = calculate_validation_metrics()
        save_validation_metrics(validation_metrics, 'data/simulation/validation_metrics.json')
    
    return downloaded_datasets, real_data_results

def run_aggregation_mode():
    """Aggregate simulation results and calculate error rates"""
    logger = get_logger()
    logger.info("Starting aggregation mode")
    
    # Load raw p-values
    if not os.path.exists('data/simulation/p_values_raw.csv'):
        logger.error("p_values_raw.csv not found. Run simulation mode first.")
        return False
    
    # Calculate error rates
    error_rates = calculate_error_rates('data/simulation/p_values_raw.csv')
    
    # Save aggregated results
    save_aggregated_results(error_rates, 'data/simulation/error_rates_summary.csv')
    
    # Save thresholds
    from code.analysis.threshold_finder import load_error_rates, save_thresholds
    error_data = load_error_rates('data/simulation/error_rates_summary.csv')
    thresholds = save_thresholds(error_data, 'data/simulation/thresholds.json')
    
    return True

def main():
    args = parse_args()
    
    # Setup logging
    log_file = setup_logging()
    logger = get_logger()
    
    logger.info("=" * 60)
    logger.info("Starting Statistical Test Sensitivity Analysis")
    logger.info("=" * 60)
    
    try:
        # Validate arguments
        validate_args(args)
        
        # Register run in metadata
        metadata = load_simulation_metadata()
        register_run(metadata, {
            'mode': args.mode,
            'test': args.test,
            'min_n': args.min_n,
            'max_n': args.max_n,
            'iterations': args.iterations,
            'alpha': args.alpha,
            'timestamp': datetime.now().isoformat()
        })
        save_simulation_metadata(metadata)
        
        # Log parameters
        log_simulation_params(args)
        
        if args.mode == 'simulation' or args.mode == 'full':
            # Generate sample sizes
            sample_sizes = generate_sample_sizes(args.min_n, args.max_n, args.step_n)
            
            # Parse effect sizes
            effect_sizes = parse_effect_sizes(args.effect_sizes)
            
            # Determine test types
            if args.test == 'all':
                test_types = ['t-test', 'anova', 'chi-squared']
            else:
                test_types = [args.test]
            
            # Determine hypotheses
            hypotheses = [args.hypothesis]
            
            # Generate all conditions
            conditions = generate_conditions(sample_sizes, effect_sizes, test_types, hypotheses, args.alpha)
            
            # Enforce hard constraint on iterations
            actual_iterations = min(args.iterations, DEFAULT_ITERATIONS)
            if args.iterations != DEFAULT_ITERATIONS:
                logger.warning(f"Iterations set to {args.iterations}, using {actual_iterations} to respect hard constraint")
            
            logger.info(f"Generated {len(conditions)} conditions with {actual_iterations} iterations each")
            
            # Run simulation
            all_results = run_simulation_grid_chunked(conditions, actual_iterations, args.seed)
            
            # Save results
            output_path = 'data/simulation/p_values_raw.csv'
            save_results_streaming(all_results, output_path)
            
            logger.info(f"Simulation complete. Results saved to {output_path}")
            
            if args.mode == 'full':
                # Run aggregation
                run_aggregation_mode()
                
                # Run validation
                datasets = args.datasets.split(',')
                run_validation_mode(datasets, iterations=actual_iterations)
                
                logger.info("Full pipeline complete")
        
        elif args.mode == 'aggregation':
            success = run_aggregation_mode()
            if not success:
                logger.error("Aggregation failed")
                sys.exit(1)
        
        elif args.mode == 'validation':
            datasets = args.datasets.split(',')
            run_validation_mode(datasets, iterations=args.iterations)
            logger.info("Validation complete")
        
        logger.info("=" * 60)
        logger.info("Analysis completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        log_error_details(e)
        sys.exit(1)

if __name__ == '__main__':
    main()