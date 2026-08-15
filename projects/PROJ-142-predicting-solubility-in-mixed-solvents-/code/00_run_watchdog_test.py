"""
Test runner to simulate a training process and verify the watchdog.

This script is used to generate a real resource_monitor.log for verification
in Task T026c. It simulates a long-running process that triggers the watchdog.

Usage:
    python code/00_run_watchdog_test.py
"""
import os
import sys
import time
import signal
import json
import argparse
from pathlib import Path
from utils.watchdog import run_watchdog
from utils.constants import DATA_DIR

def simulate_training_process(duration_seconds=10, trigger_oom=False):
    """
    Simulates a training process.
    
    Args:
        duration_seconds: How long the process should run if not killed.
        trigger_oom: If True, this process will simulate high memory usage
                     to trigger the watchdog (requires root or specific env).
                     Note: In a standard CI environment, we usually just 
                     wait for the watchdog to timeout or kill based on PID.
    """
    print(f"Simulating training process (PID: {os.getpid()})...")
    print(f"Duration: {duration_seconds} seconds")
    
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        # Simulate work
        time.sleep(1)
        elapsed = time.time() - start_time
        print(f"  Training progress: {elapsed:.1f}s...")
        
    print("Training process completed successfully.")

def main():
    parser = argparse.ArgumentParser(
        description="Run a test to verify the resource monitor watchdog."
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Duration of the simulated training process in seconds."
    )
    parser.add_argument(
        "--watchdog-timeout",
        type=int,
        default=3,
        help="Watchdog timeout in seconds. If the process runs longer than this, it gets killed."
    )
    
    args = parser.parse_args()
    
    # Ensure artifacts directory exists
    artifacts_dir = DATA_DIR / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = artifacts_dir / "resource_monitor.log"
    
    # Start the watchdog in a separate thread or subprocess context
    # For simplicity in this test, we run the watchdog logic directly 
    # but in a way that mimics the real integration (T026b)
    
    print(f"Starting watchdog test. Log will be written to: {log_path}")
    print(f"Watchdog will kill the process if it runs longer than {args.watchdog_timeout}s.")
    
    # We use the run_watchdog function from utils.watchdog
    # It expects a target function to run and a log path
    try:
        # Note: In a real scenario, this might be a subprocess wrapper.
        # Here we run the training simulation directly but monitored.
        # The watchdog will check the current process (os.getpid()) periodically.
        
        # Since run_watchdog is designed to kill the target process,
        # we pass the simulate_training_process as the target.
        # However, run_watchdog typically spawns the target. 
        # To make this work for T026c verification, we need to ensure
        # the log is written.
        
        # Let's manually invoke the watchdog logic to ensure the log is populated
        # based on the existing implementation in utils/watchdog.py
        
        # We will run the training simulation and let the watchdog kill it if it takes too long
        run_watchdog(
            target_func=simulate_training_process,
            target_args=(args.duration,),
            log_path=str(log_path),
            timeout_seconds=args.watchdog_timeout
        )
        
    except Exception as e:
        print(f"Error during watchdog test: {e}")
        sys.exit(1)
        
    print("Watchdog test completed.")
    print(f"Check {log_path} for the resource monitor log.")

if __name__ == "__main__":
    main()