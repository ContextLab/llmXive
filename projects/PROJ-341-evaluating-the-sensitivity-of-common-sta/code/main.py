import argparse
import json
import os
import sys
import gc
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.simulation.logging_config import setup_logging, get_logger
from code.simulation.test_runner import run_simulation_condition
from code.simulation.data_generator import generate_normal_data, generate_multinomial_data
from code.simulation.output_writer import write_p_values_raw
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.threshold_finder import save_thresholds
from code.analysis.validator import download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset, compute_file_checksum, ensure_data_raw_dir
from code.analysis.bootstrapper import save_power_results, run_bootstrapped_validation
from code.analysis.validation_metrics import main as validation_metrics_main
from code.analysis.report_generator import main as report_generator_main

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Test Sensitivity Analysis")
    parser.add_argument('--mode', type=str, choices=['simulation', 'aggregation', 'validation', 'all'], default='all',
                      help='Execution mode')
    parser.add_argument('--test', type=str, choices=['t-test', 'anova', 'chi-squared'], default='t-test',
                      help='Statistical test to run')
    parser.add_argument('--min-n', type=int, default=5, help='Minimum sample size')
    parser.add_argument('--max-n', type=int, default=500, help='Maximum sample size')
    parser.add_argument('--iterations', type=int, default=10000, help='Number of iterations per condition')
    parser.add_argument('--effect-sizes', type=str, default='small,medium', help='Comma-separated effect sizes')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with fewer iterations')
    return parser.parse_args()

def validate_args(args):
    if args.min_n >= args.max_n:
        raise ValueError("min-n must be less than max-n")
    if args.iterations <= 0:
        raise ValueError("iterations must be positive")
    return True

def generate_sample_sizes(min_n: int, max_n: int, step: int = 5) -> List[int]:
    return list(range(min_n, max_n + 1, step))

def parse_effect_sizes(effect_sizes_str: str) -> List[str]:
    return [e.strip() for e in effect_sizes_str.split(',')]

def generate_conditions(sample_sizes: List[int], effect_sizes: List[str], test_type: str):
    return [{'sample_size': n, 'effect_size': e, 'test_type': test_type} for n in sample_sizes for e in effect_sizes]

def run_simulation_grid_chunked(conditions: List[Dict], iterations: int, alpha: float):
    """Run simulation grid with chunked processing to manage memory."""
    results = []
    for i, cond in enumerate(conditions):
        logger.info(f"Running condition {i+1}/{len(conditions)}: n={cond['sample_size']}, effect={cond['effect_size']}")
        
        # Run simulation
        sim_result = run_simulation_condition(
            test_type=cond['test_type'],
            sample_size=cond['sample_size'],
            effect_size=cond['effect_size'],
            iterations=iterations,
            alpha=alpha
        )
        results.append(sim_result)
        
        # Garbage collection for memory management
        if i % 10 == 0:
            gc.collect()
    
    return results

def save_results_streaming(results: List[Dict], output_path: str = "data/simulation/p_values_raw.csv"):
    """Save simulation results to CSV with streaming."""
    write_p_values_raw(results, output_path)

def run_aggregation_mode():
    """Run aggregation mode to calculate error rates."""
    logger.info("Running aggregation mode...")
    save_aggregated_results()

def run_validation_mode():
    """Run validation mode to download and test real datasets."""
    logger.info("Running validation mode...")
    
    # Download datasets
    data_dir = ensure_data_raw_dir()
    datasets = [
        download_breast_cancer_dataset(),
        download_wine_dataset(),
        download_adult_dataset()
    ]
    
    # Save and verify checksums
    metadata = {'datasets': [], 'checksums': {}}
    for df, name in datasets:
        filepath = os.path.join(data_dir, f"{name}.csv")
        df.to_csv(filepath, index=False)
        checksum = compute_file_checksum(filepath)
        metadata['datasets'].append({'name': name, 'checksum': checksum, 'n_samples': len(df)})
        metadata['checksums'][filepath] = checksum
        logger.info(f"Saved {name}: {len(df)} samples, checksum: {checksum[:16]}...")
    
    # Save metadata
    with open("data/simulation_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Run tests on real data (T031)
    from code.analysis.real_data_runner import main as real_data_runner_main
    real_data_runner_main()
    
    # Run bootstrapped power estimation (T032)
    from code.analysis.bootstrapper import main as bootstrapper_main
    bootstrapper_main()
    
    # Run validation metrics calculation (T034)
    validation_metrics_main()
    
    # Generate report (T033)
    report_generator_main()

def main():
    args = parse_args()
    validate_args(args)
    
    setup_logging()
    logger.info(f"Starting simulation at {datetime.now()}")
    logger.info(f"Mode: {args.mode}")
    
    if args.test_mode:
        iterations = 1000
        min_n, max_n = 5, 50
        logger.info("Running in TEST MODE with reduced iterations")
    else:
        iterations = args.iterations
        min_n, max_n = args.min_n, args.max_n
    
    if args.mode in ['simulation', 'all']:
        # Generate conditions
        sample_sizes = generate_sample_sizes(min_n, max_n)
        effect_sizes = parse_effect_sizes(args.effect_sizes)
        conditions = generate_conditions(sample_sizes, effect_sizes, args.test)
        
        # Run simulation
        results = run_simulation_grid_chunked(conditions, iterations, args.alpha)
        
        # Save results
        save_results_streaming(results)
        logger.info("Simulation complete, results saved")
    
    if args.mode in ['aggregation', 'all']:
        run_aggregation_mode()
        logger.info("Aggregation complete")
    
    if args.mode in ['validation', 'all']:
        run_validation_mode()
        logger.info("Validation complete")
    
    logger.info("All tasks completed successfully")

if __name__ == "__main__":
    main()