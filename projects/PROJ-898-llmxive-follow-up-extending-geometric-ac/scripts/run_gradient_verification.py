"""
Script to run the differentiable solver and verify gradient flow.

This script:
1. Imports the differentiable solver module
2. Runs the main function to verify gradient flow
3. Ensures the output file is created
"""
import os
import sys

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from differentiable_solver import main

if __name__ == "__main__":
    main()
