#!/usr/bin/env python3
"""
Main entry point for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

This script orchestrates the full benchmark execution, handling configuration loading,
task execution with timeout enforcement, seed management, and report generation.

Usage:
    python src/benchmark/run_benchmark.py --config default.yaml --mode heterogeneous --seeds 5
"""
import argparse
import os
import sys
import time
import random
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Project imports based on existing API surface
from src.utils.logging import setup_logger, get_logger, log_random_seed, log_configuration
from src.utils.timeout import enforce_timeout, TimeoutError
from src.tasks.task_runner import TaskRunner
from src.evaluation.report_generator import generate_csv_report, generate_pdf_report
from src.utils.versioning import update_artifact_timestamp

# Constants
DEFAULT_CONFIG_PATH = "src/benchmark/config/default.yaml"
RESULTS_DIR = "data"
LOG_DIR = "logs"
STATE_DIR = "state"

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the Heterogeneous Scientific Foundation Model Collaboration Benchmark"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to the configuration YAML file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["heterogeneous", "unified"],
        default="heterogeneous",
        help="Execution mode: 'heterogeneous' (modality-specific models) or 'unified' (text translation)"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=5,
        help="Number of random seeds to run the benchmark with (default: 5)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=14400,  # 4 hours in seconds
        help="Total timeout for the entire benchmark run in seconds (default: 14400)"
    )
    return parser.parse_args()

def load_config(config_path: str) -> Dict[str, Any]:
    """Load and validate configuration from YAML file."""
    logger = get_logger(__name__)
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required keys
    required_keys = ["datasets", "modalities", "seeds", "timeout_per_task", "bootstrap_resamples"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    logger.info(f"Configuration loaded from {config_path}")
    logger.info(f"Mode: {config.get('mode', 'heterogeneous')}, Seeds: {config.get('seeds', 5)}")
    
    return config

def setup_directories() -> None:
    """Ensure all required output directories exist."""
    directories = [RESULTS_DIR, LOG_DIR, STATE_DIR, "data/processed"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured directories exist: {directories}")

def run_single_seed(seed: int, config: Dict[str, Any], mode: str, task_runner: TaskRunner) -> List[Dict[str, Any]]:
    """
    Execute the benchmark for a single random seed.
    
    Args:
        seed: Random seed for reproducibility
        config: Configuration dictionary
        mode: Execution mode ('heterogeneous' or 'unified')
        task_runner: Initialized TaskRunner instance
        
    Returns:
        List of result dictionaries for this seed
    """
    logger = get_logger(__name__)
    random.seed(seed)
    log_random_seed(seed)
    
    logger.info(f"Starting benchmark run for seed={seed}, mode={mode}")
    
    results = []
    timeout_per_task = config.get("timeout_per_task", 300)
    
    # Process each task defined in the configuration
    for task_def in config.get("tasks", []):
        task_id = task_def.get("task_id")
        if not task_id:
            logger.warning("Skipping task without ID")
            continue
        
        logger.info(f"Running task: {task_id}")
        
        try:
            # Enforce timeout for individual task
            result = enforce_timeout(
                task_runner.run_task,
                timeout_seconds=timeout_per_task
            )(task_id, mode=mode)
            
            result["seed"] = seed
            result["mode"] = mode
            result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            results.append(result)
            logger.info(f"Task {task_id} completed successfully")
            
        except TimeoutError as e:
            logger.error(f"Task {task_id} timed out after {timeout_per_task}s: {e}")
            results.append({
                "task_id": task_id,
                "seed": seed,
                "mode": mode,
                "status": "timeout",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
        except Exception as e:
            logger.error(f"Task {task_id} failed with error: {e}")
            results.append({
                "task_id": task_id,
                "seed": seed,
                "mode": mode,
                "status": "error",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
    
    return results

def main():
    """Main entry point for the benchmark runner."""
    args = parse_args()
    
    # Setup logging
    log_file_path = Path(LOG_DIR) / f"benchmark_{time.strftime('%Y%m%d_%H%M%S')}.log"
    logger = setup_logger(
        name="benchmark_runner",
        log_file=str(log_file_path),
        level=logging.INFO
    )
    
    logger.info("=" * 60)
    logger.info("Starting Heterogeneous Scientific Foundation Model Collaboration Benchmark")
    logger.info("=" * 60)
    logger.info(f"Arguments: config={args.config}, mode={args.mode}, seeds={args.seeds}")
    
    # Setup directories
    setup_directories()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override mode from CLI if provided
        execution_mode = args.mode
        config["mode"] = execution_mode
        log_configuration(config)
        
        # Initialize TaskRunner
        task_runner = TaskRunner(config=config)
        
        # Collect all results across seeds
        all_results = []
        total_start_time = time.time()
        
        for seed in range(args.seeds):
            seed_results = run_single_seed(seed, config, execution_mode, task_runner)
            all_results.extend(seed_results)
        
        total_duration = time.time() - total_start_time
        logger.info(f"Total benchmark execution time: {total_duration:.2f} seconds")
        
        # Generate reports
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        csv_output_path = Path(RESULTS_DIR) / f"results_{timestamp_str}.csv"
        pdf_output_path = Path(RESULTS_DIR) / f"summary_{timestamp_str}.pdf"
        
        logger.info(f"Generating CSV report at: {csv_output_path}")
        generate_csv_report(all_results, str(csv_output_path))
        
        logger.info(f"Generating PDF report at: {pdf_output_path}")
        generate_pdf_report(all_results, str(pdf_output_path))
        
        # Update state timestamp
        update_artifact_timestamp(str(log_file_path))
        
        logger.info("=" * 60)
        logger.info("Benchmark completed successfully")
        logger.info(f"Results saved to: {csv_output_path}")
        logger.info(f"Summary saved to: {pdf_output_path}")
        logger.info("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during benchmark execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
