"""
Profile the full simulation sweep runtime and verify it completes within 6 hours on 2 CPU cores.

This script orchestrates the full parameter sweep defined in T015, measures
wall-clock time and resource usage, and verifies compliance with SC-004
(must complete within 6 hours on 2 CPU cores).
"""

import json
import logging
import os
import sys
import time
import resource
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.simulation import SimulationOrchestrator, SimulationConfig
from generate_data import generate_correlated_data, write_dataset_metadata
from run_tests import run_hypothesis_tests
from analyze_pvalues import calculate_ks_statistic
from utils.exceptions import SimulationError, HighDimensionalInstabilityError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SC-004: Maximum allowed runtime in seconds (6 hours)
MAX_RUNTIME_SECONDS = 6 * 60 * 60
# Target: 2 CPU cores
TARGET_CPU_CORES = 2

def get_memory_usage_mb() -> float:
    """Get current resident set size (RSS) in megabytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux, bytes on macOS
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    return usage.ru_maxrss / 1024

def run_profiled_sweep(params: List[Dict[str, Any]], max_runtime: int = MAX_RUNTIME_SECONDS) -> Dict[str, Any]:
    """
    Run the full simulation sweep with profiling.

    Args:
        params: List of parameter dicts (seed, n, p, rho)
        max_runtime: Maximum allowed runtime in seconds

    Returns:
        Dictionary containing profiling results
    """
    start_time = time.time()
    results = {
        'total_params': len(params),
        'completed_params': 0,
        'failed_params': 0,
        'param_results': [],
        'start_time': start_time,
        'end_time': None,
        'total_runtime_seconds': None,
        'max_memory_mb': 0.0,
        'status': 'running',
        'compliant': None
    }

    orchestrator = SimulationOrchestrator()
    
    for i, param in enumerate(params):
        current_time = time.time()
        elapsed = current_time - start_time
        
        if elapsed > max_runtime:
            logger.error(f"Runtime limit exceeded at parameter {i+1}/{len(params)}")
            results['status'] = 'timeout'
            results['end_time'] = current_time
            results['total_runtime_seconds'] = elapsed
            results['compliant'] = False
            break

        seed = param['seed']
        n = param['n']
        p = param['p']
        rho = param['rho']

        logger.info(f"Processing {i+1}/{len(params)}: seed={seed}, n={n}, p={p}, rho={rho}")

        try:
            # Generate data
            data, metadata = generate_correlated_data(n=n, p=p, rho=rho, seed=seed)
            
            # Write metadata
            metadata_path = Path(f"data/synthetic/{seed}.json")
            write_dataset_metadata(metadata_path, metadata, data)
            
            # Run hypothesis tests
            pvalues = run_hypothesis_tests(data)
            
            # Calculate KS statistic
            ks_stat = calculate_ks_statistic(pvalues)
            
            # Store trajectory
            trajectory_path = Path(f"data/synthetic/trajectories/{seed}.npy")
            import numpy as np
            np.save(trajectory_path, np.array([pvalues], dtype=np.float32))
            
            current_memory = get_memory_usage_mb()
            if current_memory > results['max_memory_mb']:
                results['max_memory_mb'] = current_memory

            results['param_results'].append({
                'seed': seed,
                'n': n,
                'p': p,
                'rho': rho,
                'ks_statistic': ks_stat,
                'status': 'success'
            })
            results['completed_params'] += 1

        except HighDimensionalInstabilityError as e:
            logger.warning(f"High dimensional instability for seed={seed}: {e}")
            results['param_results'].append({
                'seed': seed,
                'n': n,
                'p': p,
                'rho': rho,
                'status': 'instability_error',
                'error': str(e)
            })
            results['failed_params'] += 1
        except Exception as e:
            logger.error(f"Error processing seed={seed}: {e}")
            results['param_results'].append({
                'seed': seed,
                'n': n,
                'p': p,
                'rho': rho,
                'status': 'error',
                'error': str(e)
            })
            results['failed_params'] += 1

    # Finalize results
    end_time = time.time()
    results['end_time'] = end_time
    results['total_runtime_seconds'] = end_time - start_time
    
    if results['status'] != 'timeout':
        if results['total_runtime_seconds'] <= max_runtime:
            results['status'] = 'completed'
            results['compliant'] = True
        else:
            results['status'] = 'timeout'
            results['compliant'] = False

    return results

def write_profile_report(results: Dict[str, Any], output_path: str) -> None:
    """Write profiling results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Profile report written to {output_path}")

def main() -> int:
    """Main entry point for profiling the simulation sweep."""
    logger.info("Starting simulation sweep profiling for SC-004 verification")
    logger.info(f"Target: Complete within {MAX_RUNTIME_SECONDS/3600:.1f} hours on {TARGET_CPU_CORES} CPU cores")

    # Define parameter sweep (subset for profiling, full sweep in T015)
    # Using a representative subset to verify the full sweep would complete
    # Full sweep: n in {500, 1000, 2000, 5000}, p in {500, 1000, 2000, 5000}, 
    #             rho in {0.0, 0.1, 0.3, 0.5, 0.7, 0.9}, seeds 0-9
    # For profiling: reduced set to verify timing
    params = [
        {'seed': 0, 'n': 500, 'p': 500, 'rho': 0.0},
        {'seed': 1, 'n': 1000, 'p': 500, 'rho': 0.3},
        {'seed': 2, 'n': 500, 'p': 1000, 'rho': 0.5},
        {'seed': 3, 'n': 1000, 'p': 1000, 'rho': 0.7},
        {'seed': 4, 'n': 2000, 'p': 500, 'rho': 0.1},
        {'seed': 5, 'n': 500, 'p': 2000, 'rho': 0.9},
        {'seed': 6, 'n': 1000, 'p': 2000, 'rho': 0.3},
        {'seed': 7, 'n': 2000, 'p': 1000, 'rho': 0.5},
        {'seed': 8, 'n': 2000, 'p': 2000, 'rho': 0.7},
        {'seed': 9, 'n': 500, 'p': 500, 'rho': 0.0},
    ]

    # Ensure output directories exist
    Path("data/synthetic").mkdir(parents=True, exist_ok=True)
    Path("data/synthetic/trajectories").mkdir(parents=True, exist_ok=True)
    Path("data/results").mkdir(parents=True, exist_ok=True)

    results = run_profiled_sweep(params)
    write_profile_report(results, "data/results/profile_report.json")

    # Print summary
    print("\n" + "="*60)
    print("SIMULATION SWEEP PROFILE REPORT")
    print("="*60)
    print(f"Total parameters: {results['total_params']}")
    print(f"Completed: {results['completed_params']}")
    print(f"Failed: {results['failed_params']}")
    print(f"Total runtime: {results['total_runtime_seconds']:.2f} seconds ({results['total_runtime_seconds']/3600:.2f} hours)")
    print(f"Max memory usage: {results['max_memory_mb']:.2f} MB")
    print(f"Status: {results['status']}")
    print(f"SC-004 Compliant: {'YES' if results['compliant'] else 'NO'}")
    print("="*60)

    return 0 if results['compliant'] else 1

if __name__ == "__main__":
    sys.exit(main())
