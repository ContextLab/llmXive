"""
Wrapper script to execute T040: Sensitivity Analysis.
This script ensures the environment is set up and calls the sensitivity module.
"""
import sys
import os

# Ensure code directory is in path if running from root
code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from analysis.sensitivity import main

if __name__ == "__main__":
    main()