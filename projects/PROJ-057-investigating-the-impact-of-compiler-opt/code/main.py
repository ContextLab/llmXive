"""
Main entry point for the Compiler Optimization Impact Investigation Pipeline.

Orchestrates the full experiment flow:
1. Generate Synthetic Tensors (Data)
2. Compile C++ Kernels with various flags
3. Execute Benchmarks and collect latency logs
4. Analyze Stability (NaN detection, Reference comparison)
5. Statistical Analysis and Visualization
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logging, get_logger
from benchmarks.config import create_default_manager
from benchmarks.tensor_generator import run_generation
from benchmarks.reference import run_reference_benchmarks
from benchmarks.compile_runner import CompileRunner
from benchmarks.executor import Executor
from analysis.stability_check import process_stability, save_stable_logs, save_unstable_audit
from analysis.stability_metrics_generator import aggregate_stability_metrics
from analysis.stats import load_latency_data, compute_block_averages, aggregate_block_averages, welch_ttest, compare_configurations, generate_comparison_report
from analysis.aggregator import aggregate_results, generate_final_pareto
from analysis.viz import generate_pareto_exploration, generate_pareto_final
from analysis.error_distribution_viz import plot_error_distribution, generate_error_distribution_summary

def main():
    parser = argparse.ArgumentParser(description="Run full compiler optimization benchmark suite.")
    parser.add_argument("--skip-generate", action="store_true", help="Skip tensor generation")
    parser.add_argument("--skip-reference", action="store_true", help="Skip reference calculation")
    parser.add_argument("--skip-compile", action="store_true", help="Skip compilation")
    parser.add_argument("--skip-execute", action="store_true", help="Skip execution")
    parser.add_argument("--skip-stability", action="store_true", help="Skip stability analysis")
    parser.add_argument("--skip-stats", action="store_true", help="Skip statistical analysis")
    parser.add_argument("--skip-viz", action="store_true", help="Skip visualization")
    parser.add_argument("--config", type=str, default=None, help="Path to custom config file")
    args = parser.parse_args()

    # Setup Logging
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_file=log_dir / "main_pipeline.log")
    logger.info("Starting Compiler Optimization Impact Investigation Pipeline")

    config_manager = create_default_manager()
    if args.config:
        config_manager.load_config(args.config)

    # 1. Generate Synthetic Tensors
    if not args.skip_generate:
        logger.info("Step 1: Generating synthetic tensors...")
        run_generation(
            output_dir=PROJECT_ROOT / "data" / "raw",
            config_manager=config_manager
        )
        logger.info("Step 1: Synthetic tensors generated.")
    else:
        logger.info("Step 1: Skipped.")

    # 2. Generate High-Precision Reference
    if not args.skip_reference:
        logger.info("Step 2: Generating high-precision reference tensors...")
        run_reference_benchmarks(
            input_dir=PROJECT_ROOT / "data" / "raw",
            output_dir=PROJECT_ROOT / "data" / "raw" / "reference"
        )
        logger.info("Step 2: Reference tensors generated.")
    else:
        logger.info("Step 2: Skipped.")

    # 3. Compile Kernels
    if not args.skip_compile:
        logger.info("Step 3: Compiling kernels with various optimization flags...")
        runner = CompileRunner(
            kernel_dir=PROJECT_ROOT / "code" / "kernels",
            output_dir=PROJECT_ROOT / "data" / "binaries",
            config_manager=config_manager
        )
        runner.compile_all()
        logger.info("Step 3: Compilation complete.")
    else:
        logger.info("Step 3: Skipped.")

    # 4. Execute Benchmarks
    if not args.skip_execute:
        logger.info("Step 4: Executing benchmarks...")
        executor = Executor(
            binary_dir=PROJECT_ROOT / "data" / "binaries",
            data_dir=PROJECT_ROOT / "data" / "raw",
            output_dir=PROJECT_ROOT / "data" / "intermediates" / "raw_logs",
            config_manager=config_manager
        )
        executor.run_all()
        logger.info("Step 4: Execution complete.")
    else:
        logger.info("Step 4: Skipped.")

    # 5. Stability Analysis
    if not args.skip_stability:
        logger.info("Step 5: Analyzing numerical stability...")
        raw_logs_dir = PROJECT_ROOT / "data" / "intermediates" / "raw_logs"
        reference_dir = PROJECT_ROOT / "data" / "raw" / "reference"
        
        # Process stability (NaN detection + Reference comparison)
        stability_results = process_stability(
            raw_logs_dir=raw_logs_dir,
            reference_dir=reference_dir,
            output_dir=PROJECT_ROOT / "data" / "intermediates"
        )
        
        # Save stable and unstable logs
        save_stable_logs(stability_results, PROJECT_ROOT / "data" / "results" / "stable_logs.jsonl")
        save_unstable_audit(stability_results, PROJECT_ROOT / "data" / "results" / "unstable_audit.jsonl")
        
        # Aggregate stability metrics
        aggregate_stability_metrics(
            stable_logs_path=PROJECT_ROOT / "data" / "results" / "stable_logs.jsonl",
            unstable_logs_path=PROJECT_ROOT / "data" / "results" / "unstable_audit.jsonl",
            output_path=PROJECT_ROOT / "data" / "results" / "stability_metrics.csv"
        )
        
        logger.info("Step 5: Stability analysis complete.")
    else:
        logger.info("Step 5: Skipped.")

    # 6. Statistical Analysis
    if not args.skip_stats:
        logger.info("Step 6: Performing statistical analysis...")
        raw_logs_dir = PROJECT_ROOT / "data" / "intermediates" / "raw_logs"
        
        # Load and process latency data
        latency_data = load_latency_data(raw_logs_dir)
        block_averages = compute_block_averages(latency_data)
        aggregated = aggregate_block_averages(block_averages)
        
        # Perform Welch's t-test
        comparison_report = generate_comparison_report(aggregated)
        
        # Save aggregated stats
        aggregated.to_csv(PROJECT_ROOT / "data" / "results" / "aggregated_stats.csv", index=False)
        comparison_report.to_csv(PROJECT_ROOT / "data" / "results" / "statistical_comparison.csv", index=False)
        
        logger.info("Step 6: Statistical analysis complete.")
    else:
        logger.info("Step 6: Skipped.")

    # 7. Visualization
    if not args.skip_viz:
        logger.info("Step 7: Generating visualizations...")
        stability_metrics_path = PROJECT_ROOT / "data" / "results" / "stability_metrics.csv"
        aggregated_stats_path = PROJECT_ROOT / "data" / "results" / "aggregated_stats.csv"
        
        # Generate Pareto Frontiers
        generate_pareto_exploration(
            stability_metrics_path=stability_metrics_path,
            stats_path=aggregated_stats_path,
            output_path=PROJECT_ROOT / "data" / "results" / "pareto_frontier_exploration.png"
        )
        
        generate_pareto_final(
            stability_metrics_path=stability_metrics_path,
            stats_path=aggregated_stats_path,
            output_path=PROJECT_ROOT / "data" / "results" / "pareto_frontier_final.png"
        )
        
        # Generate Error Distribution Plot
        plot_error_distribution(
            stability_metrics_path=stability_metrics_path,
            output_path=PROJECT_ROOT / "data" / "results" / "error_distribution.png"
        )
        
        generate_error_distribution_summary(
            stability_metrics_path=stability_metrics_path,
            output_path=PROJECT_ROOT / "data" / "results" / "error_distribution_summary.csv"
        )
        
        logger.info("Step 7: Visualizations complete.")
    else:
        logger.info("Step 7: Skipped.")

    logger.info("Pipeline execution finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())