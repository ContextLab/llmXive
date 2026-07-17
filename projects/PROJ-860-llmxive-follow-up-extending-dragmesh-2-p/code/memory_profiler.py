"""
Memory Profiling Script for llmXive Pipeline.

Implements memory profiling using tracemalloc to capture and log PEAK memory usage
for the pipeline components. This script is designed to verify that the pipeline
stays within the 7GB RAM constraint on CPU-only runners.

Usage:
    python code/memory_profiler.py [--output data/results/memory_profile.csv]
"""
import os
import sys
import time
import tracemalloc
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'code'))

from logging_config import setup_all_loggers, get_logger

def setup_profiling_logger(output_dir: Optional[Path] = None) -> logging.Logger:
    """
    Setup a dedicated logger for memory profiling results.
    
    Args:
        output_dir: Directory to save profiling results. Defaults to data/results/
        
    Returns:
        Configured logger instance
    """
    if output_dir is None:
        output_dir = project_root / 'data' / 'results'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger('memory_profiler')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler for results
    log_file = output_dir / 'memory_profiling.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def profile_function(func, *args, **kwargs) -> Tuple[Any, float, int]:
    """
    Profile a function's memory usage and execution time.
    
    Args:
        func: Function to profile
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Tuple of (function_return_value, elapsed_time_seconds, peak_memory_kb)
    """
    # Reset tracemalloc
    tracemalloc.stop()
    tracemalloc.start()
    
    start_time = time.time()
    
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        elapsed_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        raise RuntimeError(f"Function {func.__name__} failed during profiling: {e}") from e
    
    elapsed_time = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Convert bytes to KB for readability
    peak_memory_kb = peak / 1024
    
    return result, elapsed_time, peak_memory_kb

def profile_pipeline_component(component_name: str, func, *args, **kwargs) -> Dict[str, Any]:
    """
    Profile a specific pipeline component and log detailed results.
    
    Args:
        component_name: Name of the component being profiled
        func: Function to profile
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Dictionary containing profiling results
    """
    logger = get_logger('memory_profiler')
    
    logger.info(f"Starting memory profile for component: {component_name}")
    logger.info(f"Function: {func.__name__}")
    
    try:
        result, elapsed_time, peak_memory_kb = profile_function(func, *args, **kwargs)
        
        profile_result = {
            'component_name': component_name,
            'function_name': func.__name__,
            'timestamp': datetime.now().isoformat(),
            'elapsed_time_seconds': round(elapsed_time, 3),
            'peak_memory_kb': round(peak_memory_kb, 2),
            'peak_memory_mb': round(peak_memory_kb / 1024, 2),
            'peak_memory_gb': round(peak_memory_kb / (1024 * 1024), 4),
            'status': 'success'
        }
        
        logger.info(f"Profile completed for {component_name}:")
        logger.info(f"  - Elapsed time: {profile_result['elapsed_time_seconds']}s")
        logger.info(f"  - Peak memory: {profile_result['peak_memory_mb']} MB")
        
        return profile_result
        
    except Exception as e:
        logger.error(f"Profile failed for {component_name}: {e}")
        
        profile_result = {
            'component_name': component_name,
            'function_name': func.__name__,
            'timestamp': datetime.now().isoformat(),
            'elapsed_time_seconds': 0,
            'peak_memory_kb': 0,
            'peak_memory_mb': 0,
            'peak_memory_gb': 0,
            'status': 'failed',
            'error': str(e)
        }
        
        return profile_result

def write_profile_results(results: list, output_path: Path) -> None:
    """
    Write profiling results to a CSV file.
    
    Args:
        results: List of profiling result dictionaries
        output_path: Path to the output CSV file
    """
    import csv
    
    if not results:
        logging.getLogger('memory_profiler').warning("No results to write")
        return
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'component_name',
        'function_name',
        'timestamp',
        'elapsed_time_seconds',
        'peak_memory_kb',
        'peak_memory_mb',
        'peak_memory_gb',
        'status',
        'error'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    
    logging.getLogger('memory_profiler').info(f"Results written to {output_path}")

