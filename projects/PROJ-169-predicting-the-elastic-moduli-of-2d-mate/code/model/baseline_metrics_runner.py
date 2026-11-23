"""
Wrapper script to run the intra-family baseline metric generation.
This script ensures the environment is set up and calls the baseline logic.
"""
import sys
import os
import torch

# Add code directory to path if running from project root
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.baseline_metrics import main

if __name__ == "__main__":
    main()