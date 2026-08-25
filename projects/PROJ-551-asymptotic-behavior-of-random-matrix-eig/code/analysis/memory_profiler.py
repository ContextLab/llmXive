"""
Memory Profiling for Random Matrix Simulations.

This module provides tools to profile memory usage of matrix generation and
eigenvalue computation to ensure compliance with the 7 GB RAM constraint
for N=2000 matrices.
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh

# Import project modules using the provided API surface
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues
from utils.config import get_project_paths, ensure_directories

# Optional: memory_profiler import with fallback for environments without it
try:
    from memory_profiler import memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    logging.warning("memory_profiler not installed. Using manual sampling fallback.")


def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.
    Uses /proc/self/status on Linux or psutil if available, otherwise estimates.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback for Linux
        if sys.platform.startswith('linux'):
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            return float(line.split()[1]) / 1024.0
            except FileNotFoundError:
                pass
        # Ultimate fallback: estimate based on known allocations (very rough)
        logging.warning("Could not determine memory usage. Returning 0.0.")
        return 0.0


def profile_function_memory(
    func,
    *args,
    interval: float = 0.1,
    max_iterations: int = 1000,
    **kwargs
) -> Dict[str, Any]:
    """
    Profile the memory usage of a function call.

    If memory_profiler is available, use its high-resolution sampling.
    Otherwise, use manual sampling with get_memory_usage_mb.

    Returns a dict with:
      - peak_memory_mb: Maximum memory observed (MB)
      - start_memory_mb: Memory before function call (MB)
      - end_memory_mb: Memory after function call (MB)
      - memory_trace: List of (time_elapsed, memory_mb) tuples
    """
    start_mem = get_memory_usage_mb()
    memory_trace = [(0.0, start_mem)]

    if MEMORY_PROFILER_AVAILABLE:
        # Use memory_profiler for high-resolution tracking
        def run_func():
            func(*args, **kwargs)

        try:
            mem_usage, _ = memory_usage(
                run_func,
                interval=interval,
                timeout=max_iterations * interval,
                multiprocess=False
            )
            # memory_profiler returns a list of memory values
            if mem_usage:
                peak_mem = max(mem_usage)
                # Reconstruct trace with timestamps
                current_time = 0.0
                for i, mem_val in enumerate(mem_usage):
                    current_time += interval
                    memory_trace.append((current_time, mem_val))
            else:
                peak_mem = start_mem
        except Exception as e:
            logging.error(f"memory_profiler failed: {e}. Falling back to manual sampling.")
            peak_mem = start_mem
            # Fallback to manual sampling
            t0 = time.time()
            func(*args, **kwargs)
            t1 = time.time()
            end_mem = get_memory_usage_mb()
            memory_trace.append((t1 - t0, end_mem))
            peak_mem = max(start_mem, end_mem)
    else:
        # Manual sampling fallback
        t0 = time.time()
        func(*args, **kwargs)
        t1 = time.time()
        end_mem = get_memory_usage_mb()
        memory_trace.append((t1 - t0, end_mem))
        peak_mem = max(start_mem, end_mem)

    return {
        'peak_memory_mb': peak_mem,
        'start_memory_mb': start_mem,
        'end_memory_mb': end_mem,
        'memory_trace': memory_trace,
        'duration_seconds': memory_trace[-1][0] if memory_trace else 0.0
    }


def run_memory_profile_experiment(
    N: int = 2000,
    seed: int = 42,
    theta: float = 2.5,
    rank: int = 1,
    sparsity_density: float = 0.1,
    num_eigenvalues: int = 10,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a memory profiling experiment for generating a Wigner matrix,
    applying a perturbation, and computing eigenvalues.

    This simulates the core workload of the project to verify memory
    usage stays within the 7 GB limit.

    Args:
        N: Matrix dimension
        seed: Random seed for reproducibility
        theta: Perturbation strength
        rank: Rank of the perturbation
        sparsity_density: Density of the sparse perturbation
        num_eigenvalues: Number of top eigenvalues to compute
        output_path: Path to write the memory profile log

    Returns:
        Dict with profiling results
    """
    logging.info(f"Starting memory profile experiment: N={N}, seed={seed}")

    # Ensure output directory exists
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

    # Define the function to profile
    def experiment():
        # Generate Wigner matrix
        W = generate_wigner_matrix(N, seed=seed)
        
        # Create perturbation
        P = create_perturbation(N, rank=rank, theta=theta, 
                              sparsity_density=sparsity_density, 
                              seed=seed+1)
        
        # Compute eigenvalues
        eigenvalues = compute_top_eigenvalues(W + P, k=num_eigenvalues)
        
        return eigenvalues

    # Run profiling
    results = profile_function_memory(experiment)
    
    # Add experiment parameters
    results['experiment_params'] = {
        'N': N,
        'seed': seed,
        'theta': theta,
        'rank': rank,
        'sparsity_density': sparsity_density,
        'num_eigenvalues': num_eigenvalues
    }

    # Log results
    logging.info(f"Peak memory usage: {results['peak_memory_mb']:.2f} MB")
    logging.info(f"Duration: {results['duration_seconds']:.2f} seconds")

    # Write log file
    if output_path:
        with open(output_path, 'w') as f:
            f.write(f"Memory Profile Report for N={N}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Experiment Parameters:\n")
            for key, value in results['experiment_params'].items():
                f.write(f"  {key}: {value}\n")
            f.write(f"\nMemory Usage:\n")
            f.write(f"  Start: {results['start_memory_mb']:.2f} MB\n")
            f.write(f"  Peak:  {results['peak_memory_mb']:.2f} MB\n")
            f.write(f"  End:   {results['end_memory_mb']:.2f} MB\n")
            f.write(f"\nDuration: {results['duration_seconds']:.2f} seconds\n")
            f.write(f"\nMemory Trace (time, memory_mb):\n")
            for t, m in results['memory_trace']:
                f.write(f"  {t:.3f}s: {m:.2f} MB\n")
            f.write(f"\nCompliance Check:\n")
            if results['peak_memory_mb'] < 7000:
                f.write(f"  PASS: Peak memory ({results['peak_memory_mb']:.2f} MB) is within 7 GB limit.\n")
            else:
                f.write(f"  FAIL: Peak memory ({results['peak_memory_mb']:.2f} MB) exceeds 7 GB limit.\n")

    return results


