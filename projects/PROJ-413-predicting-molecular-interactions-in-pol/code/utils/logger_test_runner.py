import os
import sys
import time
from pathlib import Path
from utils.logger import PerformanceLogger, log_performance

def main():
    """
    Test runner for the logging infrastructure.
    Simulates a script execution to verify that results/performance.json is created
    and contains valid metrics.
    """
    print("Starting logger test runner...")

    # Test 1: Using PerformanceLogger as a context manager
    print("Test 1: Context manager usage")
    try:
        with PerformanceLogger("test_context_manager") as logger:
            time.sleep(0.1)  # Simulate some work
        print("  Context manager test passed.")
    except Exception as e:
        print(f"  Context manager test failed: {e}")
        return False

    # Test 2: Using log_performance convenience function
    print("Test 2: Convenience function usage")
    try:
        start = time.time()
        time.sleep(0.1)
        duration = time.time() - start
        log_performance("test_convenience", duration, memory_mb=100.5, status="success")
        print("  Convenience function test passed.")
    except Exception as e:
        print(f"  Convenience function test failed: {e}")
        return False

    # Verify the output file exists and contains data
    print("Verifying output file...")
    project_root = Path(____).parent.parent.parent
    performance_file = project_root / "results" / "performance.json"

    if not performance_file.exists():
        print(f"ERROR: Performance file not found at {performance_file}")
        return False

    import json
    with open(performance_file, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) < 2:
        print(f"ERROR: Performance file does not contain expected entries. Found {len(data)} entries.")
        return False

    # Validate structure of entries
    for entry in data:
        if "script_name" not in entry or "status" not in entry:
            print(f"ERROR: Entry missing required fields: {entry}")
            return False
        if entry["status"] not in ["success", "failed", "pending"]:
            print(f"ERROR: Invalid status in entry: {entry['status']}")
            return False

    print("Logger infrastructure test PASSED.")
    print(f"Output written to: {performance_file}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
