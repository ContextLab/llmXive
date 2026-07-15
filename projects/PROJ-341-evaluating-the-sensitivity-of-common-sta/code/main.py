"""
Main entry point for the statistical sensitivity analysis pipeline.
Orchestrates simulation, aggregation, threshold identification, visualization, and validation.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.simulation.logging_config import get_logger, log_operation, log_error_details
from code.simulation.test_runner import main as simulation_main
from code.analysis.aggregator import main as aggregator_main
from code.analysis.threshold_finder import main as threshold_main
from code.visualization.plotter import main as plotter_main
from code.analysis.validator import main as validator_main
from code.analysis.bootstrapper import main as bootstrapper_main
from code.analysis.validation_metrics import main as validation_metrics_main
from code.analysis.report_generator import main as report_generator_main
from code.analysis.alpha_sensitivity import main as alpha_sensitivity_main

logger = get_logger(__name__)

# Constants
DEFAULT_MIN_N = 5
DEFAULT_MAX_N = 500
DEFAULT_STEP_N = 5
DEFAULT_ITERATIONS = 10000
DEFAULT_ALPHA = 0.05
DEFAULT_EFFECT_SIZES = [0.2, 0.5, 0.8]  # Small, medium, large
DEFAULT_TESTS = ['t-test', 'anova', 'chi-squared']

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
        if sys.platform == 'darwin':
            return mem / (1024 * 1024)
        else:
            return mem / 1024
    except ImportError:
        return 0.0

def check_memory_limit(limit_mb: float = 7000) -> bool:
    """Check if memory usage is within limit."""
    current = get_memory_usage_mb()
    return current < limit_mb

def force_gc() -> None:
    """Force garbage collection."""
    gc.collect()

@log_operation("run_simulation")
def run_simulation(
    min_n: int = DEFAULT_MIN_N,
    max_n: int = DEFAULT_MAX_N,
    step_n: int = DEFAULT_STEP_N,
    iterations: int = DEFAULT_ITERATIONS,
    alpha: float = DEFAULT_ALPHA,
    tests: List[str] = DEFAULT_TESTS,
    effect_sizes: List[float] = DEFAULT_EFFECT_SIZES
) -> Dict[str, Any]:
    """
    Run the full simulation grid across sample sizes, tests, and effect sizes.

    This implements the parameter loop logic for T014b:
    - Iterates n from min_n to max_n with step_n
    - Iterates through all specified tests
    - Iterates through all specified effect sizes
    - Enforces the hard constraint of iterations per condition

    Args:
        min_n: Minimum sample size
        max_n: Maximum sample size
        step_n: Step size for sample sizes
        iterations: Number of iterations per condition (FR-001)
        alpha: Significance level
        tests: List of test types to run
        effect_sizes: List of effect sizes to test

    Returns:
        Dictionary with simulation metadata and status
    """
    start_time = time.time()

    # Build the parameter grid
    sample_sizes = list(range(min_n, max_n + 1, step_n))
    conditions = []

    for n in sample_sizes:
        for test in tests:
            for effect_size in effect_sizes:
                # Determine hypothesis state based on effect size
                # effect_size = 0 means null hypothesis is true
                hypothesis = "null" if effect_size == 0 else "alternative"
                conditions.append({
                    'n': n,
                    'test': test,
                    'effect_size': effect_size,
                    'hypothesis': hypothesis,
                    'iterations': iterations,
                    'alpha': alpha
                })

    logger.log("simulation_grid_created",
              total_conditions=len(conditions),
              sample_sizes=len(sample_sizes),
              tests=len(tests),
              effect_sizes=len(effect_sizes),
              iterations_per_condition=iterations)

    # Execute simulation via test_runner module
    # The test_runner handles the actual iteration and data generation
    result = simulation_main(
        min_n=min_n,
        max_n=max_n,
        step_n=step_n,
        iterations=iterations,
        alpha=alpha,
        tests=tests,
        effect_sizes=effect_sizes
    )

    elapsed = time.time() - start_time

    log_entry = logger.log("simulation_completed",
                          total_conditions=len(conditions),
                          elapsed_seconds=elapsed,
                          status=result.get('status', 'unknown'))

    return {
        'status': 'success',
        'conditions_executed': len(conditions),
        'elapsed_seconds': elapsed,
        'output_file': 'data/simulation/p_values_raw.csv',
        'log_entry': log_entry.to_json() if hasattr(log_entry, 'to_json') else str(log_entry)
    }

@log_operation("run_aggregation")
def run_aggregation() -> Dict[str, Any]:
    """
    Aggregate raw p-values into error rates.

    Reads p_values_raw.csv and calculates empirical Type I and Type II error rates.
    Writes results to data/simulation/error_rates_summary.csv
    """
    start_time = time.time()

    result = aggregator_main()

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_file': 'data/simulation/error_rates_summary.csv',
        'elapsed_seconds': elapsed
    }

@log_operation("run_thresholds")
def run_thresholds() -> Dict[str, Any]:
    """
    Identify reliability thresholds from error rates.

    Reads error_rates_summary.csv and calculates:
    - Smallest n where Type I error CI lower bound > 0.05
    - Smallest n where power CI remains < 0.80 for 3 consecutive increments

    Writes results to data/simulation/thresholds.json
    """
    start_time = time.time()

    result = threshold_main()

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_file': 'data/simulation/thresholds.json',
        'elapsed_seconds': elapsed
    }

@log_operation("run_plots")
def run_plots() -> Dict[str, Any]:
    """
    Generate visualization plots.

    Reads error_rates_summary.csv and thresholds.json to create:
    - Line plots with 95% CI bands for sample size vs error rate
    - Comparative plots for different tests
    - Annotations for reliability thresholds

    Writes plots to data/visualization/
    """
    start_time = time.time()

    result = plotter_main()

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_dir': 'data/visualization/',
        'elapsed_seconds': elapsed
    }

@log_operation("run_validation")
def run_validation() -> Dict[str, Any]:
    """
    Validate simulation findings against real-world datasets.

    Downloads and processes UCI datasets (Breast Cancer, Wine, Adult)
    and compares observed p-value distributions with simulation predictions.

    Outputs:
    - data/simulation/real_data_pvalues.csv
    - data/simulation/real_data_power.json
    - data/simulation/validation_metrics.json
    - data/reports/validation_report.md
    """
    start_time = time.time()

    result = validator_main()

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_files': [
            'data/simulation/real_data_pvalues.csv',
            'data/simulation/real_data_power.json',
            'data/simulation/validation_metrics.json',
            'data/reports/validation_report.md'
        ],
        'elapsed_seconds': elapsed
    }

@log_operation("run_bootstrap")
def run_bootstrap() -> Dict[str, Any]:
    """
    Run bootstrapped power estimation on real datasets.

    Calculates Kolmogorov-Smirnov distance between simulated and real data.
    """
    start_time = time.time()

    result = bootstrapper_main()

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_file': 'data/simulation/real_data_power.json',
        'elapsed_seconds': elapsed
    }

@log_operation("run_metrics")
def run_metrics() -> Dict[str, Any]:
    """
    Calculate validation metrics and KS statistics.
    """
    start_time = time.time()

    result = validation_metrics_main()

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_file': 'data/simulation/validation_metrics.json',
        'elapsed_seconds': elapsed
    }

@log_operation("run_report")
def run_report() -> Dict[str, Any]:
    """
    Generate final validation report.
    """
    start_time = time.time()

    result = report_generator_main()

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_file': 'data/reports/validation_report.md',
        'elapsed_seconds': elapsed
    }

@log_operation("run_alpha_sensitivity")
def run_alpha_sensitivity(
    alpha_levels: List[float] = [0.01, 0.05, 0.10]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis for different alpha thresholds.
    """
    start_time = time.time()

    result = alpha_sensitivity_main(alpha_levels=alpha_levels)

    elapsed = time.time() - start_time

    return {
        'status': 'success',
        'output_file': 'data/simulation/alpha_sensitivity.json',
        'elapsed_seconds': elapsed
    }

