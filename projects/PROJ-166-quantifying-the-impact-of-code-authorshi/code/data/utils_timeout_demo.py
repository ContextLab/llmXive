"""
Demo script to verify the pipeline timeout guard functionality.
This script is NOT part of the main pipeline but demonstrates the usage of 
pipeline_timeout_guard from code/config.py.

To test:
1. Normal run (should finish quickly):
   python code/data/utils_timeout_demo.py normal

2. Timeout simulation (set a very short timeout in code/config.py temporarily):
   # Temporarily set PIPELINE_TIMEOUT_SECONDS = 2 in config.py
   python code/data/utils_timeout_demo.py slow
"""
import sys
import time
from config import pipeline_timeout_guard, ensure_directories

def main():
    ensure_directories()
    
    if len(sys.argv) < 2:
        print("Usage: python utils_timeout_demo.py [normal|slow]")
        sys.exit(1)

    mode = sys.argv[1]

    with pipeline_timeout_guard():
        print("Pipeline guard active. Starting simulation...")
        if mode == "slow":
            print("Simulating a long-running process (sleeping 5 seconds)...")
            time.sleep(5)
            print("Process completed before timeout (if timeout was > 5s).")
        else:
            print("Simulating a normal process (sleeping 1 second)...")
            time.sleep(1)
            print("Process completed successfully.")
    
    print("Guard exited normally.")

if __name__ == "__main__":
    main()