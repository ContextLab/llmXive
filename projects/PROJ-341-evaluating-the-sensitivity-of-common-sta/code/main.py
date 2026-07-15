import argparse
import gc
import json
import os
import sys
import time
import traceback
from typing import List, Dict, Any, Optional, Tuple

# Memory optimization: Import psutil only if available, otherwise use fallback
# This prevents ModuleNotFoundError while still allowing memory checks if installed
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    # Fallback: minimal memory check using resource module (Unix only) or just skip
    try:
        import resource
        HAS_RESOURCE = True
    except ImportError:
        HAS_RESOURCE = False

from code.simulation.data_generator import generate_normal_data, generate_contingency_table_data
from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation.output_writer import write_p_values_raw
from code.simulation.logging_config import setup_logging, get_logger, log_simulation_params, log_error_details, log_output_file_written
from code.analysis.aggregator import calculate_error_rates, save_aggregated_results
from code.analysis.threshold_finder import save_thresholds, find_type_i_threshold, find_power_threshold
from code.analysis.validator import download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset
from code.analysis.real_data_runner import run_ttest_on_dataset, run_anova_on_dataset, run_chi_squared_on_dataset, save_p_values_to_csv
from code.analysis.bootstrapper import run_bootstrapped_validation, save_power_results
from code.analysis.validation_metrics import calculate_validation_metrics, save_validation_metrics
from code.analysis.report_generator import generate_report

# Constants
MEMORY_LIMIT_MB = 7000  # 7GB limit as per task requirement
DEFAULT_ITERATIONS = 10000
MIN_ITERATIONS = 100
CHUNK_SIZE = 100  # Number of sample sizes to process per chunk

logger = None

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    elif HAS_RESOURCE:
        # Unix only
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        return rusage.ru_maxrss / 1024  # Convert from KB to MB
    else:
        # Fallback: return 0 (assume safe)
        return 0.0

def check_memory_limit(limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """Check if current memory usage is within limit."""
    current = get_memory_usage_mb()
    if current > limit_mb:
        return False
    return True

def force_gc():
    """Force garbage collection to free memory."""
    gc.collect()
    if logger:
        logger.info("Garbage collection triggered")

def parse_args():
    parser = argparse.ArgumentParser(description="Statistical Test Sensitivity Analysis")
    parser.add_argument('--mode', type=str, choices=['simulation', 'validation', 'full'], default='simulation',
                      help='Execution mode: simulation, validation, or full pipeline')
    parser.add_argument('--test', type=str, choices=['t-test', 'anova', 'chi-squared', 'all'], default='all',
                      help='Statistical test to run')
    parser.add_argument('--min-n', type=int, default=5, help='Minimum sample size')
    parser.add_argument('--max-n', type=int, default=500, help='Maximum sample size')
    parser.add_argument('--step-n', type=int, default=5, help='Step size for sample sizes')
    parser.add_argument('--iterations', type=int, default=DEFAULT_ITERATIONS,
                      help=f'Number of iterations per condition (default: {DEFAULT_ITERATIONS})')
    parser.add_argument('--effect-size', type=str, default='small,medium',
                      help='Comma-separated effect sizes (e.g., small,medium,large)')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE,
                      help='Number of sample sizes to process per memory-check chunk')
    parser.add_argument('--log-file', type=str, default='data/simulation/run.log',
                      help='Path to log file')
    return parser.parse_args()

def validate_args(args):
    if args.iterations < MIN_ITERATIONS:
        raise ValueError(f"Iterations must be at least {MIN_ITERATIONS}")
    if args.min_n >= args.max_n:
        raise ValueError("min-n must be less than max-n")
    if args.step_n <= 0:
        raise ValueError("step-n must be positive")
    return True

def generate_sample_sizes(min_n: int, max_n: int, step_n: int) -> List[int]:
    """Generate list of sample sizes from min to max with step."""
    return list(range(min_n, max_n + 1, step_n))

def parse_effect_sizes(effect_str: str) -> List[str]:
    """Parse comma-separated effect sizes."""
    return [e.strip() for e in effect_str.split(',')]

def generate_conditions(sample_sizes: List[int], effect_sizes: List[str], test_types: List[str], alpha: float) -> List[Dict[str, Any]]:
    """Generate all combinations of conditions to test."""
    conditions = []
    for n in sample_sizes:
        for effect in effect_sizes:
            for test in test_types:
                conditions.append({
                    'n': n,
                    'effect_size': effect,
                    'test_type': test,
                    'alpha': alpha
                })
    return conditions

def run_simulation_grid_chunked(conditions: List[Dict[str, Any]], chunk_size: int = CHUNK_SIZE) -> List[Dict[str, Any]]:
    """
    Run simulation conditions in chunks to manage memory usage.
    Returns list of raw results.
    """
    all_results = []
    total_chunks = (len(conditions) + chunk_size - 1) // chunk_size

    for i in range(0, len(conditions), chunk_size):
        chunk = conditions[i:i + chunk_size]
        chunk_num = i // chunk_size + 1

        # Check memory before processing chunk
        if not check_memory_limit():
            logger.warning(f"Memory usage approaching limit at chunk {chunk_num}/{total_chunks}. Force GC...")
            force_gc()
            if not check_memory_limit():
                logger.error(f"Memory limit exceeded after GC. Stopping simulation.")
                break

        logger.info(f"Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} conditions)")

        for cond in chunk:
            try:
                result = run_simulation_condition(
                    n=cond['n'],
                    effect_size=cond['effect_size'],
                    test_type=cond['test_type'],
                    alpha=cond['alpha'],
                    iterations=DEFAULT_ITERATIONS
                )
                all_results.append(result)

                # Periodic GC to prevent memory buildup
                if len(all_results) % 100 == 0:
                    force_gc()

            except Exception as e:
                logger.error(f"Error in condition {cond}: {e}")
                traceback.print_exc()
                continue

        # Force GC after each chunk
        force_gc()

    return all_results

