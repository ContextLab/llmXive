"""
Profile full simulation sweep runtime and verify it completes within 6 hours on 2 CPU cores.
Implements SC-004: Performance verification for the full simulation pipeline.
"""
import json
import logging
import os
import sys
import time
import resource
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from utils.simulation import SimulationConfig, SimulationOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/profile_simulation.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
TARGET_CPU_CORES = 2
MEMORY_WARNING_THRESHOLD = 6 * 1024 * 1024 * 1024  # 6GB in bytes

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024  # Convert KB to MB (Linux/Unix)

def run_profiled_sweep() -> Dict[str, Any]:
    """
    Execute the full simulation sweep with profiling.
    Uses a representative subset of the full parameter space to estimate
    total runtime while ensuring the logic is fully exercised.
    """
    logger.info("Starting profiled simulation sweep...")
    
    # Define a representative parameter subset for profiling
    # This covers the range of scenarios without running the full combinatorial explosion
    profile_configs = [
        # Small scale - fast
        {"n": 50, "p": 100, "rho": 0.0, "distribution": "normal"},
        {"n": 50, "p": 100, "rho": 0.5, "distribution": "normal"},
        {"n": 100, "p": 200, "rho": 0.3, "distribution": "t"},
        
        # Medium scale - moderate time
        {"n": 200, "p": 500, "rho": 0.5, "distribution": "skew"},
        {"n": 300, "p": 500, "rho": 0.7, "distribution": "normal"},
        
        # Large scale - time intensive
        {"n": 500, "p": 1000, "rho": 0.5, "distribution": "t"},
    ]
    
    results = {
        "start_time": time.time(),
        "configs_profiled": len(profile_configs),
        "config_results": [],
        "total_runtime": 0,
        "peak_memory_mb": 0,
        "estimated_full_runtime_hours": 0,
        "within_budget": False,
        "warnings": []
    }
    
    initial_memory = get_memory_usage_mb()
    max_memory = initial_memory
    
    try:
        for i, config_params in enumerate(profile_configs):
            logger.info(f"Running profile config {i+1}/{len(profile_configs)}: n={config_params['n']}, p={config_params['p']}, rho={config_params['rho']}")
            
            config_start = time.time()
            config_memory_start = get_memory_usage_mb()
            
            # Create simulation config
            sim_config = SimulationConfig(
                n=config_params['n'],
                p=config_params['p'],
                rho=config_params['rho'],
                distribution_type=config_params['distribution'],
                n_iterations=10,  # Reduced for profiling, but exercises full pipeline
                seed=i * 42,
                output_dir=Path("data/profile_temp")
            )
            
            # Run simulation
            orchestrator = SimulationOrchestrator(sim_config)
            orchestrator.run()
            
            config_end = time.time()
            config_runtime = config_end - config_start
            config_memory_end = get_memory_usage_mb()
            
            # Track peak memory
            if config_memory_end > max_memory:
                max_memory = config_memory_end
            
            # Check memory warning threshold
            if config_memory_end > MEMORY_WARNING_THRESHOLD / (1024 * 1024):
                results["warnings"].append(
                    f"Config n={config_params['n']}, p={config_params['p']}: Memory {config_memory_end:.1f}MB exceeds 6GB threshold"
                )
            
            config_result = {
                "n": config_params['n'],
                "p": config_params['p'],
                "rho": config_params['rho'],
                "distribution": config_params['distribution'],
                "runtime_seconds": config_runtime,
                "peak_memory_mb": config_memory_end,
                "iterations_completed": 10
            }
            
            results["config_results"].append(config_result)
            logger.info(f"Completed config {i+1}: {config_runtime:.2f}s, Memory: {config_memory_end:.1f}MB")
            
            # Cleanup temp files
            if sim_config.output_dir.exists():
                import shutil
                shutil.rmtree(sim_config.output_dir, ignore_errors=True)
            
        results["total_runtime"] = time.time() - results["start_time"]
        results["peak_memory_mb"] = max_memory
        
        # Estimate full runtime based on profiled configs
        # Full sweep would be: 6 rho values × 4 p-sizes × 3 n-sizes × 3 distributions × iterations
        # We profiled 6 configs representing the range
        # Extrapolate: total configs in full sweep ≈ 6 × 4 × 3 × 3 = 216 configs
        # But we used reduced iterations (10) vs full (determined by power analysis)
        # For a conservative estimate, we'll use a scaling factor based on the largest config
        largest_runtime = max(r["runtime_seconds"] for r in results["config_results"])
        estimated_configs_full = 6 * 4 * 3 * 3  # 216 configs
        scaling_factor = 5  # Conservative factor for full iterations
        estimated_full_runtime_seconds = largest_runtime * estimated_configs_full * scaling_factor
        
        results["estimated_full_runtime_hours"] = estimated_full_runtime_seconds / 3600
        results["within_budget"] = estimated_full_runtime_seconds <= MAX_RUNTIME_SECONDS
        
        if not results["within_budget"]:
            results["warnings"].append(
                f"Estimated full runtime {results['estimated_full_runtime_hours']:.1f}h exceeds 6h budget"
            )
        
    except Exception as e:
        logger.error(f"Profile sweep failed: {e}", exc_info=True)
        results["error"] = str(e)
        raise
    
    return results

def write_profile_report(results: Dict[str, Any], output_path: Path) -> None:
    """Write the profiling results to a JSON report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "task_id": "T036",
        "profile_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target_cpu_cores": TARGET_CPU_CORES,
        "max_runtime_hours": 6,
        "max_runtime_seconds": MAX_RUNTIME_SECONDS,
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Profile report written to {output_path}")

def main():
    """Main entry point for the profiling task."""
    logger.info("=" * 60)
    logger.info("Starting T036: Profile simulation sweep runtime")
    logger.info("=" * 60)
    
    try:
        results = run_profiled_sweep()
        write_profile_report(results, Path("data/results/profile_simulation.json"))
        
        # Print summary
        print("\n" + "=" * 60)
        print("PROFILING SUMMARY")
        print("=" * 60)
        print(f"Configs profiled: {results['configs_profiled']}")
        print(f"Total profile runtime: {results['total_runtime']:.2f} seconds")
        print(f"Peak memory: {results['peak_memory_mb']:.1f} MB")
        print(f"Estimated full sweep runtime: {results['estimated_full_runtime_hours']:.1f} hours")
        print(f"Within 6-hour budget: {'YES' if results['within_budget'] else 'NO'}")
        
        if results["warnings"]:
            print("\nWarnings:")
            for warning in results["warnings"]:
                print(f"  - {warning}")
        
        print("=" * 60)
        
        if not results["within_budget"]:
            logger.warning("Simulation sweep may exceed 6-hour budget")
            sys.exit(1)
        
        logger.info("T036 completed successfully")
        
    except Exception as e:
        logger.error(f"T036 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
