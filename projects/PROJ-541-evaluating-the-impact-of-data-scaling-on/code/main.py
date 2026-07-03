import os
import sys
import time
import logging
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime

# Local imports based on provided API surface
from simulation.config import SimulationConfig
from simulation.generator import generate_synthetic_data
from simulation.persistence import save_synthetic_data
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import ScalingMethod, TestResult, run_pipeline
from utils.env import configure_cpu_only

# Configure logging
from simulation.logger import setup_logger
logger = setup_logger("main")

# Constants
RESULTS_DIR = Path("results")
DATA_DIR = Path("data")
CHECKPOINT_FILE = RESULTS_DIR / "checkpoint.json"
PARTIAL_RESULTS_FILE = RESULTS_DIR / "simulation_results_partial.csv"
FINAL_RESULTS_FILE = RESULTS_DIR / "simulation_results.csv"
SUMMARY_REPORT_FILE = RESULTS_DIR / "execution_summary.json"

# Time threshold for hard stop (in seconds) - Configurable
DEFAULT_TIME_THRESHOLD_SECONDS = 300  # 5 minutes default for safety

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        RESULTS_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "scaled",
        DATA_DIR / "scaled" / "standardized",
        DATA_DIR / "scaled" / "minmax",
        DATA_DIR / "scaled" / "robust",
        DATA_DIR / "synthetic",
        DATA_DIR / "config",
        RESULTS_DIR / "figures",
        Path("logs")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def get_scaling_functions() -> Dict[str, Callable]:
    """Map scaling method names to their functions."""
    return {
        "standardize": standardize_data,
        "minmax": min_max_scale,
        "robust": robust_scale
    }

def save_checkpoint(iteration_count: int, start_time: float, config: Dict[str, Any]):
    """Save partial results and checkpoint state."""
    checkpoint_data = {
        "completed_iterations": iteration_count,
        "start_time": start_time,
        "config_snapshot": config,
        "timestamp": datetime.now().isoformat(),
        "status": "interrupted"
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)
    logger.info(f"Checkpoint saved: {iteration_count} iterations completed.")

def save_partial_results(results: List[TestResult], filename: str):
    """Save current batch of results to CSV."""
    if not results:
        return
    
    fieldnames = [
        "iteration", "scaling_method", "distribution_type", 
        "sample_size", "mean_diff", "p_value", "test_type", 
        "is_significant", "timestamp"
    ]
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "iteration": r.iteration,
                "scaling_method": r.scaling_method,
                "distribution_type": r.distribution_type,
                "sample_size": r.sample_size,
                "mean_diff": r.mean_diff,
                "p_value": r.p_value,
                "test_type": r.test_type,
                "is_significant": r.is_significant,
                "timestamp": r.timestamp.isoformat() if hasattr(r, 'timestamp') else str(datetime.now())
            })
    logger.info(f"Partial results saved to {filename}")

