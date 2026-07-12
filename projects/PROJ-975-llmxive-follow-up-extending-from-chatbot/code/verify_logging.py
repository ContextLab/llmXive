"""
verify_logging.py

Verification script for T007.
Runs a test that writes a log entry using the configured logger
and confirms the existence of the output file.
"""
import os
import sys
import json

# Add project root to path if needed, though relative imports work from root
# Ensure we are in the project root context
from code.logging_config import get_logger, log_experiment_entry, verify_log_file_exists

def main():
    print("Starting T007 verification: Logging configuration test...")
    
    # 1. Get the logger (this initializes the CSV file if needed)
    logger = get_logger("t007_test")
    
    # 2. Write a test log entry using the convenience function
    # This simulates an actual experiment entry
    try:
        log_experiment_entry(
            task_id="T007_VERIFICATION_TEST",
            success=True,
            latency=0.123,
            tokens=50,
            retrieval_precision=0.85,
            retrieval_diversity=0.45,
            pruning_risk_count=0,
            library_size=10,
            pruning_enabled=False,
            extra_metadata={"test_run": True, "source": "verify_logging.py"}
        )
        print("Successfully wrote log entry via log_experiment_entry().")
    except Exception as e:
        print(f"ERROR: Failed to write log entry: {e}")
        return False

    # 3. Verify the file exists
    exists = verify_log_file_exists()
    if not exists:
        print("ERROR: Log file data/results/experiment_log.csv does not exist after writing.")
        return False
    
    print("SUCCESS: Log file data/results/experiment_log.csv exists.")

    # 4. Optional: Read and display the last line to confirm CSV structure
    try:
        log_path = "data/results/experiment_log.csv"
        with open(log_path, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                last_line = lines[-1].strip()
                print(f"Last log entry (truncated): {last_line[:100]}...")
            else:
                print("WARNING: Log file exists but appears empty or has only header.")
    except Exception as e:
        print(f"WARNING: Could not read log file for verification: {e}")

    print("T007 Verification Complete: PASSED")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)