"""
Demo script to verify T008: Setup logging infrastructure.
This script runs the logger, simulates a short task, and ensures
results/performance.json is created and populated.
"""
import os
import sys
import time

# Add project root to path if running as script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import PerformanceLogger, log_performance

def main():
    print("Starting T008 logger verification demo...")

    # Test 1: Context manager usage
    script_name = "demo_logger_test"
    print(f"Initializing logger for: {script_name}")

    with PerformanceLogger(script_name) as logger:
        # Simulate some work
        print("Simulating work (sleeping 0.5s)...")
        time.sleep(0.5)
        print("Work complete.")

    print("Context manager test passed.")

    # Test 2: Manual usage
    print("\nTesting manual log_performance function...")
    log_performance(
        script_name="manual_demo",
        duration=0.1,
        memory_mb=128.5,
        status="success"
    )
    print("Manual logging test passed.")

    # Verify output file exists
    results_dir = os.path.join(project_root, "results")
    perf_file = os.path.join(results_dir, "performance.json")

    if os.path.exists(perf_file):
        print(f"\nSUCCESS: {perf_file} created.")
        with open(perf_file, 'r') as f:
            import json
            data = json.load(f)
            print(f"Contents ({len(data)} entries):")
            print(json.dumps(data, indent=2))
    else:
        print(f"FAILURE: {perf_file} was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
