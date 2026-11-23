"""
code/tools/run_profiler.py

Runs cProfile on code/main.py for a sufficient number of iterations
and extracts top functions by cumulative time to results/logs/profile.txt.
"""
import cProfile
import pstats
import io
import os
import sys
import argparse
import time

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.main import parse_args, run_orchestration

def main():
    parser = argparse.ArgumentParser(description="Run cProfile on SpatialClaw Pipeline")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Number of iterations to run the pipeline")
    parser.add_argument("--output", type=str, default="results/logs/profile.txt",
                        help="Output file for profiling results")
    parser.add_argument("--seed", type=int, default=42, help="Master random seed")
    parser.add_argument("--n-tasks", type=int, default=50, help="Number of tasks to generate")
    parser.add_argument("--log-level", type=str, default="WARNING", help="Logging level")
    return parser.parse_args()

def run_profiled_iteration(seed, n_tasks, log_level):
    """Run a single iteration of the pipeline under cProfile."""
    # Create a profiler
    profiler = cProfile.Profile()
    
    # Mock args for run_orchestration
    class MockArgs:
        seed = seed
        n_tasks = n_tasks
        output = f"data/raw/synthetic_spatialclaw_v1_profile_{seed}.json"
        log_level = log_level
        budget_seconds = 6 * 60 * 60  # 6 hours
    
    args = MockArgs()
    
    # Run the orchestration under the profiler
    profiler.enable()
    try:
        run_orchestration(args)
    except Exception as e:
        # Log the error but continue profiling
        print(f"Error during profiling iteration: {e}", file=sys.stderr)
    finally:
        profiler.disable()
    
    return profiler

def aggregate_profiles(profilers, output_path):
    """Aggregate multiple profiles and write top functions to file."""
    # Create a stats object from the first profiler
    if not profilers:
        raise ValueError("No profiles to aggregate")
    
    # Sum up all profiles
    combined_stats = pstats.Stats(profilers[0])
    for p in profilers[1:]:
        combined_stats.add(p)
    
    # Sort by cumulative time
    combined_stats.sort_stats('cumulative')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write("SpatialClaw Pipeline Profiling Results\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total iterations: {len(profilers)}\n")
        f.write("=" * 60 + "\n\n")
        
        # Write top 50 functions by cumulative time
        f.write("Top 50 functions by cumulative time:\n")
        f.write("-" * 60 + "\n")
        
        # Use stats.print_stats with a limit
        stats_io = io.StringIO()
        combined_stats.print_stats(50)
        stats_text = stats_io.getvalue()
        f.write(stats_text)
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("End of profiling report\n")

def run():
    args = main()
    
    print(f"Running cProfile on code/main.py for {args.iterations} iterations...")
    print(f"Seed: {args.seed}, Tasks: {args.n_tasks}")
    
    start_time = time.time()
    
    profiles = []
    for i in range(args.iterations):
        print(f"  Iteration {i+1}/{args.iterations}...")
        # Use a slightly different seed for each iteration to vary the workload
        iteration_seed = args.seed + i
        profiler = run_profiled_iteration(iteration_seed, args.n_tasks, args.log_level)
        profiles.append(profiler)
    
    total_time = time.time() - start_time
    print(f"Profiling completed in {total_time:.2f}s")
    
    # Aggregate and save results
    aggregate_profiles(profiles, args.output)
    print(f"Profile results written to {args.output}")

if __name__ == "__main__":
    run()