"""
Script to execute T030: Linearity Check
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.validation.linearity_check import main as linearity_main

def main():
    """Entry point for the T030 execution script."""
    return linearity_main()

if __name__ == "__main__":
    sys.exit(main())