def run_simulation_mode(args):
    """Run the simulation mode."""
    global logger
    logger = setup_logging(log_file=args.log_file)
    log_simulation_params(logger, args)

    test_types = ['t-test', 'anova', 'chi-squared'] if args.test == 'all' else [args.test]
    sample_sizes = generate_sample_sizes(args.min_n, args.max_n, args.step_n)
    effect_sizes = parse_effect_sizes(args.effect_size)

    conditions = generate_conditions(sample_sizes, effect_sizes, test_types, args.alpha)
    logger.info(f"Generated {len(conditions)} simulation conditions")

    # Run simulation in chunks
    raw_results = run_simulation_grid_chunked(conditions, args.chunk_size)

    # Write raw p-values
    output_file = 'data/simulation/p_values_raw.csv'
    write_p_values_raw(raw_results, output_file)
    log_output_file_written(logger, output_file)

    # Aggregate results
    error_rates = calculate_error_rates(raw_results, args.alpha)
    error_rates_file = 'data/simulation/error_rates_summary.csv'
    save_aggregated_results(error_rates, error_rates_file)
    log_output_file_written(logger, error_rates_file)

    # Find thresholds
    thresholds = {}
    for test_type in test_types:
        for effect in effect_sizes:
            # Type I error threshold
            type_i_thresh = find_type_i_threshold(error_rates, test_type, effect, args.alpha)
            # Power threshold (power < 0.8)
            power_thresh = find_power_threshold(error_rates, test_type, effect)

            key = f"{test_type}_{effect}"
            thresholds[key] = {
                'test_type': test_type,
                'effect_size': effect,
                'type_i_threshold': type_i_thresh,
                'power_threshold': power_thresh
            }

    thresholds_file = 'data/simulation/thresholds.json'
    with open(thresholds_file, 'w') as f:
        json.dump(thresholds, f, indent=2)
    log_output_file_written(logger, thresholds_file)

    logger.info("Simulation mode completed successfully")
    return True

def run_validation_mode(args):
    """Run the validation mode on real datasets."""
    global logger
    logger = setup_logging(log_file=args.log_file)
    log_simulation_params(logger, args)

    # Download datasets
    logger.info("Downloading real datasets...")
    datasets = {}
    datasets['breast_cancer'] = download_breast_cancer_dataset()
    datasets['wine'] = download_wine_dataset()
    datasets['adult'] = download_adult_dataset()

    # Run tests on real datasets
    all_pvalues = []
    for name, data in datasets.items():
        logger.info(f"Running tests on {name} dataset...")
        pvalues = []

        # T-test
        try:
            p_t = run_ttest_on_dataset(data, name)
            pvalues.append({'dataset': name, 'test': 't-test', 'p_value': p_t})
        except Exception as e:
            logger.warning(f"T-test failed for {name}: {e}")

        # ANOVA
        try:
            p_a = run_anova_on_dataset(data, name)
            pvalues.append({'dataset': name, 'test': 'anova', 'p_value': p_a})
        except Exception as e:
            logger.warning(f"ANOVA failed for {name}: {e}")

        # Chi-squared
        try:
            p_c = run_chi_squared_on_dataset(data, name)
            pvalues.append({'dataset': name, 'test': 'chi-squared', 'p_value': p_c})
        except Exception as e:
            logger.warning(f"Chi-squared failed for {name}: {e}")

        all_pvalues.extend(pvalues)

    # Save real data p-values
    real_pvalues_file = 'data/simulation/real_data_pvalues.csv'
    save_p_values_to_csv(all_pvalues, real_pvalues_file)
    log_output_file_written(logger, real_pvalues_file)

    # Run bootstrapped validation
    logger.info("Running bootstrapped validation...")
    power_results = run_bootstrapped_validation(all_pvalues, args.alpha)
    power_file = 'data/simulation/real_data_power.json'
    save_power_results(power_results, power_file)
    log_output_file_written(logger, power_file)

    # Calculate validation metrics
    metrics = calculate_validation_metrics(all_pvalues, args.alpha)
    metrics_file = 'data/simulation/validation_metrics.json'
    save_validation_metrics(metrics, metrics_file)
    log_output_file_written(logger, metrics_file)

    logger.info("Validation mode completed successfully")
    return True

def run_full_pipeline(args):
    """Run both simulation and validation modes."""
    logger.info("Starting full pipeline...")
    success_sim = run_simulation_mode(args)
    if not success_sim:
        logger.error("Simulation failed. Aborting pipeline.")
        return False

    success_val = run_validation_mode(args)
    if not success_val:
        logger.error("Validation failed. Aborting pipeline.")
        return False

    # Generate report
    logger.info("Generating validation report...")
    report_file = 'data/reports/validation_report.md'
    generate_report(report_file)
    log_output_file_written(logger, report_file)

    logger.info("Full pipeline completed successfully")
    return True

def main():
    args = parse_args()
    validate_args(args)

    try:
        if args.mode == 'simulation':
            success = run_simulation_mode(args)
        elif args.mode == 'validation':
            success = run_validation_mode(args)
        elif args.mode == 'full':
            success = run_full_pipeline(args)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            success = False

        if success:
            print("Pipeline completed successfully.")
            sys.exit(0)
        else:
            print("Pipeline failed.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Critical error: {e}")
        log_error_details(logger, e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
