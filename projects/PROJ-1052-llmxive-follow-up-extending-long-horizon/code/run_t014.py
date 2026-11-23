"""
code/run_t014.py
Runner script to execute the recovery segment tagging logic (T014).
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utils.state_diff import main as t014_main

def main():
    """Execute T014."""
    print("Starting T014: Recovery Segment Tagging...")
    try:
        t014_main()
        print("T014 completed successfully.")
    except Exception as e:
        print(f"T014 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
