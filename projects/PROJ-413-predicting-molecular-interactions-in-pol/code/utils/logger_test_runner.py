"""
Test runner to verify logger functionality by executing a dummy task
and writing results to results/performance.json.
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import PerformanceLogger, log_performance

def main():
    print("Starting Logger Infrastructure Test...")
    
    # Test 1: Context Manager
    print("Test 1: Testing context manager...")
    with PerformanceLogger("test_context_manager") as logger:
        time.sleep(0.1)  # Simulate work
    print(f"  Context manager test completed. Status: {logger.metrics['status']}")

    # Test 2: Manual start/stop
    print("Test 2: Testing manual start/stop...")
    logger2 = PerformanceLogger("test_manual")
    logger2.start()
    time.sleep(0.1)
    logger2.stop()
    print(f"  Manual test completed. Status: {logger2.metrics['status']}")

    # Test 3: Error handling
    print("Test 3: Testing error handling...")
    logger3 = PerformanceLogger("test_error")
    logger3.start()
    try:
        raise ValueError("Simulated error for testing")
    except Exception as e:
        logger3.log_error(e)
    print(f"  Error handling test completed. Status: {logger3.metrics['status']}")

    # Test 4: Convenience function
    print("Test 4: Testing convenience function...")
    start = time.time()
    time.sleep(0.1)
    duration = time.time() - start
    log_performance("test_convenience", duration, memory_mb=100.5)
    print(f"  Convenience function test completed.")

    # Verify output file exists
    results_dir = PROJECT_ROOT / "results"
    perf_file = results_dir / "performance.json"
    
    if perf_file.exists():
        import json
        with open(perf_file, 'r') as f:
            data = json.load(f)
        print(f"\nSuccess! results/performance.json created with {len(data)} entries.")
        print("Sample entry:")
        if data:
            print(json.dumps(data[0], indent=2))
    else:
        print(f"\nERROR: results/performance.json was not created.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
