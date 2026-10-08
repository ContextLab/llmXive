import os
import sys
import time
import tracemalloc
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.statistics import run_permutation_test

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_mock_data(n_subjects: int = 10) -> Dict[str, np.ndarray]:
    """Generate representative mock data for profiling."""
    rng = np.random.default_rng(42)
    flexibility = rng.uniform(0.3, 0.7, size=n_subjects)
    # Simulate a moderate correlation
    creativity = 0.5 * flexibility + rng.normal(0, 0.1, size=n_subjects)
    creativity = np.clip(creativity, 0, 100)
    return {'flexibility': flexibility, 'creativity': creativity}

def profile_permutation_test(n_permutations: int = 1000, n_subjects: int = 10) -> Dict[str, Any]:
    """
    Run the permutation test with profiling enabled.
    Returns runtime and peak memory usage.
    """
    logger.info(f"Starting profiling for {n_subjects} subjects, {n_permutations} permutations")
    
    data = generate_mock_data(n_subjects)
    
    tracemalloc.start()
    start_time = time.perf_counter()
    
    results = run_permutation_test(
        flexibility=data['flexibility'],
        creativity=data['creativity'],
        n_permutations=n_permutations,
        seed=42
    )
    
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    runtime_seconds = end_time - start_time
    peak_memory_gb = peak / (1024 * 1024 * 1024)
    
    logger.info(f"Profiling complete: Runtime={runtime_seconds:.2f}s, Peak Memory={peak_memory_gb:.3f}GB")
    
    return {
        'runtime_seconds': runtime_seconds,
        'peak_memory_gb': peak_memory_gb,
        'n_permutations': n_permutations,
        'n_subjects': n_subjects,
        'empirical_p_value': results['empirical_p_value']
    }

def generate_scaling_projection(benchmark_result: Dict[str, Any], target_subjects: int = 1000) -> Dict[str, Any]:
    """
    Extrapolate runtime for a larger cohort based on benchmark results.
    Assumes linear scaling with number of subjects and permutations.
    """
    current_runtime = benchmark_result['runtime_seconds']
    current_subjects = benchmark_result['n_subjects']
    current_perms = benchmark_result['n_permutations']
    
    # Linear projection
    projected_runtime = current_runtime * (target_subjects / current_subjects)
    projected_hours = projected_runtime / 3600
    
    mitigation_needed = projected_hours > 6.0
    
    mitigation_plan = ""
    if mitigation_needed:
        mitigation_plan = (
            "MITIGATION REQUIRED: Projected runtime exceeds 6 hours.\n"
            "Strategies:\n"
            "1. Chunked processing: Split subjects into batches of 100.\n"
            "2. Parallel execution: Run batches on multiple CPU cores.\n"
            "3. Reduced permutations: Use 1000 permutations for screening, 10000 for final validation.\n"
            f"Estimated time with 10 cores: {projected_hours/10:.2f} hours."
        )
    else:
        mitigation_plan = "No mitigation required. Projected runtime is within limits."
    
    return {
        'target_subjects': target_subjects,
        'projected_runtime_hours': projected_hours,
        'mitigation_needed': mitigation_needed,
        'mitigation_plan': mitigation_plan
    }

def write_profiling_report(output_path: str, benchmark_result: Dict[str, Any], projection: Dict[str, Any]):
    """Write the profiling report to a text file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("PERMUTATION TEST PROFILING REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("BENCHMARK CONFIGURATION:\n")
        f.write(f"  Subjects: {benchmark_result['n_subjects']}\n")
        f.write(f"  Permutations: {benchmark_result['n_permutations']}\n\n")
        
        f.write("PERFORMANCE METRICS:\n")
        f.write(f"  Runtime: {benchmark_result['runtime_seconds']:.4f} seconds\n")
        f.write(f"  Peak Memory: {benchmark_result['peak_memory_gb']:.4f} GB\n")
        f.write(f"  Empirical P-Value: {benchmark_result['empirical_p_value']:.6f}\n\n")
        
        f.write("SCALING PROJECTION (1000 subjects):\n")
        f.write(f"  Projected Runtime: {projection['projected_runtime_hours']:.2f} hours\n")
        f.write(f"  Mitigation Needed: {'Yes' if projection['mitigation_needed'] else 'No'}\n\n")
        
        f.write("MITIGATION PLAN:\n")
        f.write(projection['mitigation_plan'] + "\n\n")
        
        f.write("=" * 60 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"Profiling report written to {output_path}")

def main():
    """Main entry point for the profiling script."""
    output_dir = Path("docs/outputs")
    output_file = output_dir / "profiling_report.txt"
    
    # Run benchmark with representative subset (10 subjects)
    # Using 1000 permutations for speed, but sufficient for profiling
    benchmark = profile_permutation_test(n_permutations=1000, n_subjects=10)
    
    # Generate projection for full cohort
    projection = generate_scaling_projection(benchmark, target_subjects=1000)
    
    # Write report
    write_profiling_report(str(output_file), benchmark, projection)
    
    # Assertions for CI
    assert benchmark['runtime_seconds'] < 21600, "Benchmark runtime exceeded 6 hours limit"
    assert benchmark['peak_memory_gb'] < 7.0, "Benchmark memory exceeded 7GB limit"
    
    print(f"Profiling completed successfully. Report saved to {output_file}")

if __name__ == "__main__":
    main()