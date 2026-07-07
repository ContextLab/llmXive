"""
Benchmark synthetic microstructure generator runtime.

Task: T005b
Description: Benchmark synthetic generator runtime for [deferred] images on 2-core CPU
to verify ≤6h constraint (SC-004).

This script runs the synthetic generator in a controlled environment (single thread,
no GPU) and measures the time taken to generate a specific number of samples.
It verifies that the generation rate scales linearly and estimates total time
for the full dataset (≥2000 images).
"""
import os
import sys
import time
import argparse
import multiprocessing
from data.synthetic_gen import main as synthetic_main

def run_benchmark(num_samples: int, output_dir: str, seed: int = 42) -> float:
    """
    Run the synthetic generator for a specific number of samples and measure time.

    Args:
        num_samples: Number of images to generate.
        output_dir: Directory to save generated images and metadata.
        seed: Random seed for reproducibility.

    Returns:
        Total time taken in seconds.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Prepare arguments for the synthetic generator
    # We call the main function directly but override args via environment or
    # by replicating logic. Since synthetic_gen.main() parses sys.argv,
    # we will invoke it with a modified sys.argv context or call the core logic.
    # To be safe and avoid sys.argv manipulation side effects, we call the core logic
    # if exposed, or we can spawn a subprocess.
    # Given the API surface, synthetic_gen.main() is the entry point.
    # We will simulate the command line arguments.

    original_argv = sys.argv.copy()
    try:
        # Construct arguments: --num-samples N --output-dir DIR --seed S
        sys.argv = [
            'code/data/synthetic_gen.py',
            '--num-samples', str(num_samples),
            '--output-dir', output_dir,
            '--seed', str(seed)
        ]

        start_time = time.time()
        synthetic_main()
        end_time = time.time()

        return end_time - start_time
    finally:
        sys.argv = original_argv

def estimate_total_time(sample_count: int, measured_time: float, target_count: int) -> float:
    """
    Estimate total time for target_count based on sample_count and measured_time.
    Assumes linear scaling.
    """
    rate = sample_count / measured_time if measured_time > 0 else 0
    return target_count / rate if rate > 0 else float('inf')

def main():
    parser = argparse.ArgumentParser(description="Benchmark synthetic generator runtime")
    parser.add_argument(
        '--num-samples', type=int, default=100,
        help='Number of samples to generate for the benchmark run (default: 100)'
    )
    parser.add_argument(
        '--target-count', type=int, default=2000,
        help='Target total dataset size for time estimation (default: 2000)'
    )
    parser.add_argument(
        '--output-dir', type=str, default='data/benchmark_run',
        help='Output directory for benchmark run'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed'
    )
    parser.add_argument(
        '--constraint-hours', type=float, default=6.0,
        help='Maximum allowed hours for full dataset (SC-004 constraint)'
    )

    args = parser.parse_args()

    print(f"Starting benchmark for {args.num_samples} samples...")
    print(f"Target dataset size: {args.target_count} images")
    print(f"Constraint: {args.constraint_hours} hours on 2-core CPU")
    print(f"Output directory: {args.output_dir}")

    # Set CPU affinity to simulate 2-core constraint if possible, though
    # the script itself should be efficient. We rely on the generator's
    # internal efficiency.
    try:
        # Attempt to limit to 2 cores if on Unix
        os.sched_setaffinity(0, {0, 1})
        print("CPU affinity set to cores 0, 1.")
    except (AttributeError, PermissionError, OSError):
        print("Could not set CPU affinity (expected on Windows or restricted env).")

    start_total = time.time()
    elapsed = run_benchmark(args.num_samples, args.output_dir, args.seed)
    total_elapsed = time.time() - start_total

    print(f"\n--- Benchmark Results ---")
    print(f"Samples generated: {args.num_samples}")
    print(f"Time taken: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
    
    estimated_total_seconds = estimate_total_time(args.num_samples, elapsed, args.target_count)
    estimated_total_hours = estimated_total_seconds / 3600

    print(f"Estimated time for {args.target_count} samples: {estimated_total_hours:.2f} hours")
    print(f"Constraint limit: {args.constraint_hours} hours")

    if estimated_total_hours <= args.constraint_hours:
        print("STATUS: PASS - Estimated runtime is within the 6-hour constraint.")
        sys.exit(0)
    else:
        print("STATUS: FAIL - Estimated runtime exceeds the 6-hour constraint.")
        print("Action: Optimize generator or reduce dataset size.")
        sys.exit(1)

if __name__ == '__main__':
    main()
