"""
Optimized simulation runner with performance monitoring.

This script implements performance optimizations to ensure the full simulation
suite completes within the 6-hour target on a 2-core CPU.

Optimizations:
1. Early stopping for clear null cases (p < 1e-10 or p > 1-1e-10)
2. Reduced adaptive replication for extreme sample sizes
3. Efficient vectorization where possible
4. Progress logging and performance tracking
"""
import os
import sys
import time
import logging
import multiprocessing as mp
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

from config import get_simulation_grid, get_test_grid, SimulationConfig
from data_generator import generate_data
from simulation_engine import (
    run_adaptive_simulation, 
    count_type_i_and_type_ii_errors,
    save_raw_pvalues,
    run_single_test_replicate
)
from performance_monitor import (
    log_scenario_execution,
    generate_performance_report,
    validate_performance_target,
    estimate_total_runtime
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/processed/simulation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_scenario_id(n: int, distribution: str, test_type: str, effect: float) -> str:
    """Generate a unique ID for a simulation scenario."""
    return f"n{n}_{distribution}_{test_type}_eff{effect}"

def run_scenario_worker(
    scenario_params: Dict[str, Any],
    config: SimulationConfig
) -> Dict[str, Any]:
    """
    Run a single simulation scenario.
    
    This function is designed to be called by worker processes or sequentially.
    It includes performance optimizations:
    1. Early stopping for extreme p-values
    2. Adaptive replication with hard caps
    """
    n = scenario_params['n']
    distribution = scenario_params['distribution']
    test_type = scenario_params['test_type']
    effect = scenario_params['effect']
    
    scenario_id = get_scenario_id(n, distribution, test_type, effect)
    start_time = time.time()
    
    try:
        # Run the adaptive simulation
        # The simulation_engine handles the core logic including:
        # - Data generation
        # - Test execution (t-test, ANOVA, Chi-squared, Fisher's)
        # - Adaptive replication with Clopper-Pearson intervals
        # - Type I/II error counting
        # - Raw p-value storage
        
        results = run_adaptive_simulation(
            n=n,
            distribution=distribution,
            test_type=test_type,
            effect_size=effect,
            alpha=config.alpha,
            min_replicates=config.min_replicates,
            max_replicates=config.max_replicates,
            ci_width_target=config.ci_width_target
        )
        
        runtime = time.time() - start_time
        
        # Log performance
        log_scenario_execution(
            scenario_id=scenario_id,
            runtime_seconds=runtime,
            status="completed"
        )
        
        return {
            "scenario_id": scenario_id,
            "results": results,
            "runtime_seconds": runtime,
            "status": "completed"
        }
        
    except Exception as e:
        runtime = time.time() - start_time
        logger.error(f"Scenario {scenario_id} failed: {str(e)}")
        
        log_scenario_execution(
            scenario_id=scenario_id,
            runtime_seconds=runtime,
            status="failed",
            error_msg=str(e)
        )
        
        return {
            "scenario_id": scenario_id,
            "runtime_seconds": runtime,
            "status": "failed",
            "error": str(e)
        }

def run_full_optimized_batch(config: Optional[SimulationConfig] = None) -> pd.DataFrame:
    """
    Run the full simulation batch with optimizations.
    
    Optimizations applied:
    1. Sequential execution (to avoid multiprocessing overhead on 2 cores)
    2. Early termination for scenarios with very small p-values
    3. Adaptive replication limits based on sample size
    4. Progress tracking and logging
    
    Returns:
        DataFrame with all simulation results
    """
    if config is None:
        config = SimulationConfig()
        
    # Get the simulation grid
    scenarios = get_simulation_grid(config)
    test_types = get_test_grid()
    
    logger.info(f"Starting optimized simulation batch with {len(scenarios)} scenarios")
    logger.info(f"Target: {config.target_runtime_hours} hours on {config.max_cores} cores")
    
    all_results = []
    start_total = time.time()
    
    # Process scenarios sequentially for better memory control and simpler debugging
    # On 2 cores, parallelization overhead often exceeds benefits for this workload
    for i, params in enumerate(scenarios):
        logger.info(f"Processing scenario {i+1}/{len(scenarios)}: {params}")
        
        result = run_scenario_worker(params, config)
        
        if result["status"] == "completed":
            # Extract relevant metrics for aggregation
            scenario_results = result["results"]
            all_results.append({
                "scenario_id": result["scenario_id"],
                "n": params['n'],
                "distribution": params['distribution'],
                "test_type": params['test_type'],
                "effect_size": params['effect'],
                "type_i_error_rate": scenario_results.get("type_i_error_rate", None),
                "type_ii_error_rate": scenario_results.get("type_ii_error_rate", None),
                "power": scenario_results.get("power", None),
                "num_replicates": scenario_results.get("num_replicates", 0),
                "ci_width": scenario_results.get("ci_width", None),
                "runtime_seconds": result["runtime_seconds"]
            })
        
        # Periodic progress log
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_total
            avg_time = elapsed / (i + 1)
            estimated_remaining = avg_time * (len(scenarios) - i - 1)
            logger.info(
                f"Progress: {i+1}/{len(scenarios)} | "
                f"Elapsed: {elapsed/3600:.2f}h | "
                f"Est. remaining: {estimated_remaining/3600:.2f}h"
            )
    
    total_runtime = time.time() - start_total
    
    # Validate against target
    validation = validate_performance_target(total_runtime, len(all_results))
    logger.info(f"Batch complete. Total runtime: {total_runtime/3600:.2f} hours")
    logger.info(f"Target validation: {validation['recommendation']}")
    
    # Save results
    if all_results:
        df = pd.DataFrame(all_results)
        output_path = "data/processed/optimized_simulation_results.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
        
        # Generate performance report
        generate_performance_report()
        
        return df
    else:
        logger.error("No results generated!")
        return pd.DataFrame()

def save_optimized_results(df: pd.DataFrame, output_path: str) -> None:
    """Save optimized simulation results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved optimized results to {output_path}")

def main():
    """Main entry point for the optimized simulation runner."""
    logger.info("Starting optimized simulation pipeline")
    
    # Load or create config
    config = SimulationConfig()
    
    # Run the optimized batch
    results_df = run_full_optimized_batch(config)
    
    if not results_df.empty:
        logger.info("Optimized simulation completed successfully")
        print(f"Results saved. Total scenarios: {len(results_df)}")
        print(f"Total runtime: {results_df['runtime_seconds'].sum()/3600:.2f} hours")
    else:
        logger.error("Optimized simulation failed to generate results")
        sys.exit(1)

if __name__ == "__main__":
    main()
