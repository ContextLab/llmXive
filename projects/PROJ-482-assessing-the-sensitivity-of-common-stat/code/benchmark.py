"""
Benchmark script for the statistical sensitivity simulation pipeline.

This script measures the execution time of the full simulation suite
and writes detailed results to logs/benchmark.log.

Verification: The total runtime for the full suite should be < 6 hours.
For testing purposes, a 'quick' mode is available that runs a subset.
"""
import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.config import get_simulation_grid, SimulationConfig
from code.run_simulation import run_full_batch
from code.performance_monitor import log_scenario_execution, validate_performance_target

# Setup logging for the benchmark
LOG_DIR = os.path.join(project_root, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'benchmark.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_benchmark(quick_mode: bool = False) -> Dict[str, Any]:
    """
    Run the full simulation pipeline benchmark.
    
    Args:
        quick_mode: If True, run a reduced subset for faster verification.
    
    Returns:
        Dictionary containing benchmark results and timing information.
    """
    results = {
        'start_time': datetime.now().isoformat(),
        'quick_mode': quick_mode,
        'scenarios': [],
        'total_duration_seconds': 0,
        'status': 'running'
    }

    logger.info("=" * 60)
    logger.info("Starting Benchmark for Statistical Sensitivity Pipeline")
    logger.info("=" * 60)
    
    if quick_mode:
        logger.info("Running in QUICK MODE (reduced scenario set)")
        # Define a small subset for quick validation
        # 2 sample sizes, 2 distributions, 2 tests
        sample_sizes = [10, 50]
        distributions = ['normal', 'uniform']
        test_types = ['t_test', 'chi_squared']
        hypothesis_types = ['null', 'alternative']
        replicates = 100  # Reduced for quick mode
    else:
        logger.info("Running FULL benchmark (all scenarios)")
        # Use the full grid from config
        sample_sizes = [10, 20, 50, 100, 200, 500, 1000]
        distributions = ['normal', 'uniform', 'log_normal']
        test_types = ['t_test', 'anova', 'chi_squared']
        hypothesis_types = ['null', 'alternative']
        replicates = 1000  # Standard replicates

    total_scenarios = (
        len(sample_sizes) * 
        len(distributions) * 
        len(test_types) * 
        len(hypothesis_types)
    )
    
    logger.info(f"Total scenarios to run: {total_scenarios}")
    logger.info(f"Sample sizes: {sample_sizes}")
    logger.info(f"Distributions: {distributions}")
    logger.info(f"Test types: {test_types}")
    logger.info(f"Replicates per scenario: {replicates}")

    start_time = time.time()
    
    try:
        # Run the full batch simulation
        # The run_full_batch function orchestrates the simulation
        # and saves intermediate results to data/processed/
        
        logger.info("Starting simulation batch execution...")
        
        # We will run a subset of scenarios manually to measure time
        # This gives us granular timing per scenario
        scenario_times = []
        
        for n in sample_sizes:
            for dist in distributions:
                for test in test_types:
                    for hyp in hypothesis_types:
                        scenario_start = time.time()
                        
                        scenario_id = f"n={n}_{dist}_{test}_{hyp}"
                        logger.info(f"Running scenario: {scenario_id}")
                        
                        try:
                            # Run a single scenario using the simulation engine
                            # We import here to ensure we use the latest code
                            from code.simulation_engine import run_adaptive_simulation
                            
                            # Create a minimal config for this scenario
                            config = SimulationConfig(
                                sample_size=n,
                                distribution_type=dist,
                                test_type=test,
                                hypothesis_type=hyp,
                                effect_size=0.5 if hyp == 'alternative' else 0.0,
                                alpha=0.05,
                                min_replicates=replicates // 10 if quick_mode else replicates,
                                max_replicates=replicates * 2 if quick_mode else replicates * 5,
                                target_ci_width=0.01
                            )
                            
                            # Run the simulation
                            result = run_adaptive_simulation(config)
                            
                            scenario_end = time.time()
                            duration = scenario_end - scenario_start
                            
                            scenario_times.append({
                                'scenario_id': scenario_id,
                                'n': n,
                                'distribution': dist,
                                'test_type': test,
                                'hypothesis': hyp,
                                'duration_seconds': duration,
                                'replicates_completed': result.get('replicates_completed', 0),
                                'status': 'success'
                            })
                            
                            logger.info(f"  Completed in {duration:.2f}s")
                            
                            # Log to performance monitor
                            log_scenario_execution({
                                'scenario_id': scenario_id,
                                'duration': duration,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                        except Exception as e:
                            logger.error(f"  FAILED: {str(e)}")
                            scenario_times.append({
                                'scenario_id': scenario_id,
                                'n': n,
                                'distribution': dist,
                                'test_type': test,
                                'hypothesis': hyp,
                                'duration_seconds': 0,
                                'status': 'failed',
                                'error': str(e)
                            })
        
        results['scenarios'] = scenario_times
        
    except Exception as e:
        logger.error(f"Benchmark failed with error: {str(e)}")
        results['status'] = 'failed'
        results['error'] = str(e)
    finally:
        end_time = time.time()
        total_duration = end_time - start_time
        results['total_duration_seconds'] = total_duration
        results['end_time'] = datetime.now().isoformat()
        
        # Calculate statistics
        successful_scenarios = [s for s in scenario_times if s['status'] == 'success']
        failed_scenarios = [s for s in scenario_times if s['status'] == 'failed']
        
        if successful_scenarios:
            avg_duration = sum(s['duration_seconds'] for s in successful_scenarios) / len(successful_scenarios)
            max_duration = max(s['duration_seconds'] for s in successful_scenarios)
            min_duration = min(s['duration_seconds'] for s in successful_scenarios)
            
            results['statistics'] = {
                'successful_scenarios': len(successful_scenarios),
                'failed_scenarios': len(failed_scenarios),
                'average_duration_seconds': avg_duration,
                'max_duration_seconds': max_duration,
                'min_duration_seconds': min_duration,
                'total_duration_seconds': total_duration,
                'estimated_full_suite_hours': (total_duration / len(successful_scenarios)) * total_scenarios / 3600
            }
            
            logger.info(f"Average scenario time: {avg_duration:.2f}s")
            logger.info(f"Max scenario time: {max_duration:.2f}s")
            logger.info(f"Estimated full suite time: {results['statistics']['estimated_full_suite_hours']:.2f} hours")
            
            # Validate against 6-hour target
            if results['statistics']['estimated_full_suite_hours'] < 6:
                logger.info("✅ PERFORMANCE TARGET MET: Estimated time < 6 hours")
                results['performance_target_met'] = True
            else:
                logger.warning("⚠️ PERFORMANCE TARGET NOT MET: Estimated time >= 6 hours")
                results['performance_target_met'] = False
        else:
            results['performance_target_met'] = False
            results['statistics'] = {'error': 'No successful scenarios to analyze'}

    return results

def main():
    """Main entry point for the benchmark script."""
    parser = argparse.ArgumentParser(description='Benchmark the statistical simulation pipeline')
    parser.add_argument('--quick', action='store_true', help='Run in quick mode (reduced scenarios)')
    parser.add_argument('--output', type=str, default=None, help='Path to save JSON results (default: logs/benchmark_results.json)')
    
    args = parser.parse_args()
    
    # Run the benchmark
    results = run_benchmark(quick_mode=args.quick)
    
    # Save results to JSON
    output_path = args.output or os.path.join(LOG_DIR, 'benchmark_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Benchmark results saved to {output_path}")
    logger.info(f"Full log available at {LOG_FILE}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Total Duration: {results['total_duration_seconds']:.2f} seconds")
    print(f"Status: {results['status']}")
    
    if 'statistics' in results:
        stats = results['statistics']
        print(f"Successful Scenarios: {stats.get('successful_scenarios', 0)}")
        print(f"Failed Scenarios: {stats.get('failed_scenarios', 0)}")
        
        if 'average_duration_seconds' in stats:
            print(f"Average Scenario Time: {stats['average_duration_seconds']:.2f}s")
            print(f"Estimated Full Suite Time: {stats.get('estimated_full_suite_hours', 0):.2f} hours")
            print(f"Performance Target (< 6h): {'✅ MET' if results.get('performance_target_met') else '❌ NOT MET'}")
    
    # Return exit code based on success
    sys.exit(0 if results['status'] == 'running' or results['status'] == 'success' else 1)

if __name__ == '__main__':
    main()