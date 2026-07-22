import os
import sys
import time
import json
import logging
import tracemalloc
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('llmXive.benchmark')

PROCESSED_DIR = Path('data/processed')
OUTPUT_FILE = PROCESSED_DIR / 'benchmark_log.json'

# Ensure output directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def get_memory_usage_mb():
    """Get current memory usage in MB."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)
    return 0.0

def get_peak_memory_mb():
    """Get peak memory usage in MB since tracing started."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    return 0.0

def run_phase_benchmark(phase_name: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Run a specific phase function and benchmark its execution time and memory."""
    logger.info(f"Starting benchmark phase: {phase_name}")
    
    tracemalloc.start()
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
        success = True
        error_msg = None
    except Exception as e:
        success = False
        error_msg = str(e)
        result = None
        logger.error(f"Phase {phase_name} failed: {e}")
    finally:
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    duration = end_time - start_time
    memory_mb = peak / (1024 * 1024)

    benchmark_record = {
        'phase': phase_name,
        'start_time': datetime.fromtimestamp(start_time).isoformat(),
        'end_time': datetime.fromtimestamp(end_time).isoformat(),
        'duration_seconds': round(duration, 4),
        'peak_memory_mb': round(memory_mb, 2),
        'success': success,
        'error': error_msg
    }

    if result is not None:
        benchmark_record['result_summary'] = str(result)[:200] if not isinstance(result, (dict, list)) else "data_generated"

    logger.info(f"Phase {phase_name} completed in {duration:.2f}s (Peak Memory: {memory_mb:.2f}MB)")
    return benchmark_record

def benchmark_parser_phase():
    """Benchmark the parser phase by running the main function."""
    from parser import main as parser_main
    return run_phase_benchmark('parser', parser_main)

def benchmark_splitter_phase():
    """Benchmark the splitter phase by running the main function."""
    from splitter import main as splitter_main
    return run_phase_benchmark('splitter', splitter_main)

def benchmark_ablation_phase():
    """Benchmark the ablation phase by running the main function."""
    from ablation import main as ablation_main
    return run_phase_benchmark('ablation', ablation_main)

def benchmark_classifier_phase():
    """Benchmark the classifier phase by running the main function."""
    from classifier import main as classifier_main
    return run_phase_benchmark('classifier', classifier_main)

def benchmark_simulation_phase():
    """Benchmark the simulation phase by running the main function."""
    from simulator import main as simulator_main
    return run_phase_benchmark('simulation', simulator_main)

def benchmark_stats_phase():
    """Benchmark the stats phase by running the main function."""
    from stats import main as stats_main
    return run_phase_benchmark('stats', stats_main)

def run_full_benchmark() -> List[Dict[str, Any]]:
    """Run all benchmark phases sequentially and return results."""
    results = []
    
    phases = [
        ('parser', benchmark_parser_phase),
        ('splitter', benchmark_splitter_phase),
        ('ablation', benchmark_ablation_phase),
        ('classifier', benchmark_classifier_phase),
        ('simulation', benchmark_simulation_phase),
        ('stats', benchmark_stats_phase)
    ]

    for phase_name, phase_func in phases:
        try:
            result = phase_func()
            results.append(result)
        except Exception as e:
            logger.error(f"Critical error in phase {phase_name}: {e}")
            results.append({
                'phase': phase_name,
                'success': False,
                'error': str(e),
                'duration_seconds': 0,
                'peak_memory_mb': 0
            })
            # Continue to next phase even if one fails, to get full picture
    
    return results

def save_benchmark_report(results: List[Dict[str, Any]]):
    """Save the benchmark results to the JSON file."""
    total_duration = sum(r.get('duration_seconds', 0) for r in results)
    total_memory = max(r.get('peak_memory_mb', 0) for r in results)
    success_count = sum(1 for r in results if r.get('success', False))
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_runtime_seconds': round(total_duration, 4),
        'peak_memory_mb': round(total_memory, 2),
        'phases_completed': success_count,
        'phases_total': len(results),
        'overall_success': success_count == len(results),
        'phase_results': results
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved benchmark report to {OUTPUT_FILE}")
    logger.info(f"Total Runtime: {total_duration:.2f}s, Peak Memory: {total_memory:.2f}MB")
    return report

def main():
    """Entry point for the benchmark script."""
    logger.info("Starting FULL benchmark execution.")
    start_total = time.time()
    
    results = run_full_benchmark()
    
    report = save_benchmark_report(results)
    
    end_total = time.time()
    total_real_time = end_total - start_total
    
    # Update report with total real wall-clock time
    report['total_wall_clock_seconds'] = round(total_real_time, 4)
    
    # Rewrite file with updated total
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Benchmark complete. Total wall-clock time: {total_real_time:.2f}s")
    
    if not report['overall_success']:
        logger.warning("One or more benchmark phases failed. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All benchmark phases completed successfully.")
        sys.exit(0)

if __name__ == '__main__':
    main()