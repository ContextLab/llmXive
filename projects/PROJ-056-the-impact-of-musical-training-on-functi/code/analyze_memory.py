"""
Memory Profiling Tool for PROJ-056 Pipeline.

This script runs the main pipeline in verification mode while profiling
memory usage to identify bottlenecks. It uses `memory_profiler` to track
peak RSS and reports the maximum memory consumption.

If peak memory exceeds 6GB, it outputs a recommendation to refactor
`code/main.py` to use chunked loading or Dask.
"""
import os
import sys
import time
import tracemalloc
import argparse
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Import main entry point
# We import the module, not the function, to wrap the execution
import main

try:
    from memory_profiler import memory_usage
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False
    print("WARNING: 'memory_profiler' not installed. Using tracemalloc fallback.")

# Import memory monitor for validation
from utils.memory_monitor import get_current_memory_mb, check_memory_limit, MemoryLimitExceeded

MEMORY_LIMIT_GB = 7.0
REFERENCE_LIMIT_GB = 6.0
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
LOG_FILE = OUTPUT_DIR / "memory_profile_report.txt"


def profile_with_tracemalloc(mode: str = "verification"):
    """
    Profile memory using standard library tracemalloc if memory_profiler is unavailable.
    Note: tracemalloc tracks Python object allocations, not necessarily total RSS,
    but is a good fallback for detecting large object creation.
    """
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    try:
        if mode == "verification":
            main.run_verification_mode()
        else:
            main.run_analysis_mode()
    except SystemExit:
        pass  # main.py might exit
    except Exception as e:
        print(f"Pipeline execution failed during profiling: {e}")
        raise
    finally:
        snapshot_after = tracemalloc.take_snapshot()
        tracemalloc.stop()

    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    peak_alloc = sum(stat.size_diff for stat in top_stats)
    peak_mb = peak_alloc / (1024 * 1024)

    return {
        "method": "tracemalloc",
        "peak_allocated_mb": peak_mb,
        "top_stats": top_stats[:5]
    }


def profile_with_memory_profiler(mode: str = "verification"):
    """
    Profile memory using memory_profiler package (preferred for RSS tracking).
    """
    def run_pipeline():
        if mode == "verification":
            main.run_verification_mode()
        else:
            main.run_analysis_mode()

    # measure_memory returns a tuple (result, (min, max, mean, std))
    # We run it multiple times to be safe, but here we just take the peak of one run
    # We use a timeout to prevent hanging if the script gets stuck
    try:
        mem_usage, _ = memory_usage((run_pipeline,), timeout=300, interval=0.5, max_iterations=1)
        # mem_usage is a list of memory usages over time
        peak_mb = max(mem_usage) if mem_usage else 0.0
        return {
            "method": "memory_profiler",
            "peak_rss_mb": peak_mb
        }
    except Exception as e:
        print(f"memory_profiler failed: {e}")
        return profile_with_tracemalloc(mode)


def write_report(report_data: dict, mode: str):
    """Writes the memory profile report to disk."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(LOG_FILE, 'w') as f:
        f.write(f"Memory Profile Report for PROJ-056\n")
        f.write(f"Mode: {mode}\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"=" * 50 + "\n\n")

        if report_data.get("method") == "memory_profiler":
            peak_mb = report_data.get("peak_rss_mb", 0)
            peak_gb = peak_mb / 1024
            f.write(f"Peak RSS (memory_profiler): {peak_mb:.2f} MB ({peak_gb:.2f} GB)\n")
            
            if peak_mb > REFERENCE_LIMIT_GB * 1024:
                f.write(f"\n⚠️  WARNING: Peak memory ({peak_gb:.2f} GB) exceeds {REFERENCE_LIMIT_GB} GB threshold.\n")
                f.write(f"RECOMMENDATION: Refactor code/main.py to use chunked loading or Dask.\n")
            else:
                f.write(f"\n✓ Memory usage is within acceptable limits (< {REFERENCE_LIMIT_GB} GB).\n")
        else:
            peak_mb = report_data.get("peak_allocated_mb", 0)
            f.write(f"Peak Python Allocation (tracemalloc): {peak_mb:.2f} MB\n")
            f.write(f"Note: This measures Python object allocation, not total RSS.\n")

        if "top_stats" in report_data:
            f.write("\nTop Memory Allocations:\n")
            for stat in report_data["top_stats"]:
                f.write(f"  {stat}\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("Report saved to: " + str(LOG_FILE) + "\n")

    print(f"Report written to: {LOG_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Profile memory usage of the pipeline.")
    parser.add_argument(
        "--mode",
        choices=["verification", "analysis"],
        default="verification",
        help="Pipeline mode to profile (default: verification)"
    )
    parser.add_argument(
        "--limit",
        type=float,
        default=MEMORY_LIMIT_GB,
        help="Memory limit in GB (default: 7.0)"
    )
    args = parser.parse_args()

    print(f"Starting memory profiling in '{args.mode}' mode...")
    print(f"Memory limit set to: {args.limit} GB")

    # Check initial memory
    initial_mem = get_current_memory_mb()
    print(f"Initial memory usage: {initial_mem:.2f} MB")

    report_data = {}
    try:
        if HAS_MEMORY_PROFILER:
            print("Using 'memory_profiler' for RSS tracking...")
            report_data = profile_with_memory_profiler(args.mode)
        else:
            print("Falling back to 'tracemalloc'...")
            report_data = profile_with_tracemalloc(args.mode)

        write_report(report_data, args.mode)

        # Validate against limit
        if HAS_MEMORY_PROFILER:
            peak_mb = report_data.get("peak_rss_mb", 0)
            if peak_mb > args.limit * 1024:
                raise MemoryLimitExceeded(
                    f"Peak memory ({peak_mb/1024:.2f} GB) exceeded limit ({args.limit} GB). "
                    "Refactoring required."
                )
        
        print("Memory profiling completed successfully.")

    except MemoryLimitExceeded as e:
        print(f"⚠️  MEMORY LIMIT EXCEEDED: {e}")
        # Write a specific failure report
        write_report(report_data, args.mode)
        # We do not exit with error code here to allow the task to complete 
        # with the report generated, but the user is warned.
        return 1
    except Exception as e:
        print(f"Error during profiling: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