def generate_summary_report(iteration_count: int, start_time: float, elapsed: float, reason: str):
    """Generate and save the execution summary report."""
    report = {
        "total_completed_iterations": iteration_count,
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "stop_time": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "stop_reason": reason,
        "partial_results_file": str(PARTIAL_RESULTS_FILE),
        "checkpoint_file": str(CHECKPOINT_FILE)
    }
    
    with open(SUMMARY_REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary to stdout as requested
    print(f"=== EXECUTION SUMMARY ===")
    print(f"Completed Iterations: {iteration_count}")
    print(f"Reason for Stop: {reason}")
    print(f"Elapsed Time: {elapsed:.2f} seconds")
    print(f"Partial Results: {PARTIAL_RESULTS_FILE}")
    print("=========================")
    
    logger.info(f"Summary report generated: {iteration_count} iterations completed due to {reason}")

def run_simulation_loop(config: SimulationConfig, time_threshold: int = DEFAULT_TIME_THRESHOLD_SECONDS):
    """
    Run the simulation loop with checkpointing and time-based hard stop.
    
    Args:
        config: Simulation configuration object
        time_threshold: Maximum seconds to run before hard stop
    
    Returns:
        Tuple of (completed_iterations, results_list)
    """
    ensure_directories()
    start_time = time.time()
    all_results: List[TestResult] = []
    iteration = 0
    scaling_funcs = get_scaling_functions()
    
    logger.info(f"Starting simulation loop with time threshold: {time_threshold}s")
    
    # Define iteration batches for checkpointing
    batch_size = 10
    
    try:
        while True:
            # Check time threshold
            elapsed = time.time() - start_time
            if elapsed >= time_threshold:
                logger.warning(f"Time threshold ({time_threshold}s) exceeded. Initiating hard stop.")
                save_checkpoint(iteration, start_time, config.to_dict() if hasattr(config, 'to_dict') else vars(config))
                save_partial_results(all_results, str(PARTIAL_RESULTS_FILE))
                generate_summary_report(iteration, start_time, elapsed, "Time threshold exceeded")
                return iteration, all_results
            
            # Run a batch of iterations
            batch_results = []
            for _ in range(batch_size):
                iteration += 1
                
                # Generate synthetic data
                try:
                    data, mean_diff, is_valid, error_msg = generate_synthetic_data(config)
                    if not is_valid:
                        logger.warning(f"Iteration {iteration}: {error_msg}")
                        continue
                    
                    # Run pipeline for each scaling method
                    for method_name, scale_func in scaling_funcs.items():
                        try:
                            result = run_pipeline(data, scale_func, method_name, iteration)
                            batch_results.append(result)
                            all_results.append(result)
                        except Exception as e:
                            logger.error(f"Pipeline failed for {method_name} at iter {iteration}: {e}")
                            
                except Exception as e:
                    logger.error(f"Data generation failed at iter {iteration}: {e}")
                    continue
                
                # Check time again after batch
                if time.time() - start_time >= time_threshold:
                    break
            
            # Save checkpoint periodically if we have results
            if batch_results and iteration % (batch_size * 5) == 0:
                save_checkpoint(iteration, start_time, config.to_dict() if hasattr(config, 'to_dict') else vars(config))
                
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        logger.info("Interrupted by user.")
        save_checkpoint(iteration, start_time, config.to_dict() if hasattr(config, 'to_dict') else vars(config))
        save_partial_results(all_results, str(PARTIAL_RESULTS_FILE))
        generate_summary_report(iteration, start_time, elapsed, "KeyboardInterrupt")
        return iteration, all_results
        
    return iteration, all_results

def main():
    """Main entry point for the simulation pipeline."""
    # Configure CPU constraints
    configure_cpu_only()
    
    # Create a default config for demonstration
    # In a real scenario, this would be loaded from a YAML file
    config = SimulationConfig(
        n_iterations=1000,
        sample_size=100,
        distribution_types=["normal", "skewed", "heteroscedastic"],
        scaling_methods=["standardize", "minmax", "robust"],
        alpha=0.05
    )
    
    logger.info("Starting main simulation pipeline...")
    
    # Run with a time threshold (default 300s, but can be adjusted)
    # For testing purposes, we might use a shorter threshold
    iterations, results = run_simulation_loop(config, time_threshold=300)
    
    # If the loop finished without a hard stop, save final results
    if len(results) > 0:
        save_partial_results(results, str(FINAL_RESULTS_FILE))
        logger.info(f"Simulation complete. {len(results)} results saved to {FINAL_RESULTS_FILE}")
        
        # Generate final summary if not already done
        if not SUMMARY_REPORT_FILE.exists():
            generate_summary_report(
                iterations, 
                time.time() - (300 if iterations > 0 else 0), 
                time.time() - (time.time() - 300 if iterations > 0 else time.time()),
                "Completed normally"
            )
    else:
        logger.warning("No results were generated.")

if __name__ == "__main__":
    main()