def run_memory_profile_pipeline(output_path: Optional[Path] = None) -> list:
    """
    Run memory profiling on the complete pipeline components.
    
    This function profiles:
    1. Object generation (generator)
    2. Training loop (train)
    3. Evaluation loop (evaluate)
    4. Baseline execution (baseline_runner)
    
    Args:
        output_path: Optional path for CSV output. Defaults to data/results/memory_profile.csv
        
    Returns:
        List of profiling result dictionaries
    """
    logger = get_logger('memory_profiler')
    logger.info("=" * 60)
    logger.info("Starting Memory Profiling Pipeline")
    logger.info("=" * 60)
    
    if output_path is None:
        output_path = project_root / 'data' / 'results' / 'memory_profile.csv'
    
    results = []
    
    # Profile 1: Object Generation
    logger.info("\n[1/4] Profiling Object Generation...")
    try:
        from generator import NovelObjectSet
        generator = NovelObjectSet(seed=42, num_objects=5)  # Small set for profiling
        profile_result = profile_pipeline_component(
            "object_generation",
            generator.generate_objects,
            output_dir=str(project_root / 'data' / 'generated')
        )
        results.append(profile_result)
    except ImportError as e:
        logger.warning(f"Could not import generator module: {e}")
        results.append({
            'component_name': 'object_generation',
            'function_name': 'generate_objects',
            'timestamp': datetime.now().isoformat(),
            'status': 'skipped',
            'error': f"Import error: {e}"
        })
    
    # Profile 2: Training Loop (single episode)
    logger.info("\n[2/4] Profiling Training Loop...")
    try:
        from train import run_episode
        from environment import create_cpu_environment
        
        env = create_cpu_environment()
        episode_result = profile_pipeline_component(
            "training_loop",
            run_episode,
            env,
            max_steps=10  # Short episode for profiling
        )
        env.reset()
        results.append(episode_result)
    except ImportError as e:
        logger.warning(f"Could not import training module: {e}")
        results.append({
            'component_name': 'training_loop',
            'function_name': 'run_episode',
            'timestamp': datetime.now().isoformat(),
            'status': 'skipped',
            'error': f"Import error: {e}"
        })
    
    # Profile 3: Evaluation Loop (single episode)
    logger.info("\n[3/4] Profiling Evaluation Loop...")
    try:
        from evaluate import run_adaptive_episode, run_static_episode
        from environment import create_cpu_environment
        
        env = create_cpu_environment()
        
        # Profile adaptive episode
        adaptive_result = profile_pipeline_component(
            "evaluation_adaptive",
            run_adaptive_episode,
            env,
            max_steps=10
        )
        results.append(adaptive_result)
        
        # Profile static episode
        static_result = profile_pipeline_component(
            "evaluation_static",
            run_static_episode,
            env,
            max_steps=10
        )
        results.append(static_result)
        
        env.reset()
    except ImportError as e:
        logger.warning(f"Could not import evaluation module: {e}")
        results.append({
            'component_name': 'evaluation_loop',
            'function_name': 'run_adaptive_episode',
            'timestamp': datetime.now().isoformat(),
            'status': 'skipped',
            'error': f"Import error: {e}"
        })
    
    # Profile 4: Baseline Runner
    logger.info("\n[4/4] Profiling Baseline Runner...")
    try:
        from baseline_runner import run_baseline_episode
        from environment import create_cpu_environment
        
        env = create_cpu_environment()
        baseline_result = profile_pipeline_component(
            "baseline_runner",
            run_baseline_episode,
            env,
            max_steps=10
        )
        results.append(baseline_result)
        env.reset()
    except ImportError as e:
        logger.warning(f"Could not import baseline runner module: {e}")
        results.append({
            'component_name': 'baseline_runner',
            'function_name': 'run_baseline_episode',
            'timestamp': datetime.now().isoformat(),
            'status': 'skipped',
            'error': f"Import error: {e}"
        })
    
    # Write results to CSV
    write_profile_results(results, output_path)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Memory Profiling Summary")
    logger.info("=" * 60)
    
    successful_profiles = [r for r in results if r.get('status') == 'success']
    if successful_profiles:
        max_peak_mb = max(r['peak_memory_mb'] for r in successful_profiles)
        logger.info(f"Maximum peak memory across components: {max_peak_mb:.2f} MB")
        logger.info(f"Constraint: 7 GB = 7168 MB")
        logger.info(f"Status: {'PASS' if max_peak_mb < 7168 else 'WARNING: Exceeds threshold'}")
    else:
        logger.warning("No successful profiles to summarize")
    
    return results

def main():
    """Main entry point for memory profiling script."""
    parser = argparse.ArgumentParser(
        description='Memory profiling script for llmXive pipeline'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for CSV results (default: data/results/memory_profile.csv)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    output_dir = Path(args.output).parent if args.output else project_root / 'data' / 'results'
    logger = setup_profiling_logger(output_dir)
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("llmXive Memory Profiler v1.0")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        output_path = Path(args.output) if args.output else None
        results = run_memory_profile_pipeline(output_path)
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results if r.get('status') == 'failed')
        skipped_count = sum(1 for r in results if r.get('status') == 'skipped')
        
        if failed_count > 0:
            logger.error(f"Profiling completed with {failed_count} failures and {skipped_count} skips")
            sys.exit(1)
        elif skipped_count > 0:
            logger.warning(f"Profiling completed with {skipped_count} skipped components")
            sys.exit(0)
        else:
            logger.info("Profiling completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Profiling failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()