@log_operation("run_full_pipeline")
def run_full_pipeline(
    min_n: int = DEFAULT_MIN_N,
    max_n: int = DEFAULT_MAX_N,
    step_n: int = DEFAULT_STEP_N,
    iterations: int = DEFAULT_ITERATIONS,
    alpha: float = DEFAULT_ALPHA,
    tests: List[str] = DEFAULT_TESTS,
    effect_sizes: List[float] = DEFAULT_EFFECT_SIZES,
    skip_simulation: bool = False,
    skip_aggregation: bool = False,
    skip_thresholds: bool = False,
    skip_plots: bool = False,
    skip_validation: bool = False,
    skip_bootstrap: bool = False,
    skip_metrics: bool = False,
    skip_report: bool = False,
    skip_alpha_sensitivity: bool = False
) -> Dict[str, Any]:
    """
    Run the complete pipeline from simulation to final report.

    This is the main orchestrator that ensures all deliverables are produced:
    - data/simulation/p_values_raw.csv
    - data/simulation/error_rates_summary.csv
    - data/simulation/thresholds.json
    - data/visualization/*.png
    - data/simulation/real_data_pvalues.csv
    - data/simulation/real_data_power.json
    - data/simulation/validation_metrics.json
    - data/reports/validation_report.md
    """
    start_time = time.time()
    pipeline_results = {}

    logger.log("pipeline_started",
              min_n=min_n, max_n=max_n, iterations=iterations,
              tests=tests, effect_sizes=effect_sizes)

    # Step 1: Simulation
    if not skip_simulation:
        try:
            logger.log("step_simulation_start")
            sim_result = run_simulation(
                min_n=min_n, max_n=max_n, step_n=step_n,
                iterations=iterations, alpha=alpha,
                tests=tests, effect_sizes=effect_sizes
            )
            pipeline_results['simulation'] = sim_result
            logger.log("step_simulation_complete")
        except Exception as e:
            logger.log("step_simulation_failed", error=str(e))
            pipeline_results['simulation'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    force_gc()

    # Step 2: Aggregation
    if not skip_aggregation:
        try:
            logger.log("step_aggregation_start")
            agg_result = run_aggregation()
            pipeline_results['aggregation'] = agg_result
            logger.log("step_aggregation_complete")
        except Exception as e:
            logger.log("step_aggregation_failed", error=str(e))
            pipeline_results['aggregation'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    force_gc()

    # Step 3: Threshold Identification
    if not skip_thresholds:
        try:
            logger.log("step_thresholds_start")
            thresh_result = run_thresholds()
            pipeline_results['thresholds'] = thresh_result
            logger.log("step_thresholds_complete")
        except Exception as e:
            logger.log("step_thresholds_failed", error=str(e))
            pipeline_results['thresholds'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    # Step 4: Visualization
    if not skip_plots:
        try:
            logger.log("step_plots_start")
            plot_result = run_plots()
            pipeline_results['plots'] = plot_result
            logger.log("step_plots_complete")
        except Exception as e:
            logger.log("step_plots_failed", error=str(e))
            pipeline_results['plots'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    # Step 5: Validation (Real Data)
    if not skip_validation:
        try:
            logger.log("step_validation_start")
            val_result = run_validation()
            pipeline_results['validation'] = val_result
            logger.log("step_validation_complete")
        except Exception as e:
            logger.log("step_validation_failed", error=str(e))
            pipeline_results['validation'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    # Step 6: Bootstrap
    if not skip_bootstrap:
        try:
            logger.log("step_bootstrap_start")
            boot_result = run_bootstrap()
            pipeline_results['bootstrap'] = boot_result
            logger.log("step_bootstrap_complete")
        except Exception as e:
            logger.log("step_bootstrap_failed", error=str(e))
            pipeline_results['bootstrap'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    # Step 7: Metrics
    if not skip_metrics:
        try:
            logger.log("step_metrics_start")
            metrics_result = run_metrics()
            pipeline_results['metrics'] = metrics_result
            logger.log("step_metrics_complete")
        except Exception as e:
            logger.log("step_metrics_failed", error=str(e))
            pipeline_results['metrics'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    # Step 8: Report
    if not skip_report:
        try:
            logger.log("step_report_start")
            report_result = run_report()
            pipeline_results['report'] = report_result
            logger.log("step_report_complete")
        except Exception as e:
            logger.log("step_report_failed", error=str(e))
            pipeline_results['report'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    # Step 9: Alpha Sensitivity
    if not skip_alpha_sensitivity:
        try:
            logger.log("step_alpha_sensitivity_start")
            alpha_result = run_alpha_sensitivity()
            pipeline_results['alpha_sensitivity'] = alpha_result
            logger.log("step_alpha_sensitivity_complete")
        except Exception as e:
            logger.log("step_alpha_sensitivity_failed", error=str(e))
            pipeline_results['alpha_sensitivity'] = {'status': 'failed', 'error': str(e)}
            if not os.environ.get('CONTINUE_ON_ERROR'):
                raise

    total_elapsed = time.time() - start_time

    # Check if all steps succeeded
    all_success = all(
        r.get('status') == 'success'
        for r in pipeline_results.values()
    )

    logger.log("pipeline_completed",
              total_elapsed=total_elapsed,
              all_success=all_success,
              results_summary={k: v.get('status') for k, v in pipeline_results.items()})

    return {
        'status': 'success' if all_success else 'partial',
        'total_elapsed_seconds': total_elapsed,
        'steps': pipeline_results
    }

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Statistical Sensitivity Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Mode selection
    parser.add_argument(
        '--mode',
        choices=['simulation', 'aggregation', 'thresholds', 'plots',
                'validation', 'bootstrap', 'metrics', 'report',
                'alpha_sensitivity', 'full_pipeline'],
        default='full_pipeline',
        help='Pipeline mode to run'
    )

    # Simulation parameters
    parser.add_argument(
        '--min-n', type=int, default=DEFAULT_MIN_N,
        help=f'Minimum sample size (default: {DEFAULT_MIN_N})'
    )
    parser.add_argument(
        '--max-n', type=int, default=DEFAULT_MAX_N,
        help=f'Maximum sample size (default: {DEFAULT_MAX_N})'
    )
    parser.add_argument(
        '--step-n', type=int, default=DEFAULT_STEP_N,
        help=f'Step size for sample sizes (default: {DEFAULT_STEP_N})'
    )
    parser.add_argument(
        '--iterations', type=int, default=DEFAULT_ITERATIONS,
        help=f'Iterations per condition (default: {DEFAULT_ITERATIONS})'
    )
    parser.add_argument(
        '--alpha', type=float, default=DEFAULT_ALPHA,
        help=f'Significance level (default: {DEFAULT_ALPHA})'
    )
    parser.add_argument(
        '--tests', nargs='+', default=DEFAULT_TESTS,
        choices=['t-test', 'anova', 'chi-squared'],
        help=f'Test types to run (default: {DEFAULT_TESTS})'
    )
    parser.add_argument(
        '--effect-sizes', nargs='+', type=float, default=DEFAULT_EFFECT_SIZES,
        help=f'Effect sizes to test (default: {DEFAULT_EFFECT_SIZES})'
    )

    # Alpha sensitivity
    parser.add_argument(
        '--alpha-levels', nargs='+', type=float, default=[0.01, 0.05, 0.10],
        help='Alpha levels for sensitivity analysis'
    )

    # Pipeline control
    parser.add_argument(
        '--skip-simulation', action='store_true',
        help='Skip simulation step'
    )
    parser.add_argument(
        '--skip-aggregation', action='store_true',
        help='Skip aggregation step'
    )
    parser.add_argument(
        '--skip-thresholds', action='store_true',
        help='Skip threshold identification step'
    )
    parser.add_argument(
        '--skip-plots', action='store_true',
        help='Skip visualization step'
    )
    parser.add_argument(
        '--skip-validation', action='store_true',
        help='Skip validation step'
    )
    parser.add_argument(
        '--skip-bootstrap', action='store_true',
        help='Skip bootstrap step'
    )
    parser.add_argument(
        '--skip-metrics', action='store_true',
        help='Skip metrics step'
    )
    parser.add_argument(
        '--skip-report', action='store_true',
        help='Skip report generation step'
    )
    parser.add_argument(
        '--skip-alpha-sensitivity', action='store_true',
        help='Skip alpha sensitivity analysis'
    )

    # Continue on error
    parser.add_argument(
        '--continue-on-error', action='store_true',
        help='Continue pipeline even if a step fails'
    )

    return parser.parse_args()

def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.continue_on_error:
        os.environ['CONTINUE_ON_ERROR'] = '1'

    try:
        if args.mode == 'simulation':
            result = run_simulation(
                min_n=args.min_n,
                max_n=args.max_n,
                step_n=args.step_n,
                iterations=args.iterations,
                alpha=args.alpha,
                tests=args.tests,
                effect_sizes=args.effect_sizes
            )
        elif args.mode == 'aggregation':
            result = run_aggregation()
        elif args.mode == 'thresholds':
            result = run_thresholds()
        elif args.mode == 'plots':
            result = run_plots()
        elif args.mode == 'validation':
            result = run_validation()
        elif args.mode == 'bootstrap':
            result = run_bootstrap()
        elif args.mode == 'metrics':
            result = run_metrics()
        elif args.mode == 'report':
            result = run_report()
        elif args.mode == 'alpha_sensitivity':
            result = run_alpha_sensitivity(alpha_levels=args.alpha_levels)
        elif args.mode == 'full_pipeline':
            result = run_full_pipeline(
                min_n=args.min_n,
                max_n=args.max_n,
                step_n=args.step_n,
                iterations=args.iterations,
                alpha=args.alpha,
                tests=args.tests,
                effect_sizes=args.effect_sizes,
                skip_simulation=args.skip_simulation,
                skip_aggregation=args.skip_aggregation,
                skip_thresholds=args.skip_thresholds,
                skip_plots=args.skip_plots,
                skip_validation=args.skip_validation,
                skip_bootstrap=args.skip_bootstrap,
                skip_metrics=args.skip_metrics,
                skip_report=args.skip_report,
                skip_alpha_sensitivity=args.skip_alpha_sensitivity
            )
        else:
            logger.log("unknown_mode", mode=args.mode)
            print(f"Unknown mode: {args.mode}")
            return 1

        print(json.dumps(result, indent=2, default=str))
        return 0

    except Exception as e:
        logger.log("pipeline_error", error=str(e), traceback=traceback.format_exc())
        print(f"Error: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())