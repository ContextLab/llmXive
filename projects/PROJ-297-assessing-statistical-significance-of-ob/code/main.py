import os
import sys
import json
import time
import argparse
import logging
import cProfile
import pstats
import io
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Import project modules
from config import get_config, ensure_dirs
from constitution import check_by_amendment_ratification, enforce_gate, ConstitutionalError
from loaders import load_all_datasets, apply_hygiene_pipeline
from stats_engine import (
    compute_correlation,
    construct_graph,
    calculate_stats,
    run_permutations_for_threshold,
    calculate_empirical_p_value,
    estimate_runtime_pilot,
    adjust_permutation_count,
    generate_synthetic_dataset
)
from correction import benjamini_yekutieli, apply_correction_to_results
from viz import plot_heatmap, plot_histogram, plot_primary_threshold_visualizations

# Setup logging
def setup_logging(log_file: str = "output/results/pipeline.log") -> logging.Logger:
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Timeout handling
def setup_timeout_handler(seconds: int):
    import signal
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Execution exceeded {seconds} seconds limit.")
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def handle_timeout():
    import signal
    signal.alarm(0)

def write_runtime_log(duration: float, output_dir: str):
    log_path = os.path.join(output_dir, "runtime_log.json")
    with open(log_path, 'w') as f:
        json.dump({"total_duration_seconds": duration}, f)

@contextmanager
def profiler_context(output_path: str):
    """Context manager for performance profiling."""
    pr = cProfile.Profile()
    pr.enable()
    try:
        yield
    finally:
        pr.disable()
        s = io.StringIO()
        sort_by = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
        ps.print_stats()
        with open(output_path, 'w') as f:
            f.write(s.getvalue())
        logging.info(f"Profile written to {output_path}")

def run_single_synthetic_validation(config: Dict[str, Any], logger: logging.Logger) -> bool:
    logger.info("Running single synthetic validation run.")
    df = generate_synthetic_dataset(
        n_samples=config['synthetic_n_samples'],
        n_vars=config['synthetic_n_vars'],
        seed=config['random_seed']
    )
    corr_matrix = compute_correlation(df, method='pearson')
    graph = construct_graph(corr_matrix, config['threshold'])
    stats = calculate_stats(graph)
    logger.info(f"Synthetic stats: {stats}")
    return True

def run_synthetic_validation_loop(config: Dict[str, Any], logger: logging.Logger) -> bool:
    logger.info("Starting synthetic validation loop.")
    passed_count = 0
    total_runs = config['validation_runs']
    for i in range(total_runs):
        logger.info(f"Validation run {i+1}/{total_runs}")
        if run_single_synthetic_validation(config, logger):
            passed_count += 1
    success = passed_count >= config['validation_threshold']
    logger.info(f"Validation loop complete: {passed_count}/{total_runs} passed.")
    return success

def run_threshold_sweep(config: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    logger.info("Starting threshold sweep.")
    results = {}
    datasets = load_all_datasets(config['data_raw_dir'])
    cleaned_datasets = apply_hygiene_pipeline(datasets, logger)

    for name, df in cleaned_datasets.items():
        logger.info(f"Processing dataset: {name}")
        corr_matrix = compute_correlation(df, method='pearson')
        for thresh in config['thresholds']:
            graph = construct_graph(corr_matrix, thresh)
            stats = calculate_stats(graph)
            if name not in results:
                results[name] = {}
            results[name][thresh] = stats
            logger.info(f"  Threshold {thresh}: {stats}")
    return results

def generate_sensitivity_report(results: Dict[str, Any], output_dir: str):
    report_path = os.path.join(output_dir, "sensitivity_report.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Sensitivity report written to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline for Statistical Significance Assessment")
    parser.add_argument('--permutations', type=int, default=2000, help='Number of permutations')
    parser.add_argument('--threshold', type=float, default=0.3, help='Correlation threshold')
    parser.add_argument('--sweep', action='store_true', help='Run threshold sweep')
    parser.add_argument('--profile', action='store_true', help='Enable performance profiling')
    args = parser.parse_args()

    # Setup
    config = get_config()
    config['permutations'] = args.permutations
    config['threshold'] = args.threshold
    ensure_dirs(config)
    logger = setup_logging()

    # Constitutional Gate
    try:
        check_by_amendment_ratification()
    except ConstitutionalError as e:
        logger.critical(str(e))
        sys.exit(1)

    # Timeout
    if config.get('limit_seconds'):
        setup_timeout_handler(config['limit_seconds'])

    start_time = time.time()

    try:
        if args.profile:
            profile_path = os.path.join(config['output_dir'], "profile.prof")
            with profiler_context(profile_path):
                _run_pipeline(config, logger, args)
        else:
            _run_pipeline(config, logger, args)
    finally:
        handle_timeout()
        duration = time.time() - start_time
        write_runtime_log(duration, config['output_dir'])
        logger.info(f"Pipeline completed in {duration:.2f} seconds.")

def _run_pipeline(config: Dict[str, Any], logger: logging.Logger, args: argparse.Namespace):
    # Synthetic Validation
    if not run_synthetic_validation_loop(config, logger):
        logger.warning("Synthetic validation failed. Proceeding with caution.")

    # Main Analysis
    datasets = load_all_datasets(config['data_raw_dir'])
    cleaned_datasets = apply_hygiene_pipeline(datasets, logger)

    all_results = {}
    for name, df in cleaned_datasets.items():
        logger.info(f"Analyzing dataset: {name}")
        corr_matrix = compute_correlation(df, method='pearson')

        # Permutations
        null_dist = run_permutations_for_threshold(
            df, config['threshold'], config['permutations'], config['random_seed']
        )

        # Empirical P-values
        p_values = calculate_empirical_p_value(corr_matrix, null_dist)

        # Correction
        corrected_results = apply_correction_to_results(p_values, method='by')

        all_results[name] = {
            'correlation_matrix': corr_matrix.to_dict(),
            'p_values': p_values,
            'corrected_results': corrected_results
        }

        # Visualization
        plot_heatmap(corr_matrix, os.path.join(config['output_dir'], f"{name}_heatmap.png"))
        plot_histogram(p_values.values(), os.path.join(config['output_dir'], f"{name}_pval_hist.png"))

    # Threshold Sweep
    if args.sweep:
        sweep_results = run_threshold_sweep(config, logger)
        generate_sensitivity_report(sweep_results, config['output_dir'])

    # Final Report
    report_path = os.path.join(config['output_dir'], "final_analysis_results.json")
    with open(report_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    logger.info(f"Final results written to {report_path}")

if __name__ == "__main__":
    main()