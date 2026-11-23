"""
Entry point for running the pipeline as a module: python -m code
"""
import sys
import os

# Ensure the project root is in the path if running from outside
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import main

if __name__ == "__main__":
    main()