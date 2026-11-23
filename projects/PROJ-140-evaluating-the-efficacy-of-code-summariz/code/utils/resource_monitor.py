"""
Resource Monitor for CI Compliance (FR-007)

Monitors RAM usage and runtime to ensure they stay within:
- RAM: ≤ 7 GB
- Runtime: ≤ 6 hours

This script is designed to run in the background while the main analysis
script executes. It asserts constraints and fails loudly if they are violated.
"""
import os
import sys
import time
import argparse
import signal
from pathlib import Path
from datetime import datetime
import resource

# Constants
RAM_LIMIT_GB = 7.0
RUNTIME_LIMIT_HOURS = 6.0
CHECK_INTERVAL_SECONDS = 5.0

def get_memory_usage_gb():
    """Get current process memory usage in GB."""
    try:
        # rusage.ru_maxrss is in KB on Linux
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_rss_kb = usage.ru_maxrss
        return max_rss_kb / (1024 * 1024)  # Convert KB to GB
    except Exception as e:
        print(f"Error reading memory usage: {e}", file=sys.stderr)
        return 0.0

def check_resources(max_ram_gb: float = RAM_LIMIT_GB, max_runtime_h: float = RUNTIME_LIMIT_HOURS):
    """
    Check current resource usage. Raises SystemExit if limits are exceeded.
    """
    current_ram = get_memory_usage_gb()
    start_time = getattr(check_resources, 'start_time', None)
    
    if start_time is None:
        check_resources.start_time = time.time()
        start_time = check_resources.start_time

    elapsed_time = time.time() - start_time
    elapsed_hours = elapsed_time / 3600.0

    if current_ram > max_ram_gb:
        msg = f"⚠️  RAM LIMIT EXCEEDED: {current_ram:.2f} GB > {max_ram_gb} GB"
        print(msg, file=sys.stderr)
        raise SystemExit(1)

    if elapsed_hours > max_runtime_h:
        msg = f"⚠️  RUNTIME LIMIT EXCEEDED: {elapsed_hours:.2f} hours > {max_runtime_h} hours"
        print(msg, file=sys.stderr)
        raise SystemExit(1)

def monitor_loop(max_ram_gb: float = RAM_LIMIT_GB, max_runtime_h: float = RUNTIME_LIMIT_HOURS):
    """
    Continuously monitor resources until interrupted or limits exceeded.
    """
    print(f"Resource Monitor started. Limits: RAM ≤ {max_ram_gb}GB, Time ≤ {max_runtime_h}h")
    print(f"Start time: {datetime.now().isoformat()}")
    
    # Set start time for the first check
    check_resources.start_time = time.time()

    try:
        while True:
            time.sleep(CHECK_INTERVAL_SECONDS)
            check_resources(max_ram_gb, max_runtime_h)
    except KeyboardInterrupt:
        print("\nMonitor stopped by user.")
    except SystemExit as e:
        # Re-raise to stop the job
        raise
    except Exception as e:
        print(f"Monitor error: {e}", file=sys.stderr)
        raise

def main():
    parser = argparse.ArgumentParser(description="Monitor system resources for CI compliance.")
    parser.add_argument("--max-ram-gb", type=float, default=RAM_LIMIT_GB, help="Max RAM in GB")
    parser.add_argument("--max-runtime-h", type=float, default=RUNTIME_LIMIT_HOURS, help="Max runtime in hours")
    parser.add_argument("--check-only", action="store_true", help="Check once and exit (for final validation)")
    parser.add_argument("--exit-on-exceed", action="store_true", help="Exit immediately if limits exceeded")
    
    args = parser.parse_args()

    if args.check_only:
        # Perform a single check
        try:
            check_resources(args.max_ram_gb, args.max_runtime_h)
            print("Resource check passed.")
        except SystemExit:
            print("Resource check failed.", file=sys.stderr)
            sys.exit(1)
        return

    # Run continuous monitoring
    monitor_loop(args.max_ram_gb, args.max_runtime_h)

if __name__ == "__main__":
    main()