def main():
    """Main entry point for memory profiling."""
    parser = argparse.ArgumentParser(description="Profile memory usage for random matrix simulations")
    parser.add_argument('--N', type=int, default=2000, help='Matrix dimension (default: 2000)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed (default: 42)')
    parser.add_argument('--theta', type=float, default=2.5, help='Perturbation strength (default: 2.5)')
    parser.add_argument('--rank', type=int, default=1, help='Perturbation rank (default: 1)')
    parser.add_argument('--sparsity', type=float, default=0.1, help='Sparsity density (default: 0.1)')
    parser.add_argument('--eigenvalues', type=int, default=10, help='Number of eigenvalues (default: 10)')
    parser.add_argument('--output', type=str, default=None, help='Output log file path')
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # If no output path specified, use default
    if not args.output:
        project_paths = get_project_paths()
        args.output = str(project_paths['state_dir'] / 'memory_profile_N{}.log'.format(args.N))

    # Run experiment
    results = run_memory_profile_experiment(
        N=args.N,
        seed=args.seed,
        theta=args.theta,
        rank=args.rank,
        sparsity_density=args.sparsity,
        num_eigenvalues=args.eigenvalues,
        output_path=args.output
    )

    # Print summary
    print(f"\nMemory Profile Summary:")
    print(f"  Peak Memory: {results['peak_memory_mb']:.2f} MB")
    print(f"  Duration: {results['duration_seconds']:.2f} seconds")
    print(f"  Log written to: {args.output}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
