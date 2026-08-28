"""
Memory profiling module for the mitochondrial aging correlation analysis.

This module provides utilities to monitor and log memory usage during
the analysis pipeline execution, ensuring adherence to the 7GB RAM constraint.
"""
import os
import sys
import logging
import time
import gc
from pathlib import Path
from typing import List, Dict, Any

# Try to import memory_profiler, but handle gracefully if not installed
# The task requires using memory_profiler, so we assume it's in requirements.txt
try:
    from memory_profiler import memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    logging.warning("memory_profiler not installed. Memory profiling will be skipped.")

from config.environment import get_local_paths

logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the Python process in megabytes.
    
    Returns:
        float: Current memory usage in MB
    """
    try:
        # Method 1: Use /proc/self/status on Linux
        if sys.platform.startswith('linux'):
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        return float(line.split()[1]) / 1024.0
        
        # Method 2: Use resource module (Unix)
        if sys.platform != 'win32':
            import resource
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            return rusage.ru_maxrss / 1024.0  # Convert kB to MB
        
        # Fallback: Use tracemalloc
        import tracemalloc
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        
        # Last resort: return 0 with warning
        logger.warning("Could not determine memory usage accurately")
        return 0.0
        
    except Exception as e:
        logger.warning(f"Error getting memory usage: {e}")
        return 0.0

def profile_memory_usage(func, *args, **kwargs) -> Dict[str, Any]:
    """
    Profile memory usage of a function execution.
    
    Args:
        func: Function to profile
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Dict containing:
            - 'peak_memory_mb': Peak memory usage during execution
            - 'start_memory_mb': Memory at start
            - 'end_memory_mb': Memory at end
            - 'duration_seconds': Execution duration
            - 'memory_samples': List of (time, memory) tuples
    """
    if not MEMORY_PROFILER_AVAILABLE:
        logger.warning("memory_profiler not available. Running function without profiling.")
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return {
            'peak_memory_mb': get_memory_usage_mb(),
            'start_memory_mb': get_memory_usage_mb(),
            'end_memory_mb': get_memory_usage_mb(),
            'duration_seconds': duration,
            'memory_samples': [],
            'warning': 'memory_profiler not installed'
        }
    
    # Force garbage collection before profiling
    gc.collect()
    
    start_memory = get_memory_usage_mb()
    start_time = time.time()
    
    # Use memory_profiler to track memory over time
    def wrapped_func():
        return func(*args, **kwargs)
    
    try:
        # memory_usage returns a tuple of (memory_usage, time_stamps)
        mem_usage, time_stamps = memory_usage(
            wrapped_func,
            interval=0.5,
            timeout=3600,  # 1 hour max
            max_iterations=1,
            include_children=True,
            multiprocess=False
        )
    except Exception as e:
        logger.error(f"memory_profiler failed: {e}")
        # Fallback to simple measurement
        result = func(*args, **kwargs)
        end_memory = get_memory_usage_mb()
        duration = time.time() - start_time
        return {
            'peak_memory_mb': end_memory,
            'start_memory_mb': start_memory,
            'end_memory_mb': end_memory,
            'duration_seconds': duration,
            'memory_samples': [],
            'error': str(e)
        }
    
    end_time = time.time()
    end_memory = get_memory_usage_mb()
    peak_memory = max(mem_usage) if mem_usage else end_memory
    
    # Create memory samples
    memory_samples = []
    if mem_usage and time_stamps:
        for t, m in zip(time_stamps, mem_usage):
            memory_samples.append({'time_seconds': t, 'memory_mb': m})
    elif mem_usage:
        # Fallback if time_stamps not available
        for i, m in enumerate(mem_usage):
            memory_samples.append({'time_seconds': i * 0.5, 'memory_mb': m})
    
    return {
        'peak_memory_mb': peak_memory,
        'start_memory_mb': start_memory,
        'end_memory_mb': end_memory,
        'duration_seconds': end_time - start_time,
        'memory_samples': memory_samples,
        'function_name': func.__name__
    }

def write_memory_profile_log(profile_results: List[Dict[str, Any]], output_path: str = None):
    """
    Write memory profiling results to a log file.
    
    Args:
        profile_results: List of profiling result dictionaries
        output_path: Path to output log file (defaults to code/logs/memory_profile.log)
    """
    if output_path is None:
        paths = get_local_paths()
        log_dir = paths.get('log_dir', Path('code/logs'))
        output_path = str(Path(log_dir) / 'memory_profile.log')
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("MEMORY PROFILE LOG\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        if not MEMORY_PROFILER_AVAILABLE:
            f.write("WARNING: memory_profiler package not installed.\n")
            f.write("Memory profiling was not performed with detailed tracking.\n")
            f.write("Only snapshot measurements were taken.\n\n")
        
        f.write(f"Number of functions profiled: {len(profile_results)}\n")
        f.write("-" * 80 + "\n\n")
        
        for i, result in enumerate(profile_results, 1):
            f.write(f"Profile #{i}: {result.get('function_name', 'Unknown')}\n")
            f.write(f"  Start Memory: {result['start_memory_mb']:.2f} MB\n")
            f.write(f"  Peak Memory:  {result['peak_memory_mb']:.2f} MB\n")
            f.write(f"  End Memory:   {result['end_memory_mb']:.2f} MB\n")
            f.write(f"  Duration:     {result['duration_seconds']:.2f} seconds\n")
            
            if 'warning' in result:
                f.write(f"  WARNING: {result['warning']}\n")
            if 'error' in result:
                f.write(f"  ERROR: {result['error']}\n")
            
            # Show memory trend if samples available
            samples = result.get('memory_samples', [])
            if samples:
                f.write(f"  Memory Samples ({len(samples)} points):\n")
                # Show first 10 and last 5 samples to avoid huge logs
                display_samples = samples[:10] + (samples[-5:] if len(samples) > 15 else [])
                for j, sample in enumerate(display_samples):
                    if j == 10:
                        f.write(f"    ... ({len(samples) - 15} more samples) ...\n")
                    else:
                        f.write(f"    t={sample['time_seconds']:.1f}s: {sample['memory_mb']:.2f} MB\n")
            
            f.write("\n" + "-" * 80 + "\n\n")
        
        # Summary statistics
        f.write("\nSUMMARY STATISTICS\n")
        f.write("=" * 80 + "\n")
        if profile_results:
            peak_memories = [r['peak_memory_mb'] for r in profile_results]
            durations = [r['duration_seconds'] for r in profile_results]
            
            f.write(f"Total functions profiled: {len(profile_results)}\n")
            f.write(f"Peak memory (max across all): {max(peak_memories):.2f} MB\n")
            f.write(f"Peak memory (avg across all): {sum(peak_memories)/len(peak_memories):.2f} MB\n")
            f.write(f"Total execution time: {sum(durations):.2f} seconds\n")
            
            # Check against 7GB constraint
            max_peak_mb = max(peak_memories)
            constraint_mb = 7 * 1024  # 7GB in MB
            f.write(f"\nMemory Constraint Check (7GB = {constraint_mb} MB):\n")
            if max_peak_mb < constraint_mb:
                f.write(f"  ✓ PASS: Peak memory ({max_peak_mb:.2f} MB) is within 7GB limit\n")
            else:
                f.write(f"  ✗ FAIL: Peak memory ({max_peak_mb:.2f} MB) EXCEEDS 7GB limit\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF MEMORY PROFILE LOG\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"Memory profile log written to: {output_path}")

def main():
    """
    Main function to profile memory usage of the analysis pipeline.
    
    This function runs the key analysis functions and profiles their memory usage,
    then writes the results to code/logs/memory_profile.log.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting memory profiling for analysis pipeline")
    
    # Import analysis functions
    from analysis.load_data import main as load_data_main
    from analysis.preprocess import main as preprocess_main
    from analysis.model import main as model_main
    from analysis.sensitivity import main as sensitivity_main
    
    profile_results = []
    
    # Profile each major component
    components = [
        ('load_data', load_data_main),
        ('preprocess', preprocess_main),
        ('model', model_main),
        ('sensitivity', sensitivity_main)
    ]
    
    for name, func in components:
        logger.info(f"Profiling {name}...")
        try:
            result = profile_memory_usage(func)
            result['function_name'] = name
            profile_results.append(result)
            logger.info(f"  Peak memory: {result['peak_memory_mb']:.2f} MB")
        except Exception as e:
            logger.error(f"Error profiling {name}: {e}")
            profile_results.append({
                'function_name': name,
                'peak_memory_mb': 0,
                'start_memory_mb': 0,
                'end_memory_mb': 0,
                'duration_seconds': 0,
                'memory_samples': [],
                'error': str(e)
            })
    
    # Write results to log
    write_memory_profile_log(profile_results)
    
    logger.info("Memory profiling complete")
    return profile_results

if __name__ == '__main__':
    main()
