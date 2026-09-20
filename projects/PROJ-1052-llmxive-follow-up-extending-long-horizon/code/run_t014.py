"""
Runner script for T014: Implement recovery segment tagging logic.

This script executes the logic defined in code/utils/state_diff.py to read
the baseline execution logs, calculate state differences using sentence embeddings,
identify segments contributing >5% to state change, and update the CSV with
recovery_segment_id tags.
"""
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.state_diff import main as t014_main

if __name__ == "__main__":
    print("Executing T014: Recovery Segment Tagging...")
    t014_main()
    print("T014 execution finished.")
